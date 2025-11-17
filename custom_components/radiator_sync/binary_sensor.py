from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .heater.entities import HeaterActiveBinary
from .coordinator import Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup the heater binary_sensor."""

    coordinator: Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    heater = coordinator.heater

    ent = HeaterActiveBinary(heater)
    async_add_entities([ent])
    heater.register(ent)
