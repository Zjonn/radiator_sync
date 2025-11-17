from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .heater.entities import HeaterModeSelect
from .coordinator import Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup the heater select entity."""

    coordinator: Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([HeaterModeSelect(coordinator.heater)])
