from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import EntityCategory


from .state_manager import RadiatorStateManager


class RadiatorRoomHeatDemand(SensorEntity):
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = "measurement"

    def __init__(self, state: RadiatorStateManager):
        self.radiator_state = state
        self._attr_name = f"{state.room_name} Heat Demand"
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_heat_demand"

    async def on_update(self):
        self.async_write_ha_state()

    @property
    def native_value(self):
        return self.radiator_state.get_heat_demand()

    @property
    def device_info(self) -> DeviceInfo:
        return self.radiator_state.device_info()


class RadiatorSyncRoomClimate(ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_mode = HVACMode.HEAT

    def __init__(self, state: RadiatorStateManager):
        self.radiator_state = state
        self._attr_name = f"{state.room_name} Radiator"
        self._attr_unique_id = f"{state.coordinator.entry.entry_id}_climate"
        self._attr_min_temp = 15.0
        self._attr_max_temp = 24.0
        self._attr_target_temperature = None

    async def async_set_hvac_mode(self, mode):
        self._attr_hvac_mode = mode
        self.async_write_ha_state()

    @property
    def current_temperature(self):
        return self.radiator_state.current_temperature()

    @property
    def target_temperature(self):
        return self.radiator_state.target_temperature()
    
    @property
    def min_temp(self):
        return self._attr_min_temp

    @property
    def max_temp(self):
        return self._attr_max_temp

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            await self.radiator_state.set_target_temperature(kwargs[ATTR_TEMPERATURE])

    async def async_added_to_hass(self):
        await self.radiator_state.start()

    async def async_will_remove_from_hass(self):
        await self.radiator_state.stop()

    @property
    def device_info(self) -> DeviceInfo:
        return self.radiator_state.device_info()
