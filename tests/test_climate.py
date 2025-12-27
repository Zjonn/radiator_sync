"""Test the Radiator Sync climate."""

from homeassistant.components.climate.const import HVACMode


async def test_climate(hass, setup_integration):
    """Test climate setup and state."""
    state = hass.states.get("climate.living_room_radiator")
    assert state is not None
    assert state.state == HVACMode.HEAT
    assert state.attributes.get("current_temperature") == 20.0
    assert state.attributes.get("temperature") == 21.0

    # Change target temperature via service
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {
            "entity_id": "climate.living_room_radiator",
            "temperature": 22.0,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("climate.living_room_radiator")
    assert state.attributes.get("temperature") == 22.0
