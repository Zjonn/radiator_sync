from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .heater.entities import HeaterModeSelect
from .coordinator import RadiatorSyncCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup mode selection entity."""

    coordinator: RadiatorSyncCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    heater_manager = coordinator.heater

    entities = [
        HeaterModeSelect(heater_manager),
    ]

    async_add_entities(entities)
