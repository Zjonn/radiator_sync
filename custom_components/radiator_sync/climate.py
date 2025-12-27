from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .radiator.entities import RadiatorSyncRoomClimate
from .coordinator import RadiatorSyncCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup climate entities for all managed rooms."""

    coordinator: RadiatorSyncCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    entities = [RadiatorSyncRoomClimate(room) for room in coordinator.get_rooms()]
    async_add_entities(entities)
