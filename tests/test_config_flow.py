"""Test the Radiator Sync config flow."""
from unittest.mock import patch
from homeassistant import config_entries, data_entry_flow
from custom_components.radiator_sync.const import DOMAIN

async def test_form(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "custom_components.radiator_sync.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "heater": "switch.test_heater",
                "min_on_s": 300,
                "min_off_s": 300,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "RadiatorSync"
    assert result2["data"] == {
        "heater": "switch.test_heater",
        "min_on_s": 300,
        "min_off_s": 300,
    }
    assert result2["options"] == {"rooms": {}}
    assert len(mock_setup_entry.mock_calls) == 1
