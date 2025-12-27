"""Test the Radiator Sync selects."""


async def test_select(hass, setup_integration):
    """Test select setup and state."""
    state = hass.states.get("select.radiator_sync_test_entry_id_heater_mode")
    assert state is not None
    assert state.state == "auto"

    # Change option via service
    await hass.services.async_call(
        "select",
        "select_option",
        {
            "entity_id": "select.radiator_sync_test_entry_id_heater_mode",
            "option": "on",
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("select.radiator_sync_test_entry_id_heater_mode")
    assert state.state == "on"
