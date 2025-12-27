"""Test the Radiator Sync binary sensors."""

from homeassistant.const import STATE_OFF, STATE_ON


async def test_binary_sensors(hass, setup_integration):
    """Test binary sensor setup and state."""
    # Check heater active binary sensor
    # With entry_id="test_entry_id", unique_id is "test_entry_id_heater_active"
    # HA slugifies the entity_id
    state = hass.states.get("binary_sensor.heater_heater_active")
    assert state is not None
    assert state.state == STATE_OFF

    # Trigger heater ON
    hass.states.async_set("switch.test_heater", STATE_ON)
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.heater_heater_active")
    assert state.state == STATE_ON
