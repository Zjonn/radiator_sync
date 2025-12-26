from typing import Dict, Any

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .heater.state_manager import HeaterStateManager
from .radiator.state_manager import RadiatorStateManager

import logging

_LOGGER = logging.getLogger(__name__)


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
        self.heater = HeaterStateManager(self, heater_conf)
        self.rooms: Dict[str, RadiatorStateManager] = {}

        for name, config in rooms_conf.items():
            room = RadiatorStateManager(self, config)
            self.rooms[name] = room

    def get_rooms(self):
        """Return all managed rooms."""
        return self.rooms.values()

    async def async_refresh_entities(self):
        """Notify all managed entities to update their state and run orchestration."""
        await self.on_update()
        self.async_set_updated_data(None)

    async def on_update(self):
        """Orchestrate heater demand based on room demands."""
        heat_demands = [
            demand
            for room in self.rooms.values()
            if (demand := room.get_heat_demand()) is not None
        ]

        if not heat_demands:
            await self.heater.apply_heat_demand(0.0)
            return

        heat_demand = sum(heat_demands) / len(heat_demands)
        await self.heater.apply_heat_demand(heat_demand)
