"""Elite Dangerous XML Parser for use with Joystick Diagrams."""

import logging
import os
from pathlib import Path
from typing import Union
from xml.dom import minidom
from xml.etree import ElementTree

from joystick_diagrams.input.axis import Axis, AxisSlider
from joystick_diagrams.input.button import Button
from joystick_diagrams.input.hat import Hat  #, HatDirection
from joystick_diagrams.input.profile_collection import ProfileCollection
from joystick_diagrams.utils import resolve_bind

_logger = logging.getLogger(__name__)

HAT_FORMAT_LOOKUP = {"up": "U", "down": "D", "left": "L", "right": "R"}

PROFILE_MAPPINGS = {
    "MouseHumanoidXMode": "Humanoid",
    "MouseHumanoidYMode": "Humanoid",
    "MouseHumanoidSensitivity": "Humanoid",
    "HumanoidForwardAxis": "Humanoid",
    "HumanoidForwardButton": "Humanoid",
    "HumanoidBackwardButton": "Humanoid",
    "HumanoidStrafeAxis": "Humanoid",
    "HumanoidStrafeLeftButton": "Humanoid",
    "HumanoidStrafeRightButton": "Humanoid",
    "HumanoidRotateAxis": "Humanoid",
    "HumanoidRotateSensitivity": "Humanoid",
    "HumanoidRotateLeftButton": "Humanoid",
    "HumanoidRotateRightButton": "Humanoid",
    "HumanoidPitchAxis": "Humanoid",
    "HumanoidPitchSensitivity": "Humanoid",
    "HumanoidPitchUpButton": "Humanoid",
    "HumanoidPitchDownButton": "Humanoid",
    "HumanoidSprintButton": "Humanoid",
    "HumanoidWalkButton": "Humanoid",
    "HumanoidCrouchButton": "Humanoid",
    "HumanoidJumpButton": "Humanoid",
    "HumanoidPrimaryInteractButton": "Humanoid",
    "HumanoidSecondaryInteractButton": "Humanoid",
    "HumanoidItemWheelButton": "Humanoid",
    "HumanoidEmoteWheelButton": "Humanoid",
    "HumanoidUtilityWheelCycleMode": "Humanoid",
    "HumanoidItemWheelButton_XAxis": "Humanoid",
    "HumanoidItemWheelButton_XLeft": "Humanoid",
    "HumanoidItemWheelButton_XRight": "Humanoid",
    "HumanoidItemWheelButton_YAxis": "Humanoid",
    "HumanoidItemWheelButton_YUp": "Humanoid",
    "HumanoidItemWheelButton_YDown": "Humanoid",
    "HumanoidItemWheel_AcceptMouseInput": "Humanoid",
    "HumanoidPrimaryFireButton": "Humanoid",
    "HumanoidZoomButton": "Humanoid",
    "HumanoidThrowGrenadeButton": "Humanoid",
    "HumanoidMeleeButton": "Humanoid",
    "HumanoidReloadButton": "Humanoid",
    "HumanoidSwitchWeapon": "Humanoid",
    "HumanoidSelectPrimaryWeaponButton": "Humanoid",
    "HumanoidSelectSecondaryWeaponButton": "Humanoid",
    "HumanoidSelectUtilityWeaponButton": "Humanoid",
    "HumanoidSelectNextWeaponButton": "Humanoid",
    "HumanoidSelectPreviousWeaponButton": "Humanoid",
    "HumanoidHideWeaponButton": "Humanoid",
    "HumanoidSelectNextGrenadeTypeButton": "Humanoid",
    "HumanoidSelectPreviousGrenadeTypeButton": "Humanoid",
    "HumanoidToggleFlashlightButton": "Humanoid",
    "HumanoidToggleNightVisionButton": "Humanoid",
    "HumanoidToggleShieldsButton": "Humanoid",
    "HumanoidClearAuthorityLevel": "Humanoid",
    "HumanoidHealthPack": "Humanoid",
    "HumanoidBattery": "Humanoid",
    "HumanoidSelectFragGrenade": "Humanoid",
    "HumanoidSelectEMPGrenade": "Humanoid",
    "HumanoidSelectShieldGrenade": "Humanoid",
    "HumanoidSwitchToRechargeTool": "Humanoid",
    "HumanoidSwitchToCompAnalyser": "Humanoid",
    "HumanoidSwitchToSuitTool": "Humanoid",
    "HumanoidToggleToolModeButton": "Humanoid",
    "HumanoidToggleMissionHelpPanelButton": "Humanoid",
    "HumanoidPing": "Humanoid",
    "GalaxyMapOpen_Humanoid": "Humanoid",
    "SystemMapOpen_Humanoid": "Humanoid",
    "FocusCommsPanel_Humanoid": "Humanoid",
    "QuickCommsPanel_Humanoid": "Humanoid",
    "HumanoidOpenAccessPanelButton": "Humanoid",
    "HumanoidConflictContextualUIButton": "Humanoid",
    "HumanoidEmoteSlot1": "Humanoid",
    "HumanoidEmoteSlot2": "Humanoid",
    "HumanoidEmoteSlot3": "Humanoid",
    "HumanoidEmoteSlot4": "Humanoid",
    "HumanoidEmoteSlot5": "Humanoid",
    "HumanoidEmoteSlot6": "Humanoid",
    "HumanoidEmoteSlot7": "Humanoid",
    "HumanoidEmoteSlot8": "Humanoid",
}

