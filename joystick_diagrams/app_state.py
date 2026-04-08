import logging
from copy import deepcopy

from joystick_diagrams.db.device_alias_service import DeviceAliasService
from joystick_diagrams.db.device_service import DeviceService
from joystick_diagrams.db.label_service import LabelService
from joystick_diagrams.input.profile import Profile_
from joystick_diagrams.input.profile_collection import ProfileCollection
from joystick_diagrams.plugin_wrapper import PluginWrapper
from joystick_diagrams.plugins.output_plugin_manager import OutputPluginManager
from joystick_diagrams.plugins.plugin_manager import ParserPluginManager
from joystick_diagrams.profile_wrapper import ProfileWrapper

_logger = logging.getLogger(__name__)


class AppState:
    """appState for managing shared data for application."""

    _inst = None

    def __new__(cls, *args, **kwargs):
        if not cls._inst:
            cls._inst = super(AppState, cls).__new__(cls)

            cls._inst._init(
                plugin_manager=kwargs["plugin_manager"],
                output_plugin_manager=kwargs.get("output_plugin_manager"),
            )
        return cls._inst

    def _init(
        self,
        plugin_manager: ParserPluginManager,
        output_plugin_manager: OutputPluginManager | None = None,
    ) -> None:
        self.plugin_manager: ParserPluginManager = plugin_manager
        self.output_plugin_manager: OutputPluginManager | None = output_plugin_manager

        self.main_window = None
        self.label_service = LabelService()
        self.device_service = DeviceService()
        self.device_alias_service = DeviceAliasService()
        # Profile map for Plugin Profiles for lookups
        self.plugin_profile_map: dict[str, Profile_] = {}

        # Profile wrappers for use by app
        self.profile_wrappers: list[ProfileWrapper] = []

        self.profileParentMapping: dict[str, list[str]] = {}
        self.processedProfileObjectMapping: dict[str, Profile_] = {}
        self.process_profiles_from_collections()

    def process_profiles_from_collections(self):
        plugin_collections = self.get_plugin_wrapper_collections()

        # Create profile map from raw profiles
        _logger.debug(
            f"Processing profiles from plugins with {len(plugin_collections)} plugin collections"
        )
        self.create_plugin_profile_map(plugin_collections)

        # Create profile wrappers for use in app
        self.create_profile_wrappers(self.plugin_manager.get_enabled_plugin_wrappers())

        # Initialise wrappers — restores state, resolves inheritance from parents
        # Must run before aliasing so inheritance uses original (unaliased) profiles,
        # and aliasing then resolves GUIDs on the final merged result.
        self.initialise_profile_wrappers()

        # Apply GUID alias resolution on fully inherited profiles
        self._apply_guid_aliases()

    def initialise_profile_wrappers(self):
        _logger.debug(f"Initialising {len(self.profile_wrappers)} profile wrappers ")

        for wrapper in self.profile_wrappers:
            wrapper.initialise_wrapper()

    def create_profile_wrappers(self, plugin_wrappers: list[PluginWrapper]):
        # Clear Existing Wrappers
        self.profile_wrappers.clear()

        for plugin in plugin_wrappers:
            # Get pluugins only

            if not plugin.plugin_profile_collection:
                continue

            profiles = plugin.plugin_profile_collection.profiles

            _logger.debug(f"{len(profiles)} profiles detected for {plugin}")

            for profile in profiles.values():
                self.profile_wrappers.append(ProfileWrapper(profile, plugin))

            _logger.debug(
                f"Processing profiles from plugins with {plugin} plugin collections"
            )

    def _apply_guid_aliases(self):
        """Apply device GUID alias resolution to all profile wrappers.

        Resolves aliased GUIDs so that devices with different physical GUIDs
        that represent the same logical device are merged under the canonical GUID.
        """
        if not self.device_alias_service.get_all_aliases():
            return

        for wrapper in self.profile_wrappers:
            wrapper.profile = self._apply_aliases_to_profile(
                wrapper.profile, self.device_alias_service
            )

    @staticmethod
    def _apply_aliases_to_profile(
        profile: Profile_, alias_service: DeviceAliasService
    ) -> Profile_:
        """Resolve GUID aliases within a single profile, merging devices as needed.

        For each device, its GUID is resolved via the alias service. If the
        canonical GUID already exists in the result set, the source device's
        inputs are merged into the existing device (existing bindings take
        priority and are never overwritten).

        Args:
            profile: The profile to process (mutated in place and returned).
            alias_service: Service providing GUID alias resolution.

        Returns:
            The profile with aliases resolved.
        """
        items = list(profile.devices.items())
        original_count = len(items)
        new_devices = {}

        for guid, device in items:
            canonical = alias_service.resolve(guid)

            if canonical in new_devices:
                # Merge source inputs into existing device; existing bindings win
                existing_device = new_devices[canonical]
                merged_count = 0
                for input_type, inputs in device.inputs.items():
                    for input_key, input_ in inputs.items():
                        if input_key not in existing_device.inputs[input_type]:
                            existing_device.inputs[input_type][input_key] = deepcopy(
                                input_
                            )
                            merged_count += 1
                _logger.debug(
                    f"Merged device {guid[:8]} into existing {canonical[:8]}, added {merged_count} inputs"
                )
            else:
                if canonical != guid:
                    _logger.debug(
                        f"Aliased device {guid[:8]} -> {canonical[:8]} in profile {profile.name}"
                    )
                device.guid = canonical
                new_devices[canonical] = device

        _logger.debug(
            f"Alias resolution complete for {profile.name}: {original_count} devices -> {len(new_devices)} devices"
        )
        profile.devices = new_devices
        return profile

    def get_plugin_wrapper_collections(self) -> dict[str, ProfileCollection]:
        """Returns a list of Profile Collections that are tagged with the Plugin Name where the plugin is enabled"""
        return {
            x.name: x.plugin_profile_collection
            for x in self.plugin_manager.plugin_wrappers
            if x.enabled and x.plugin_profile_collection
        }

    def create_plugin_profile_map(
        self, profile_collections: dict[str, ProfileCollection]
    ):
        """Processes the **raw** profilee collections from all loaded and enabled plugins, into a new dictionary mapping

        Key = Plugin Name - Profile Name
        Value = Profile Object

        The keys are used to denote profiles from different sources potentially with the same name
        """

        # Clear existing processed profiles
        self.plugin_profile_map.clear()

        for profile_source, profiles in profile_collections.items():
            for profile_obj in profiles.profiles.values():
                composite_key = f"{profile_source.lower().strip()}_{profile_obj.name.lower().strip()}"
                self.plugin_profile_map[composite_key] = profile_obj

        _logger.debug(
            f"Loaded plugins resulted in the following profiles being detected {self.plugin_profile_map}"
        )


if __name__ == "__main__":
    pass
