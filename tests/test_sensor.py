"""Test the Radiator Sync sensors."""

async def test_sensors(hass, setup_integration):
    """Test sensor setup and state."""
    # Check heater heat demand sensor
    state = hass.states.get("sensor.heater_heat_demand")
    assert state is not None
    assert state.state == "50.0"

    # Check room heat demand sensor
    state = hass.states.get("sensor.living_room_heat_demand")
    assert state is not None
    assert state.state == "50"
