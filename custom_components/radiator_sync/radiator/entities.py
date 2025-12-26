from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    HVACAction,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    UnitOfTemperature,
    EntityCategory,
)
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import callback


from .state_manager import RadiatorStateManager


class RadiatorRoomHeatDemand(CoordinatorEntity, SensorEntity):
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = "measurement"

    def __init__(self, state: RadiatorStateManager):
        super().__init__(state.coordinator)
        self.radiator_state = state
        self._attr_name = f"{state.room_name} Heat Demand"
        self._attr_unique_id = (
            f"{state.coordinator.entry.entry_id}_{state.room_name}_heat_demand"
        )
        self._attr_device_info = self.radiator_state.device_info()
        self._attr_native_value = self.radiator_state.get_heat_demand()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.radiator_state.get_heat_demand()
        self.async_write_ha_state()


class RadiatorSyncRoomClimate(CoordinatorEntity, ClimateEntity):
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_mode = HVACMode.HEAT

    def __init__(self, state: RadiatorStateManager):
        super().__init__(state.coordinator)
        self.radiator_state = state
        self._attr_name = f"{state.room_name} Radiator"
        self._attr_unique_id = (
            f"{state.coordinator.entry.entry_id}_{state.room_name}_climate"
        )
        self._attr_min_temp = 15.0
        self._attr_max_temp = 24.0
        self._attr_device_info = self.radiator_state.device_info()
        
        self._update_attr()

    def _update_attr(self):
        self._attr_current_temperature = self.radiator_state.current_temperature()
        self._attr_target_temperature = self.radiator_state.target_temperature()
        self._attr_current_humidity = self.radiator_state.current_humidity()
        self._attr_hvac_action = (
            HVACAction.HEATING if self.radiator_state.is_heating() else HVACAction.IDLE
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_attr()
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        self._attr_hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        if ATTR_TEMPERATURE in kwargs:
            await self.radiator_state.set_target_temperature(kwargs[ATTR_TEMPERATURE])

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        await self.radiator_state.start()

    async def async_will_remove_from_hass(self):
        await super().async_will_remove_from_hass()
        await self.radiator_state.stop()
