"""Test the Radiator Sync global presets."""

from custom_components.radiator_sync.const import DEFAULT_PRESETS


async def test_global_preset_aggregation(hass, setup_integration):
    """Test that global preset reflects room presets and vice versa."""

    # Check initial state (should be none/Manual)
    entry_id = setup_integration.entry_id
    global_preset_entity = f"select.radiator_sync_{entry_id.lower()}_global_preset"

    global_preset = hass.states.get(global_preset_entity)
    assert global_preset is not None
    assert global_preset.state == "none"

    # Apply global preset
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": global_preset_entity, "option": "Night"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Check that all rooms updated
    climate_entities = hass.states.async_entity_ids("climate")
    state_lr = hass.states.get(climate_entities[0])
    assert state_lr.attributes.get("preset_mode") == "Night"
    assert state_lr.attributes.get("temperature") == DEFAULT_PRESETS["Night"]["default"]

    # Check global state reflects 'Night'
    global_preset = hass.states.get(global_preset_entity)
    assert global_preset.state == "Night"

    # Break sync in one room
    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": climate_entities[0], "temperature": 22.0},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Room preset should be gone
    state_lr = hass.states.get(climate_entities[0])
    assert state_lr.attributes.get("preset_mode") is None

    # Global preset should show 'none' (Manual)
    global_preset = hass.states.get(global_preset_entity)
    assert global_preset.state == "none"


async def test_room_preset_sync(hass, setup_integration):
    """Test that setting a preset on a single room affects global aggregator."""

    entry_id = setup_integration.entry_id
    global_preset_entity = f"select.radiator_sync_{entry_id.lower()}_global_preset"
    climate_entities = hass.states.async_entity_ids("climate")

    # 1. Manually set all rooms to Night one by one
    for entity_id in climate_entities:
        await hass.services.async_call(
            "climate",
            "set_preset_mode",
            {"entity_id": entity_id, "preset_mode": "Night"},
            blocking=True,
        )
    await hass.async_block_till_done()

    # Now all rooms are Night, global should be Night
    global_preset = hass.states.get(global_preset_entity)
    assert global_preset.state == "Night"


async def test_preset_room_override(hass, setup_integration):
    """Test that room-specific overrides work."""
    entry = setup_integration

    # Update config entry with an override for 'Living Room'
    new_options = {
        **entry.options,
        "presets": {"Night": {"default": 19.5, "overrides": {"Living Room": 22.5}}},
    }
    hass.config_entries.async_update_entry(entry, options=new_options)
    await hass.async_block_till_done()

    climate_entities = hass.states.async_entity_ids("climate")
    # In conftest.py, we have 'Living Room'
    living_room_entity = next(e for e in climate_entities if "living_room" in e)

    # Apply Night preset to Living Room
    await hass.services.async_call(
        "climate",
        "set_preset_mode",
        {"entity_id": living_room_entity, "preset_mode": "Night"},
        blocking=True,
    )
    await hass.async_block_till_done()

    # Check that override was applied (22.5 instead of default 19.5)
    state = hass.states.get(living_room_entity)
    assert state.attributes.get("temperature") == 22.5
