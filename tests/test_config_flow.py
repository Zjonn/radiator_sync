"""Test the Radiator Sync config flow."""

from unittest.mock import patch
from homeassistant import config_entries, data_entry_flow
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.radiator_sync.const import (
    DOMAIN,
    CONF_NAME,
    CONF_SENSOR_TEMP,
    CONF_HYSTERESIS,
)


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
    assert result2["options"] == {
        "rooms": {},
        "presets": {
            "Night": {"default": 19.5, "overrides": {}},
            "Away": {"default": 15.0, "overrides": {}},
        },
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_options_flow_add_room(hass):
    """Test adding a room via options flow."""
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="RadiatorSync",
        data={"heater": "switch.test_heater"},
        options={"rooms": {}, "presets": {"Away": 15.0}},
        source=config_entries.SOURCE_USER,
        entry_id="test_id",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"operation": "add_room"},
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "add_room"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Living Room",
            CONF_SENSOR_TEMP: "sensor.living_room_temp",
            CONF_HYSTERESIS: 0.5,
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["rooms"]["Living Room"] == {
        CONF_NAME: "Living Room",
        CONF_SENSOR_TEMP: "sensor.living_room_temp",
        CONF_HYSTERESIS: 0.5,
    }


async def test_options_flow_edit_room(hass):
    """Test editing a room via options flow."""
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="RadiatorSync",
        data={"heater": "switch.test_heater"},
        options={
            "rooms": {
                "Living Room": {
                    CONF_NAME: "Living Room",
                    CONF_SENSOR_TEMP: "sensor.living_room_temp",
                    CONF_HYSTERESIS: 0.5,
                }
            },
            "presets": {"Away": 15.0},
        },
        source=config_entries.SOURCE_USER,
        entry_id="test_id",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"operation": "edit_room"},
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "edit_room"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"name": "Living Room"},
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "edit_room_apply"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Lounge",
            CONF_SENSOR_TEMP: "sensor.lounge_temp",
            CONF_HYSTERESIS: 0.3,
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert "Living Room" not in result["data"]["rooms"]
    assert result["data"]["rooms"]["Lounge"] == {
        CONF_NAME: "Lounge",
        CONF_SENSOR_TEMP: "sensor.lounge_temp",
        CONF_HYSTERESIS: 0.3,
    }


async def test_options_flow_remove_room(hass):
    """Test removing a room via options flow."""
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="RadiatorSync",
        data={"heater": "switch.test_heater"},
        options={
            "rooms": {
                "Living Room": {
                    CONF_NAME: "Living Room",
                    CONF_SENSOR_TEMP: "sensor.living_room_temp",
                }
            },
            "presets": {"Away": 15.0},
        },
        source=config_entries.SOURCE_USER,
        entry_id="test_id",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"operation": "remove_room"},
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "remove_room"

    with patch("custom_components.radiator_sync.config_flow.er.async_get") as mock_er:
        mock_er.return_value.entities = {}
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"name": "Living Room"},
        )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert "Living Room" not in result["data"]["rooms"]


async def test_options_flow_manage_presets(hass):
    """Test managing presets via options flow."""
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="RadiatorSync",
        data={"heater": "switch.test_heater"},
        options={
            "rooms": {},
            "presets": {"Away": 15.0},
        },
        source=config_entries.SOURCE_USER,
        entry_id="test_id",
    )
    config_entry.add_to_hass(hass)

    # Add preset
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"operation": "manage_presets"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"preset_action": "add"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"name": "Night", "temperature": 18.5},
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["presets"]["Night"] == {"default": 18.5, "overrides": {}}

    # Edit preset
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"operation": "manage_presets"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"preset_action": "edit"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"name": "Night"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"name": "Night", "temperature": 19.0},
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["presets"]["Night"] == {"default": 19.0, "overrides": {}}

    # Remove preset
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"operation": "manage_presets"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"preset_action": "remove"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"name": "Night"},
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert "Night" not in result["data"]["presets"]


async def test_options_flow_preset_with_override(hass):
    """Test adding a preset with a room override via options flow."""
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="RadiatorSync",
        data={"heater": "switch.test_heater"},
        options={
            "rooms": {"Living Room": {CONF_NAME: "Living Room"}},
            "presets": {"Away": {"default": 15.0, "overrides": {}}},
        },
        source=config_entries.SOURCE_USER,
        entry_id="test_id",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"operation": "manage_presets"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"preset_action": "add"},
    )
    # The form should now contain 'override_Living Room'
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "name": "Night",
            "temperature": 18.5,
            "override_Living Room": 20.5
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"]["presets"]["Night"] == {
        "default": 18.5,
        "overrides": {"Living Room": 20.5}
    }



async def test_options_flow_errors(hass):
    """Test error cases in options flow."""
    config_entry = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="RadiatorSync",
        data={"heater": "switch.test_heater"},
        options={
            "rooms": {"Living Room": {CONF_NAME: "Living Room"}},
            "presets": {"Away": 15.0},
        },
        source=config_entries.SOURCE_USER,
        entry_id="test_id",
    )
    config_entry.add_to_hass(hass)

    # Duplicate room name
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"operation": "add_room"},
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Living Room",
            CONF_SENSOR_TEMP: "sensor.living_room_temp",
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "name_exists"}

    # No rooms abort
    config_entry_no_rooms = MockConfigEntry(
        version=1,
        domain=DOMAIN,
        title="RadiatorSync",
        data={"heater": "switch.test_heater"},
        options={"rooms": {}, "presets": {}},
        source=config_entries.SOURCE_USER,
        entry_id="test_id_empty",
    )
    config_entry_no_rooms.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(
        config_entry_no_rooms.entry_id
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"operation": "edit_room"},
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "no_rooms"
