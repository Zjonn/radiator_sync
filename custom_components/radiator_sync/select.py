from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_PRESETS, DEFAULT_PRESETS
from .heater.entities import HeaterModeSelect
from .coordinator import RadiatorSyncCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup mode selection entity."""

    coordinator: RadiatorSyncCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    heater_manager = coordinator.heater

    entities: list[SelectEntity] = [
        HeaterModeSelect(heater_manager),
        GlobalPresetSelect(coordinator),
    ]

    async_add_entities(entities)


class GlobalPresetSelect(CoordinatorEntity[RadiatorSyncCoordinator], SelectEntity):
    """Global aggregator for room presets."""

    _attr_translation_key = "global_preset"

    def __init__(self, coordinator: RadiatorSyncCoordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_global_preset"
        self._attr_device_info = coordinator.heater.device_info()
        self._update_attr()

    def _update_attr(self):
        presets = self.coordinator.entry.options.get(CONF_PRESETS, {})
        self._attr_options = ["none"] + list(presets.keys())

        # Check if all rooms have the same preset
        rooms = list(self.coordinator.get_rooms())
        if not rooms:
            self._attr_current_option = "none"
            return

        first_preset = rooms[0].preset_mode
        if all(room.preset_mode == first_preset for room in rooms):
            self._attr_current_option = first_preset if first_preset else "none"
        else:
            self._attr_current_option = "none"

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_attr()
        self.async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        """Apply preset to all rooms."""
        if option == "none":
            # We don't have a way to 'unset' to none specifically other than manual temp change
            # but we can just leave it. Or we could explicitly set _active_preset to None in rooms.
            for room in self.coordinator.get_rooms():
                room._active_preset = None
                await room.notify()
        else:
            for room in self.coordinator.get_rooms():
                await room.set_preset_mode(option)

        self._update_attr()
        self.async_write_ha_state()
