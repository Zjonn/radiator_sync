from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .heater.entities import HeaterHeatDemand
from .radiator.entities import RadiatorRoomHeatDemand
from .coordinator import RadiatorSyncCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Setup all sensors: heater diagnostics + heat demand."""

    coordinator: RadiatorSyncCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    heater_manager = coordinator.heater

    entities = [
        HeaterHeatDemand(heater_manager),
    ]

    for room in coordinator.get_rooms():
        entities.append(RadiatorRoomHeatDemand(room))

    async_add_entities(entities)
