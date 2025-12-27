from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback

from ..coordinator import RadiatorSyncCoordinator

from .state_manager import HeaterStateManager

import logging

_LOGGER = logging.getLogger(__name__)


class HeaterThresholdNumber(CoordinatorEntity[RadiatorSyncCoordinator], NumberEntity):
    """Configurable threshold for minimum required heat demand."""

    _attr_translation_key = "heater_threshold"
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.AUTO

    def __init__(self, state: HeaterStateManager):
        super().__init__(state.coordinator)
        self.heater_state = state
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_threshold"
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 100.0
        self._attr_native_step = 1.0
        self._attr_device_info = self.heater_state.device_info()
        self._attr_native_value = self.heater_state.threshold_heat_demand

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self.heater_state.threshold_heat_demand
        self.async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        await self.heater_state.set_threshold_heat_demand(value)


class HeaterActiveBinary(
    CoordinatorEntity[RadiatorSyncCoordinator], BinarySensorEntity
):
    """Shows if heater is currently heating."""

    _attr_translation_key = "heater_active"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, state: HeaterStateManager):
        super().__init__(state.coordinator)
        self.heater_state = state
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_active"
        self._attr_device_info = self.heater_state.device_info()
        self._attr_is_on = self.heater_state.is_running

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_is_on = self.heater_state.is_running
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        await self.heater_state.start()

    async def async_will_remove_from_hass(self):
        await super().async_will_remove_from_hass()
        await self.heater_state.stop()


class HeaterHeatDemand(CoordinatorEntity[RadiatorSyncCoordinator], SensorEntity):
    """Number of boiler cycles."""

    _attr_translation_key = "heater_heat_demand"
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, state: HeaterStateManager):
        super().__init__(state.coordinator)
        self.heater_state = state
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_heat_demand"
        self._attr_device_info = self.heater_state.device_info()
        self._attr_native_value = self.heater_state.heat_demand

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self.heater_state.heat_demand
        self.async_write_ha_state()


class HeaterModeSelect(CoordinatorEntity[RadiatorSyncCoordinator], SelectEntity):
    """Provides 3 modes:
    - auto (radiators drive boiler)
    - on (force boiler on)
    - off (force boiler off)
    """

    _attr_translation_key = "heater_mode"
    _attr_options = ["auto", "on", "off"]

    def __init__(self, state: HeaterStateManager):
        super().__init__(state.coordinator)
        self.heater_state = state

        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_mode"
        self._attr_device_info = self.heater_state.device_info()
        self._attr_current_option = self.heater_state._override_mode

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_current_option = self.heater_state._override_mode
        self.async_write_ha_state()

    async def async_select_option(self, option: str):
        if option not in ["auto", "on", "off"]:
            _LOGGER.error("Invalid heater mode option selected: %s", option)
            return

        await self.heater_state.set_override_mode(option)
