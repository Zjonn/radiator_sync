from typing import Optional, Callable
from datetime import datetime

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_registry import async_get as async_get_entity_reg
from homeassistant.helpers.device_registry import async_get as async_get_dev_reg


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..coordinator import RadiatorSyncCoordinator

from ..const import CONF_HEATER, CONF_MIN_ON, CONF_MIN_OFF, DOMAIN


class HeaterStateManager:
    """Tracks boiler runtime, cycles and running state, and manages HA subscription."""

    def __init__(self, coordinator: "RadiatorSyncCoordinator", config):
        self.coordinator = coordinator

        self.heater_name = config[CONF_HEATER]
        self.min_on_seconds = config[CONF_MIN_ON]
        self.min_off_seconds = config[CONF_MIN_OFF]
        self.is_running = False

        self.last_on: Optional[datetime] = None
        self.last_off: Optional[datetime] = None

        self.heat_demand = 0.0
        self.threshold_heat_demand = 0.0
        self._override_mode = "auto"

        self._unsub: Optional[Callable] = None

    def load_state(self, state: dict):
        """Load state from persistence."""
        self.is_running = state.get("is_running", False)
        if last_on := state.get("last_on"):
            self.last_on = datetime.fromisoformat(last_on)
        if last_off := state.get("last_off"):
            self.last_off = datetime.fromisoformat(last_off)
        self.heat_demand = state.get("heat_demand", 0.0)
        self.threshold_heat_demand = state.get("threshold_heat_demand", 0.0)
        self._override_mode = state.get("override_mode", "auto")

    def get_state(self) -> dict:
        """Get state for persistence."""
        return {
            "is_running": self.is_running,
            "last_on": self.last_on.isoformat() if self.last_on else None,
            "last_off": self.last_off.isoformat() if self.last_off else None,
            "heat_demand": self.heat_demand,
            "threshold_heat_demand": self.threshold_heat_demand,
            "override_mode": self._override_mode,
        }

    async def _persist(self):
        await self.coordinator.async_save_runtime_state()

    def device_info(self) -> DeviceInfo:
        hass = self.coordinator.hass

        ent_reg = async_get_entity_reg(hass)
        dev_reg = async_get_dev_reg(hass)

        model = self.heater_name
        entity_entry = ent_reg.async_get(self.heater_name)
        if entity_entry and entity_entry.device_id:
            dev_entry = dev_reg.async_get(entity_entry.device_id)
            model = dev_entry.name if dev_entry else entity_entry.name

        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.entry.entry_id}_heater")},
            name="Heater",
            manufacturer="RadiatorSync",
            model=model,
        )

    async def set_override_mode(self, mode: str) -> None:
        """Change override mode, forcing boiler state if required."""

        self._override_mode = mode
        await self._persist()
        await self.notify()

        if mode == "on":
            await self.coordinator.hass.services.async_call(
                "switch", "turn_on", {"entity_id": self.heater_name}, blocking=False
            )
        elif mode == "off":
            await self.coordinator.hass.services.async_call(
                "switch", "turn_off", {"entity_id": self.heater_name}, blocking=False
            )

    async def set_threshold_heat_demand(self, value: float) -> None:
        """Set minimum heat demand required to activate heater."""
        self.threshold_heat_demand = max(0.0, min(100.0, value))
        await self._persist()
        await self.notify()  # update entities showing threshold

    async def apply_heat_demand(self, demand: float) -> None:
        """Turn boiler on/off based on demand (0–100%) with anti-cycling logic."""

        if self.heat_demand == demand:
            return

        self.heat_demand = demand
        await self._persist()
        await self.notify()

        if self._override_mode != "auto":
            return  # ignore heat demand when overridden

        now = datetime.now()
        should_run = (demand >= self.threshold_heat_demand) or (
            self.is_running and demand > 0.0
        )

        if should_run and not self.is_running:
            if self.last_off is not None:
                off_time = (now - self.last_off).total_seconds()
                if off_time < self.min_off_seconds:
                    # Still in anti-short-cycle off window
                    return

            await self.coordinator.hass.services.async_call(
                "switch", "turn_on", {"entity_id": self.heater_name}, blocking=False
            )
            return

        if not should_run and self.is_running:
            if self.last_on is not None:
                on_time = (now - self.last_on).total_seconds()
                if on_time < self.min_on_seconds:
                    # Still in anti-short-cycle on window
                    return

            await self.coordinator.hass.services.async_call(
                "switch", "turn_off", {"entity_id": self.heater_name}, blocking=False
            )
            return

    # ----------------------------
    # Listener registration
    # ----------------------------

    async def notify(self):
        await self.coordinator.async_refresh_entities()

    # ----------------------------
    # Heater state change logic
    # ----------------------------

    async def update_from_state(self, new_state: str):
        """Update running/cycle/runtime logic from switch state."""
        now_running = new_state == "on"

        if now_running == self.is_running:
            return

        if now_running and not self.is_running:
            # Started
            self.last_on = datetime.now()

        self.is_running = now_running
        await self._persist()
        await self.notify()

    # ----------------------------
    # HA binding lifecycle
    # ----------------------------

    async def start(self):
        """Start listening to HA switch state of the heater."""

        @callback
        async def _changed(ev):
            st = ev.data.get("new_state")
            if st:
                await self.update_from_state(st.state)

        # Subscribe to entity state changes
        self._unsub = async_track_state_change_event(
            self.coordinator.hass, [self.heater_name], _changed
        )

        # Initial state read
        st = self.coordinator.hass.states.get(self.heater_name)
        if st:
            await self.update_from_state(st.state)

    async def stop(self):
        """Stop state tracking."""
        if self._unsub:
            self._unsub()
            self._unsub = None
