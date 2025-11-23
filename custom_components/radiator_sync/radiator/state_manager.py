from typing import Optional, Callable, Any

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity import DeviceInfo

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..coordinator import Coordinator


from ..const import (
    DOMAIN,
    CONF_NAME,
    CONF_ROOM_CLIMATE,
    CONF_SENSOR_TEMP,
    CONF_SENSOR_HUM,
    CONF_HYSTERESIS,
    DEFAULT_HYSTERESIS,
)

import logging

_LOGGER = logging.getLogger(__name__)


class RadiatorStateManager:
    """Central state + update/notify logic for a single room radiator."""

    MAX_DELTA = 2.0  # 100% demand if ΔT >= 2°C

    def __init__(self, coordinator: "Coordinator", config: dict) -> None:
        self.coordinator = coordinator
        opts = coordinator.entry.options

        self.room_name = config.get(CONF_NAME)
        self.sensor_temp = config.get(CONF_SENSOR_TEMP)
        self.hum_sensor = config.get(CONF_SENSOR_HUM)
        self.hysteresis = config.get(CONF_HYSTERESIS, DEFAULT_HYSTERESIS)
        self.climate_target = config.get(CONF_ROOM_CLIMATE)

        self._is_heating = False
        self._current_temp: Optional[float] = None
        self._target_temp: Optional[float] = opts.get(
            f"{self.room_name}_target_temp", 21.0
        )
        self._current_humidity: Optional[float] = None
        self._listeners: list[Any] = []
        self._unsubs: list[Callable] = []

    async def _persist(self):
        entry = self.coordinator.entry
        new_opts = dict(entry.options)

        new_opts.update(
            {
                f"{self.room_name}_target_temp": self._target_temp,
            }
        )

        self.coordinator.hass.config_entries.async_update_entry(entry, options=new_opts)

    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                (DOMAIN, f"{self.coordinator.entry.entry_id}_{self.room_name}_radiator")
            },
            name=f"{self.room_name}",
            manufacturer="RadiatorSync",
            model=self.climate_target or "Generic Radiator",
        )

    # ----------------------------
    # Registration and state read
    # ----------------------------

    def register(self, entity: Any):
        """Registers an entity that should refresh when state changes."""
        self._listeners.append(entity)

    async def notify(self):
        """Notifies registered entities to refresh HA state."""
        for s in self._listeners:
            await s.on_update()

        # also apply linked climate control if target & current available
        await self._apply_climate_control()

    def current_temperature(self) -> Optional[float]:
        return self._current_temp

    def target_temperature(self) -> Optional[float]:
        return self._target_temp

    def current_humidity(self) -> Optional[int]:
        return (
            int(self._current_humidity) if self._current_humidity is not None else None
        )

    def is_heating(self) -> bool:
        return self._is_heating

    def get_heat_demand(self) -> int:
        """Return heat demand 0–100% based on target/current difference."""
        if self._current_temp is None or self._target_temp is None:
            return 0

        delta = max(0.0, (self._target_temp + self.hysteresis) - self._current_temp)
        return round(min(delta / self.MAX_DELTA, 1.0) * 100.0)

    # ----------------------------
    # Temperature & target changes
    # ----------------------------

    async def set_target_temperature(self, new_t: float):
        """Update target and forward to actual thermostat entity, if exists."""
        self._target_temp = new_t
        await self._apply_climate_control()
        await self._persist()
        await self.notify()

    # ----------------------------
    # Climate control decision logic
    # ----------------------------

    async def _apply_climate_control(self):
        """Modify linked climate temperature depending on temp/hysteresis window."""

        if not self.climate_target:
            return  # climate optional

        if self._current_temp is None or self._target_temp is None:
            return

        low = self._target_temp - self.hysteresis
        high = self._target_temp + self.hysteresis

        # too cold -> boost heating
        if self._current_temp < low:
            await self._set_climate_temp(self._target_temp + 5)
            self._is_heating = True
            return

        # too warm -> reduce heating
        elif self._current_temp > high:
            await self._set_climate_temp(self._target_temp - 5)
            self._is_heating = False
            return

    async def _set_climate_temp(self, value: float):
        """Send set_temperature only if entity exists."""
        if not self.climate_target:
            return
        await self.coordinator.hass.services.async_call(
            "climate",
            "set_temperature",
            {"entity_id": self.climate_target, "temperature": value},
            blocking=False,
        )

    # ----------------------------
    # Sensor tracking
    # ----------------------------

    async def start(self):
        """Begin tracking temperature and climate target changes."""

        @callback
        async def hum_update(ev):
            st = ev.data.get("new_state")
            if st and st.state not in ("unknown", "unavailable"):
                try:
                    self._current_humidity = float(st.state)
                except Exception as e:
                    _LOGGER.error(
                        f"Radiator '{self.room_name}': invalid humidity state: {st.state}: {e}"
                    )
                await self.notify()

        @callback
        async def temp_update(ev):
            st = ev.data.get("new_state")
            if st and st.state not in ("unknown", "unavailable"):
                try:
                    self._current_temp = float(st.state)
                except Exception as e:
                    _LOGGER.error(
                        f"Radiator '{self.room_name}': invalid temperature state: {st.state}: {e}"
                    )
                await self.notify()

        @callback
        async def hw_target_update(ev):
            st = ev.data.get("new_state")
            if st and "temperature" in st.attributes:
                await self._apply_climate_control()

        # track sensor and target climate
        if self.sensor_temp:
            self._unsubs.append(
                async_track_state_change_event(
                    self.coordinator.hass, [self.sensor_temp], temp_update
                )
            )

        if self.hum_sensor:
            self._unsubs.append(
                async_track_state_change_event(
                    self.coordinator.hass, [self.hum_sensor], hum_update
                )
            )

        if self.climate_target:
            self._unsubs.append(
                async_track_state_change_event(
                    self.coordinator.hass, [self.climate_target], hw_target_update
                )
            )

        # initial values read
        st = self.coordinator.hass.states.get(self.sensor_temp)
        if st:
            try:
                self._current_temp = float(st.state)
            except Exception as e:
                _LOGGER.error(
                    f"Radiator '{self.room_name}': invalid temperature state: {st.state}: {e}"
                )

        if self.climate_target:
            st = self.coordinator.hass.states.get(self.climate_target)
            if st and "temperature" in st.attributes:
                self._target_temp = st.attributes["temperature"]

        await self.notify()

    async def stop(self):
        for u in self._unsubs:
            u()
        self._unsubs.clear()
