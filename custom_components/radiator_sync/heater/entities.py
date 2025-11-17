from datetime import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.select import SelectEntity
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import EntityCategory

from ..const import DOMAIN
from .state_manager import HeaterStateManager

import logging

_LOGGER = logging.getLogger(__name__)


class HeaterThresholdNumber(NumberEntity):
    """Configurable threshold for minimum required heat demand."""

    _attr_name = "Heater Threshold Heat Demand"
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = "slider"  # user-friendly UI

    def __init__(self, state: HeaterStateManager):
        self.heater_state = state
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_threshold"
        self._attr_native_min_value = 0.0
        self._attr_native_max_value = 100.0
        self._attr_native_step = 1.0

    async def async_set_native_value(self, value: float) -> None:
        await self.heater_state.set_threshold_heat_demand(value)

    @property
    def native_value(self) -> float:
        return self.heater_state.threshold_heat_demand

    @property
    def device_info(self) -> DeviceInfo:
        return self.heater_state.device_info()


class HeaterActiveBinary(BinarySensorEntity):
    """Shows if heater is currently heating."""

    _attr_name = "Heater Active"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = "measurement"

    def __init__(self, state: HeaterStateManager):
        self.heater_state = state
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_active"

    async def on_update(self):
        self.async_write_ha_state()

    @property
    def is_on(self):
        return self.heater_state.is_running

    @property
    def device_info(self) -> DeviceInfo:
        return self.heater_state.device_info()

    async def async_added_to_hass(self):
        await self.heater_state.start()

    async def async_will_remove_from_hass(self):
        await self.heater_state.stop()


class HeaterRuntime(SensorEntity):
    """Total runtime in minutes."""

    _attr_name = "Heater Runtime"
    _attr_native_unit_of_measurement = "min"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, state: HeaterStateManager):
        self.heater_state = state
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_runtime"

    async def on_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        return self.heater_state.device_info()

    @property
    def native_value(self):
        total = self.heater_state.total_runtime_s
        if self.heater_state.is_running and self.heater_state.last_on:
            total += (datetime.now() - self.heater_state.last_on).total_seconds()
        return round(total / 60.0, 2)


class HeaterCycles(SensorEntity):
    """Number of boiler cycles."""

    _attr_name = "Heater Cycles"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, state: HeaterStateManager):
        self.heater_state = state
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_cycles"

    async def on_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        return self.heater_state.device_info()

    @property
    def native_value(self):
        return self.heater_state.cycles


class HeaterHeatDemand(SensorEntity):
    """Number of boiler cycles."""

    _attr_name = "Heater Heat Demand"
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, state: HeaterStateManager):
        self.heater_state = state
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_heat_demand"

    async def on_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        return self.heater_state.device_info()

    @property
    def native_value(self):
        return self.heater_state.heat_demand


class HeaterLastOn(SensorEntity):
    """Timestamp of last time the boiler was turned on."""

    _attr_name = "Heater Last On"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, state: HeaterStateManager):
        self.heater_state = state
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_last_on"

    async def on_update(self):
        self.async_write_ha_state()

    @property
    def device_info(self):
        return self.heater_state.device_info()

    @property
    def native_value(self):
        if self.heater_state.last_on:
            return self.heater_state.last_on.isoformat()
        return None


class HeaterModeSelect(SelectEntity):
    """Provides 3 modes:
    - auto (radiators drive boiler)
    - on (force boiler on)
    - off (force boiler off)
    """

    _attr_name = "Heater Mode"
    _attr_options = ["auto", "on", "off"]

    def __init__(self, state: HeaterStateManager):
        self.heater_state = state

        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heater_mode"
        self._attr_current_option = "auto"

    @property
    def device_info(self):
        return self.heater_state.device_info()

    async def async_select_option(self, option: str):
        self._attr_current_option = option

        if option not in ["auto", "on", "off"]:
            _LOGGER.error("Invalid heater mode option selected: %s", option)
            return

        await self.heater_state.set_override_mode(option)
