"""Test the Radiator Sync numbers."""


async def test_number(hass, setup_integration):
    """Test number setup and state."""
    state = hass.states.get("number.radiator_sync_test_entry_id_heater_threshold")
    assert state is not None
    assert state.state == "0.0"

    # Change value via service
    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.radiator_sync_test_entry_id_heater_threshold",
            "value": 15.0,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("number.radiator_sync_test_entry_id_heater_threshold")
    assert state.state == "15.0"
