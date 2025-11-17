from .radiator.entities import RadiatorSyncRoomClimate
from .const import DOMAIN
from .coordinator import Coordinator

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup climate entities for each room."""

    coordinator: Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = [RadiatorSyncRoomClimate(room) for room in coordinator.get_rooms()]

    async_add_entities(entities)
