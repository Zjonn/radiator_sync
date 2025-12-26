from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_ROOMS
from .coordinator import RadiatorSyncCoordinator

import logging

_LOGGER = logging.getLogger(__name__)


PLATFORMS = ["climate", "binary_sensor", "sensor", "select", "number"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    # Create coordinator ONCE per entry
    heater_conf = entry.data
    rooms_conf = entry.options.get(CONF_ROOMS, {})
    coordinator = RadiatorSyncCoordinator(hass, entry, heater_conf, rooms_conf)

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "options": dict(entry.options),
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
