"""Test Radiator Sync initialization."""

from homeassistant.core import HomeAssistant
from custom_components.radiator_sync.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_setup_entry(hass: HomeAssistant):
    """Test setting up the entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "heater": "switch.test_heater",
            "min_on_s": 300,
            "min_off_s": 300,
        },
        title="Radiator Sync",
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert DOMAIN in hass.data
