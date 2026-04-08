"""Integration tests for GUID aliasing + profile inheritance + export pipeline.

Verifies that when devices are aliased and profiles inherit from parents,
the final merged profile has correct bindings with proper priority rules:
- Child bindings win over parent bindings (inheritance)
- Target device bindings win over source device bindings (aliasing)
- Aliasing must run AFTER inheritance to avoid being discarded
"""

from copy import deepcopy
from unittest.mock import MagicMock, patch

import pytest

from joystick_diagrams.app_state import AppState
from joystick_diagrams.db.device_alias_service import DeviceAliasService
from joystick_diagrams.input.button import Button
from joystick_diagrams.input.profile import Profile_
from joystick_diagrams.profile_wrapper import ProfileWrapper
from joystick_diagrams.ui.device_setup_controller import (
    convert_profile_wrappers_to_export_devices,
)

GUID_A = "aaaa0000-0000-0000-0000-000000000001"
GUID_B = "bbbb0000-0000-0000-0000-000000000002"


def _make_mock_plugin_wrapper(name="TestPlugin"):
    pw = MagicMock()
    pw.name = name
    pw.icon = ""
    return pw


def _make_profile_with_device(name, guid, device_name, buttons=None):
    """Helper: create a profile with one device, optionally adding button inputs."""
    profile = Profile_(name)
    device = profile.add_device(guid, device_name)
    for btn_id, command in buttons or []:
        device.create_input(Button(btn_id), command)
    return profile


@pytest.fixture()
def alias_service_a_to_b():
    """DeviceAliasService with GUID_A -> GUID_B alias."""
    with patch(
        "joystick_diagrams.db.device_alias_service.db_device_aliases"
    ) as mock_db:
        mock_db.get_all_aliases.return_value = [(GUID_A, GUID_B)]
        yield DeviceAliasService()


@pytest.fixture()
def alias_service_no_aliases():
    """DeviceAliasService with no aliases configured."""
    with patch(
        "joystick_diagrams.db.device_alias_service.db_device_aliases"
    ) as mock_db:
        mock_db.get_all_aliases.return_value = []
        yield DeviceAliasService()


