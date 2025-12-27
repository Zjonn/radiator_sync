"""Test the Radiator Sync climate."""

from homeassistant.components.climate.const import HVACMode


async def test_climate(hass, setup_integration):
    """Test climate setup and state."""
    state = hass.states.get("climate.radiator_sync_test_entry_id_living_room_climate")
    assert state is not None
    assert state.state == HVACMode.HEAT
    assert state.attributes.get("current_temperature") == 20.0
    assert state.attributes.get("temperature") == 21.0

    # Change target temperature via service
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {
            "entity_id": "climate.radiator_sync_test_entry_id_living_room_climate",
            "temperature": 22.0,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("climate.radiator_sync_test_entry_id_living_room_climate")
    assert state.attributes.get("temperature") == 22.0