class EliteDangerous:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.__load_file()
        self.keybindings = {}
        self.hats = None
        self.devices = {}
        self.button_array = {}
        self.action_map_bypass = {"Fire 1", "Fire 2"}
        self.custom_labels = {
            "attack1": "z_attack",
            "combatheal": "z_combat_heal",
            "combathealtarget": "z_heal_target",
            # Add more custom labels as needed
        }

    def __load_file(self):
        if os.getenv("APPDATA"):
            appdata_path = os.getenv("APPDATA")
            file_path = Path.joinpath(
                Path(appdata_path),
                "Local",
                "Frontier Developments",
                "Elite Dangerous",
                "Options",
                "Bindings",
                self.file_path,
            )
        if os.path.exists(file_path):
            if (os.path.splitext(self.file_path))[1] in [".binds", ".xml"]:
                data = Path(self.file_path).read_text(encoding="utf-8")
                try:
                    self.__validate_file(data)
                except Exception as e:
                    raise Exception(
                        "File is not a valid Elite Dangerous XML"
                    ) from e  # TODO remove base exception
                return data
            elif (os.path.splitext(file_path))[1] not in [".binds", ".xml"]:
                raise Exception(
                    "File must be an XML file"
                )  # TODO remove base exception
        else:
            raise FileNotFoundError("File not found")

    def __validate_file(self, data) -> bool:
        try:
            parsed_xml = minidom.parseString(data)
        except ValueError as e:
            raise Exception(
                "File is not a valid Elite Dangerous XML"
            ) from e  # TODO remove base exception
        else:
            if (
                len(parsed_xml.getElementsByTagName("Root")) == 1
                and len(parsed_xml.getElementsByTagName("Primary")) > 0
                and len(parsed_xml.getElementsByTagName("Secondary")) > 0
            ):
                return True

            raise Exception

    def get_human_readable_name(self, name) -> str:
        if name in self.custom_labels:
            return self.name_format(self.custom_labels.get(name))

        return self.name_format(name)

    def name_format(self, name: str) -> str:
        name_parts = name.split("_")
        if len(name_parts) == 1:
            return name_parts[0].capitalize()
        else:
            return (" ".join(name_parts[1:])).capitalize()

    def process_name(self, name: str) -> str:
        _logger.debug(f"Bind Name: {name}")

        return self.get_human_readable_name(name)

    def resolve_input(
        self, input_str: str
    ) -> tuple[dict[str, str], Union[Axis, Button, Hat, AxisSlider], str | None] | None:
        """Resolve an INPUT string to the a device/binding.

        Returns (device id, bind string, modifiers)
        """
        input_str = input_str.strip()

        _device_id, _binding = input_str[0:3], input_str[4:]

        # Resolve the devices and create in the profile if needed
        device_lookup = self.devices.get(_device_id)

        if not device_lookup:
            _logger.error("A device was not found in the valid list of devices.")
            return None

        if not _binding:  # Handles "jsX_ " scenario no mapping
            return None

        _modifiers, _resolved_bind = resolve_bind(_binding)

        if not _resolved_bind:
            _logger.error("Bind could not be resolved for {_binding}")
            return None

        return (device_lookup, _resolved_bind, _modifiers)

    def create_device_lookup(self, options) -> None:
        """Create lookup table for bind strings to resolve easier."""
        _prefixes = {
            "joystick": "js",
            # "keyboard": "kb", - Not Supported
            # "mouse": "mo", - Not Supported
            # "gamepad": "gp" - Not Supported
        }

        def parse_product(product_str: str) -> tuple[str, str]:
            product_name = product_str[0:-38].strip()
            product_guid = product_str[-37:-1].strip()
            return (product_name, product_guid)

        for option in options:
            _type = option.getAttribute("type")
            _inst = option.getAttribute("instance")

            _product = option.getAttribute("Product")

            _name, _guid = parse_product(_product)

            # Only get valid prefixes
            prefix = _prefixes.get(_type)

            if not prefix:
                continue
            device_identifier = f"{_prefixes[_type]}{_inst}"
            self.devices[device_identifier] = {"name": _name, "guid": _guid}

        _logger.debug(f"Created device lookups: {self.devices} ")

    # Additional Parsing Functions
    def handle_key_press(self, key):
        action = self.keybindings.get(key)
        if action:
            # Perform the action
            pass

    def add_keybinding(self, key, action):
        self.keybindings[key] = action

    def remove_keybinding(self, key):
        self.keybindings.pop(key, None)

    def update_keybinding(self, key, new_action):
        self.keybindings[key] = new_action

    # Parse XML Data
    def parse(self) -> ProfileCollection:
        root = ElementTree.fromstring(self.data)
        collection = ProfileCollection()
        profile = collection.create_profile("Elite Dangerous")
        # For each 'Primary', 'Secondary', and 'Binding' element in the XML
        for tag in ['Primary', 'Secondary', 'Binding']:
            for action in root.iter(tag):
                # Get the 'Device' and 'Key' attributes
                device_name = action.get('Device')
                key = action.get('Key')
                # If both 'Device' and 'Key' are present
                if device_name and key:
                    device = profile.add_device('{150D55D0-D984-11EE-8001-444553540000}', device_name)
                    device.create_input(key, action.text)

        return collection

def get_profile_name_map(name: str) -> str:
    """Return a mapped profile name  for a given name.

    Allows multiple profiles to be grouped into one
    """
    _name = PROFILE_MAPPINGS.get(name)

    # Handle unexpected new mappings with default
    if _name is None:
        _logger.warning(
            f"No map found for a Elite Dangerous profile {name}. This should be raised as a bug."
        )
        _name = "Spaceship"

    return _name

if __name__ == "__main__":
    #ed = EliteDangerous("Custom.4.0.binds")
    #print(ed.keybindings)
    pass
