from typing import Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.storage import Store

from .heater.state_manager import HeaterStateManager
from .radiator.state_manager import RadiatorStateManager
from .const import DOMAIN

import logging

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.runtime_state"


class RadiatorSyncCoordinator(DataUpdateCoordinator[None]):
    """DataUpdateCoordinator for Radiator Sync."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        heater_conf: Dict[str, Any],
        rooms_conf: Dict[str, Any],
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Radiator Sync Coordinator",
            update_interval=None,  # Event-driven
        )

        self.entry = entry
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")
        self._runtime_state: Dict[str, Any] = {}

        self.heater = HeaterStateManager(self, heater_conf)
        self.rooms: Dict[str, RadiatorStateManager] = {}

        for name, config in rooms_conf.items():
            room = RadiatorStateManager(self, config)
            self.rooms[name] = room

    async def async_setup(self):
        """Set up the coordinator and load runtime state."""
        data = await self._store.async_load()
        if data:
            self._runtime_state = data
        
        # Initialize state managers with loaded state
        self.heater.load_state(self._runtime_state.get("heater", {}))
        for name, room in self.rooms.items():
            room.load_state(self._runtime_state.get(f"room_{name}", {}))

    async def async_save_runtime_state(self):
        """Save runtime state to store."""
        state = {
            "heater": self.heater.get_state(),
        }
        for name, room in self.rooms.items():
            state[f"room_{name}"] = room.get_state()
        
        self._runtime_state = state
        await self._store.async_save(state)

    def get_rooms(self):
        """Return all managed rooms."""
        return self.rooms.values()

    async def async_refresh_entities(self):
        """Notify all managed entities to update their state and run orchestration."""
        await self.on_update()
        self.async_set_updated_data(None)

    def _orchestrate(self):
        """Calculate and return average heat demand."""
        heat_demands = [
            demand
            for room in self.rooms.values()
            if (demand := room.get_heat_demand()) is not None
        ]

        if not heat_demands:
            return 0.0

        return sum(heat_demands) / len(heat_demands)

    async def on_update(self):
        """Orchestrate heater demand based on room demands."""
        heat_demand = self._orchestrate()
        await self.heater.apply_heat_demand(heat_demand)
