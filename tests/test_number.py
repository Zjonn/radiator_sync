"""Test the Radiator Sync numbers."""

async def test_number(hass, setup_integration):
    """Test number setup and state."""
    state = hass.states.get("number.heater_threshold_heat_demand")
    assert state is not None
    assert state.state == "0.0"

    # Change threshold via service
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.heater_threshold_heat_demand", "value": 10.0},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("number.heater_threshold_heat_demand")
    assert state.state == "10.0"
