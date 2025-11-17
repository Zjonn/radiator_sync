from typing import Optional, Callable, List
from datetime import datetime

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.entity import DeviceInfo

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..coordinator import Coordinator

from ..const import CONF_HEATER, CONF_MIN_ON, CONF_MIN_OFF, DOMAIN


class HeaterStateManager:
    """Tracks boiler runtime, cycles and running state, and manages HA subscription."""

    def __init__(self, coordinator: "Coordinator", config):
        self.coordinator = coordinator
        opts = coordinator.entry.options

        self.heater_name = config[CONF_HEATER]
        self.min_on_seconds = config[CONF_MIN_ON]
        self.min_off_seconds = config[CONF_MIN_OFF]
        self.is_running = opts.get("is_running", False)
        self.last_on = (
            datetime.fromisoformat(opts.get("last_on")) if opts.get("last_on") else None
        )
        self.last_off = (
            datetime.fromisoformat(opts.get("last_off"))
            if opts.get("last_off")
            else None
        )
        self.total_runtime_s = opts.get("total_runtime_s", 0.0)
        self.heat_demand = opts.get("heat_demand", 0.0)
        self.threshold_heat_demand = opts.get("threshold_heat_demand", 0.0)
        self.cycles = opts.get("cycles", 0)
        self._override_mode = opts.get("override_mode", "auto")

        self._listeners: List = []
        self._unsub: Optional[Callable] = None

    async def _persist(self):
        entry = self.coordinator.entry
        new_opts = dict(entry.options)

        new_opts.update(
            {
                "is_running": self.is_running,
                "last_on": self.last_on.isoformat() if self.last_on else None,
                "last_off": self.last_off.isoformat() if self.last_off else None,
                "total_runtime_s": self.total_runtime_s,
                "heat_demand": self.heat_demand,
                "threshold_heat_demand": self.threshold_heat_demand,
                "cycles": self.cycles,
                "override_mode": self._override_mode,
                "min_on_seconds": self.min_on_seconds,
                "min_off_seconds": self.min_off_seconds,
                "heater_name": self.heater_name,
            }
        )

        self.coordinator.hass.config_entries.async_update_entry(entry, options=new_opts)

    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self.coordinator.entry.entry_id}_heater")},
            name="Heater",
            manufacturer="RadiatorSync",
            model=self.heater_name,
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

    async def set_heat_demand(self, demand: float) -> None:
        """Turn boiler on/off based on demand (0–100%) with anti-cycling logic."""

        self.heat_demand = demand
        await self._persist()

        if self._override_mode != "auto":
            return  # ignore heat demand when overridden

        now = datetime.now()
        should_run = demand >= self.threshold_heat_demand

        if should_run and not self.is_running:
            if self.last_off is not None:
                off_time = (now - self.last_off).total_seconds()
                if off_time < self.min_off_seconds:
                    # Still in anti-short-cycle off window
                    return

            # turn ON
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

            # turn OFF
            await self.coordinator.hass.services.async_call(
                "switch", "turn_off", {"entity_id": self.heater_name}, blocking=False
            )
            return

    # ----------------------------
    # Listener registration
    # ----------------------------

    def register(self, listener):
        self._listeners.append(listener)

    async def notify(self):
        for e in self._listeners:
            await e.on_update()

    # ----------------------------
    # Heater state change logic
    # ----------------------------

    async def update_from_state(self, new_state: str):
        """Update running/cycle/runtime logic from switch state."""
        now_running = new_state == "on"

        if now_running and not self.is_running:
            # Started
            self.last_on = datetime.now()
            self.cycles += 1

        if not now_running and self.is_running and self.last_on:
            # Stopped → accumulate runtime
            self.total_runtime_s += (datetime.now() - self.last_on).total_seconds()

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
