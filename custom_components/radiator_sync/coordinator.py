from typing import Dict

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .heater.state_manager import HeaterStateManager
from .radiator.state_manager import RadiatorStateManager

import logging

_LOGGER = logging.getLogger(__name__)


class Coordinator:
    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, heater_conf, rooms_conf
    ) -> None:
        """Initialize the coordinator."""

        self.hass = hass
        self.entry = entry
        self.heater = HeaterStateManager(self, heater_conf)
        self.rooms: Dict[str, RadiatorStateManager] = {}

        for name, config in rooms_conf.items():
            room = RadiatorStateManager(self, config)
            self.rooms[name] = room
            room.register(self)

    def get_rooms(self):
        """Return all managed rooms."""
        return self.rooms.values()

    async def on_update(self):
        """Notify all managed entities to update their state."""
        heat_demands = [
            demand
            for room in self.rooms.values()
            if (demand := room.get_heat_demand()) is not None
        ]
        heat_demand = sum(heat_demands) / len(heat_demands)
        await self.heater.apply_heat_demand(heat_demand)
