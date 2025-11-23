from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .heater.entities import (
    HeaterHeatDemand,
    HeaterThresholdNumber,
)
from .radiator.entities import RadiatorRoomHeatDemand
from .coordinator import Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup all sensors: heater diagnostics + heat demand."""

    coordinator: Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    heater_manager = coordinator.heater

    async_add_entities([HeaterThresholdNumber(heater_manager)])
    heater_sensors = [
        HeaterHeatDemand(heater_manager),
    ]
    async_add_entities(heater_sensors)
    for entitie in heater_sensors:
        heater_manager.register(entitie)

    room_entities = [RadiatorRoomHeatDemand(room) for room in coordinator.get_rooms()]
    async_add_entities(room_entities, True)
    for room, entitie in zip(coordinator.get_rooms(), room_entities):
        room.register(entitie)