class TestAliasAndInheritanceCombined:
    """Tests for the combined aliasing + inheritance pipeline."""

    def test_alias_plus_inheritance_merges_correctly(self, alias_service_a_to_b):
        """Parent has Device A bindings, child has Device B bindings, A aliased to B.

        After inheritance (child merges parent) then aliasing (A resolves to B),
        the result should have a single device under GUID_B with:
        - Button1 = "missile" (child wins over parent)
        - Button2 = "flare" (child only)
        - Button3 = "chaff" (inherited from parent)
        """
        mock_pw = _make_mock_plugin_wrapper()

        parent_profile = _make_profile_with_device(
            "parent", GUID_A, "JoystickA", buttons=[(1, "fire"), (3, "chaff")]
        )
        child_profile = _make_profile_with_device(
            "child", GUID_B, "JoystickB", buttons=[(1, "missile"), (2, "flare")]
        )

        parent_wrapper = ProfileWrapper(parent_profile, mock_pw)
        child_wrapper = ProfileWrapper(child_profile, mock_pw)

        # Set up inheritance: child inherits from parent
        child_wrapper.parents = [parent_wrapper]
        child_wrapper.inherit_parents_into_profile()

        # After inheritance, child should have both devices (A from parent, B from child)
        assert GUID_A in child_wrapper.profile.devices
        assert GUID_B in child_wrapper.profile.devices

        # Now apply aliasing (A -> B)
        child_wrapper.profile = AppState._apply_aliases_to_profile(
            child_wrapper.profile, alias_service_a_to_b
        )

        # After aliasing, only GUID_B should remain
        assert GUID_A not in child_wrapper.profile.devices
        assert GUID_B in child_wrapper.profile.devices
        assert len(child_wrapper.profile.devices) == 1

        merged = child_wrapper.profile.devices[GUID_B]
        # Child's Button1 wins over parent's (child had "missile", parent had "fire")
        assert merged.inputs["buttons"]["BUTTON_1"].command == "missile"
        # Child's Button2 (no conflict)
        assert merged.inputs["buttons"]["BUTTON_2"].command == "flare"
        # Parent's Button3 inherited and merged in (from Device A, now under B)
        assert merged.inputs["buttons"]["BUTTON_3"].command == "chaff"

    def test_alias_plus_inheritance_parent_both_devices_merge(
        self, alias_service_a_to_b
    ):
        """Parent has both Device A and Device B, child has Device B only.

        After inheritance + aliasing: child has single device under GUID_B with
        all buttons from parent A, parent B, and child B (child wins on conflicts).
        """
        mock_pw = _make_mock_plugin_wrapper()

        parent_profile = Profile_("parent")
        dev_a = parent_profile.add_device(GUID_A, "JoystickA")
        dev_a.create_input(Button(3), "chaff")
        dev_a.create_input(Button(4), "countermeasures")
        dev_b = parent_profile.add_device(GUID_B, "JoystickB")
        dev_b.create_input(Button(5), "gear_toggle")

        child_profile = _make_profile_with_device(
            "child", GUID_B, "JoystickB", buttons=[(1, "missile"), (5, "gear_up")]
        )

        parent_wrapper = ProfileWrapper(parent_profile, mock_pw)
        child_wrapper = ProfileWrapper(child_profile, mock_pw)

        child_wrapper.parents = [parent_wrapper]
        child_wrapper.inherit_parents_into_profile()

        child_wrapper.profile = AppState._apply_aliases_to_profile(
            child_wrapper.profile, alias_service_a_to_b
        )

        assert len(child_wrapper.profile.devices) == 1
        merged = child_wrapper.profile.devices[GUID_B]

        # From child
        assert merged.inputs["buttons"]["BUTTON_1"].command == "missile"
        # From parent Device A (inherited, then aliased into B)
        assert merged.inputs["buttons"]["BUTTON_3"].command == "chaff"
        assert merged.inputs["buttons"]["BUTTON_4"].command == "countermeasures"
        # Child's Button5 wins over parent's (child="gear_up", parent="gear_toggle")
        assert merged.inputs["buttons"]["BUTTON_5"].command == "gear_up"

    def test_export_devices_reflect_aliased_inherited_profile(
        self, alias_service_a_to_b
    ):
        """Full pipeline: inheritance + aliasing + export device construction.

        ExportDevices should contain a single canonical device with merged inputs.
        """
        mock_pw = _make_mock_plugin_wrapper()

        parent_profile = _make_profile_with_device(
            "parent", GUID_A, "JoystickA", buttons=[(1, "fire"), (3, "chaff")]
        )
        child_profile = _make_profile_with_device(
            "child", GUID_B, "JoystickB", buttons=[(1, "missile"), (2, "flare")]
        )

        parent_wrapper = ProfileWrapper(parent_profile, mock_pw)
        child_wrapper = ProfileWrapper(child_profile, mock_pw)

        child_wrapper.parents = [parent_wrapper]
        child_wrapper.inherit_parents_into_profile()

        child_wrapper.profile = AppState._apply_aliases_to_profile(
            child_wrapper.profile, alias_service_a_to_b
        )

        # Convert to export devices
        export_devices = convert_profile_wrappers_to_export_devices([child_wrapper])

        # Should produce exactly 1 export device (single merged device)
        assert len(export_devices) == 1
        ed = export_devices[0]
        assert ed.device_id == GUID_B
        assert ed.device.inputs["buttons"]["BUTTON_1"].command == "missile"
        assert ed.device.inputs["buttons"]["BUTTON_2"].command == "flare"
        assert ed.device.inputs["buttons"]["BUTTON_3"].command == "chaff"

    def test_old_ordering_bug_aliasing_lost_after_inheritance(
        self, alias_service_a_to_b
    ):
        """Regression: running aliasing BEFORE inheritance loses alias resolution.

        inherit_parents_into_profile() rebuilds from original_profile, discarding
        the aliased wrapper.profile. This test demonstrates the bug and verifies
        the correct ordering.
        """
        mock_pw = _make_mock_plugin_wrapper()

        parent_profile = _make_profile_with_device(
            "parent", GUID_A, "JoystickA", buttons=[(3, "chaff")]
        )
        child_profile = _make_profile_with_device(
            "child", GUID_B, "JoystickB", buttons=[(1, "missile")]
        )

        parent_wrapper = ProfileWrapper(parent_profile, mock_pw)
        child_wrapper = ProfileWrapper(child_profile, mock_pw)
        child_wrapper.parents = [parent_wrapper]

        # === WRONG ORDER (old bug): alias first, then inherit ===
        bug_wrapper = ProfileWrapper(deepcopy(child_profile), mock_pw)
        bug_wrapper.parents = [parent_wrapper]

        # Apply aliasing first — this resolves GUIDs correctly...
        bug_wrapper.profile = AppState._apply_aliases_to_profile(
            bug_wrapper.profile, alias_service_a_to_b
        )
        # At this point, aliasing is correct
        assert GUID_B in bug_wrapper.profile.devices

        # ...but inheritance rebuilds from original_profile, discarding aliasing
        bug_wrapper.inherit_parents_into_profile()
        # Bug: Device A is back under its original GUID (unaliased)
        assert (
            GUID_A in bug_wrapper.profile.devices
        ), "Bug demo: inheritance rebuilt from original_profile, restoring unaliased GUID_A"

        # === CORRECT ORDER: inherit first, then alias ===
        child_wrapper.inherit_parents_into_profile()
        child_wrapper.profile = AppState._apply_aliases_to_profile(
            child_wrapper.profile, alias_service_a_to_b
        )

        # Correct: only GUID_B remains, with merged bindings
        assert GUID_A not in child_wrapper.profile.devices
        assert GUID_B in child_wrapper.profile.devices
        merged = child_wrapper.profile.devices[GUID_B]
        assert merged.inputs["buttons"]["BUTTON_1"].command == "missile"
        assert merged.inputs["buttons"]["BUTTON_3"].command == "chaff"

    def test_no_parents_aliasing_survives(self, alias_service_a_to_b):
        """Profile with no parents — aliasing is applied and survives
        because inheritance returns early without modifying wrapper.profile."""
        mock_pw = _make_mock_plugin_wrapper()

        profile = _make_profile_with_device(
            "solo", GUID_A, "JoystickA", buttons=[(1, "fire")]
        )
        wrapper = ProfileWrapper(profile, mock_pw)

        # Inheritance with no parents — returns early, no-op
        wrapper.inherit_parents_into_profile()

        # Apply aliasing
        wrapper.profile = AppState._apply_aliases_to_profile(
            wrapper.profile, alias_service_a_to_b
        )

        assert GUID_A not in wrapper.profile.devices
        assert GUID_B in wrapper.profile.devices
        assert (
            wrapper.profile.devices[GUID_B].inputs["buttons"]["BUTTON_1"].command
            == "fire"
        )
