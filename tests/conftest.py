"""Fixtures for Radiator Sync integration tests."""

import pytest
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.radiator_sync.const import (
    DOMAIN,
    CONF_HEATER,
    CONF_ROOMS,
    CONF_NAME,
    CONF_SENSOR_TEMP,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="RadiatorSync",
        data={
            CONF_HEATER: "switch.test_heater",
            "min_on_s": 300,
            "min_off_s": 300,
        },
        options={
            CONF_ROOMS: {
                "Living Room": {
                    CONF_NAME: "Living Room",
                    CONF_SENSOR_TEMP: "sensor.living_room_temp",
                }
            }
        },
        entry_id="test_entry_id",
    )


@pytest.fixture
async def setup_integration(hass, mock_config_entry):
    """Set up the integration."""
    # Setup switch component so its services exist
    await async_setup_component(hass, "switch", {})

    mock_config_entry.add_to_hass(hass)

    # Pre-set some states
    hass.states.async_set("switch.test_heater", "off")
    hass.states.async_set("sensor.living_room_temp", "20.0")

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return mock_config_entry
