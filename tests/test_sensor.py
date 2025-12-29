"""Test the Radiator Sync sensors."""


async def test_sensors(hass, setup_integration):
    """Test sensor setup and state."""
    # Check heater heat demand sensor
    state = hass.states.get("sensor.heater_heater_heat_demand")
    assert state is not None
    # Initial setup in conftest doesn't trigger orchestration to 50.0 immediately
    # Unless target_temp was set to something that causes 50% demand relative to 20.0
    # Living room is set to 21.0, current 20.0. ΔT = 1.0.
    # MAX_DELTA = 2.0. So 1.0 / 2.0 = 50%.
    assert state.state == "50"

    # Check room heat demand sensor
    state = hass.states.get("sensor.living_room_heat_demand")
    assert state is not None
    assert state.state == "50"
