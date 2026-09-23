"""Unit tests for HeaterStateManager's anti-short-cycle and re-evaluation logic.

Covers the overnight stuck-on incident (22->23 Sept): demand dropped to 0 while
the min-on window was still active, and because nothing ever re-checked the
heater once demand stopped changing, the boiler stayed on for ~9 hours.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from custom_components.radiator_sync.const import (
    CONF_HEATER,
    CONF_MIN_OFF,
    CONF_MIN_ON,
)
from custom_components.radiator_sync.heater import state_manager as state_manager_module
from custom_components.radiator_sync.heater.state_manager import HeaterStateManager


@pytest.fixture
def coordinator(hass):
    return SimpleNamespace(
        hass=hass,
        entry=SimpleNamespace(entry_id="test_entry"),
        async_save_runtime_state=AsyncMock(),
        async_refresh_entities=AsyncMock(),
    )


@pytest.fixture
def manager(coordinator):
    mgr = HeaterStateManager(
        coordinator,
        {CONF_HEATER: "switch.test_heater", CONF_MIN_ON: 480, CONF_MIN_OFF: 300},
    )
    mgr.threshold_heat_demand = 14.0
    return mgr


@pytest.fixture
def switch_calls(hass):
    """Record switch.turn_on/turn_off service calls made by the heater manager.

    `hass.services.async_call` is read-only and can't be monkeypatched
    directly, so we register real handlers for the two services instead.
    """
    calls = []

    async def _handler(call):
        calls.append(call)

    hass.services.async_register("switch", "turn_on", _handler)
    hass.services.async_register("switch", "turn_off", _handler)
    return calls


@pytest.fixture
def mock_call_later(monkeypatch):
    """Capture async_call_later invocations instead of scheduling real timers."""
    scheduled = []

    def _fake(hass, delay, action):
        unsub = Mock(name="unsub")
        scheduled.append(SimpleNamespace(delay=delay, action=action, unsub=unsub))
        return unsub

    monkeypatch.setattr(state_manager_module, "async_call_later", _fake)
    return scheduled


async def test_turn_on_immediately_when_no_prior_off(
    hass, manager, switch_calls, mock_call_later
):
    manager.last_off = None

    await manager.apply_heat_demand(20.0)
    await hass.async_block_till_done()

    assert len(switch_calls) == 1
    assert switch_calls[0].service == "turn_on"
    assert switch_calls[0].data == {"entity_id": "switch.test_heater"}
    assert mock_call_later == []


async def test_turn_off_immediately_when_min_on_elapsed(
    hass, manager, switch_calls, mock_call_later
):
    manager.is_running = True
    manager.last_on = datetime.now() - timedelta(seconds=manager.min_on_seconds + 5)

    await manager.apply_heat_demand(0.0)
    await hass.async_block_till_done()

    assert len(switch_calls) == 1
    assert switch_calls[0].service == "turn_off"
    assert switch_calls[0].data == {"entity_id": "switch.test_heater"}
    assert mock_call_later == []


async def test_stuck_on_bug_is_fixed_by_scheduled_reeval(
    hass, manager, switch_calls, mock_call_later
):
    """Regression test for the overnight incident.

    Demand drops to 0 just inside the min-on window and then never changes
    again. Previously the `heat_demand == demand` dedupe made every later call
    a no-op, and nothing ever turned the heater off. Now the deferred decision
    must be retried and the heater must turn off once the window elapses, even
    with no further demand changes.
    """
    manager.is_running = True
    manager.last_on = datetime.now()  # heater just turned on

    # Demand falls to zero while still inside the min-on window.
    await manager.apply_heat_demand(0.0)
    await hass.async_block_till_done()

    assert switch_calls == []
    assert len(mock_call_later) == 1
    assert mock_call_later[0].delay == pytest.approx(manager.min_on_seconds, abs=1)

    # Demand stays at 0 (as it did for ~9 hours overnight). The old dedupe
    # would have short-circuited this call entirely.
    await manager.apply_heat_demand(0.0)
    await hass.async_block_till_done()

    assert switch_calls == []
    assert len(mock_call_later) == 2  # re-evaluated and rescheduled, not dropped
    mock_call_later[0].unsub.assert_called_once()  # stale timer was cancelled

    # Time passes past the min-on window. The scheduled re-evaluation fires on
    # its own, with no further demand change required.
    manager.last_on = datetime.now() - timedelta(seconds=manager.min_on_seconds + 1)
    mock_call_later[1].action(datetime.now())
    await hass.async_block_till_done()

    assert len(switch_calls) == 1
    assert switch_calls[0].service == "turn_off"
    assert switch_calls[0].data == {"entity_id": "switch.test_heater"}


async def test_min_off_window_defers_and_reschedules_turn_on(
    hass, manager, switch_calls, mock_call_later
):
    manager.last_off = datetime.now()  # heater just turned off

    await manager.apply_heat_demand(20.0)
    await hass.async_block_till_done()

    assert switch_calls == []
    assert len(mock_call_later) == 1
    assert mock_call_later[0].delay == pytest.approx(manager.min_off_seconds, abs=1)

    manager.last_off = datetime.now() - timedelta(seconds=manager.min_off_seconds + 1)
    mock_call_later[0].action(datetime.now())
    await hass.async_block_till_done()

    assert len(switch_calls) == 1
    assert switch_calls[0].service == "turn_on"
    assert switch_calls[0].data == {"entity_id": "switch.test_heater"}


async def test_override_mode_skips_evaluation(
    hass, manager, switch_calls, mock_call_later
):
    manager._override_mode = "on"
    manager.is_running = False

    await manager.apply_heat_demand(50.0)
    await hass.async_block_till_done()

    assert manager.heat_demand == 50.0
    assert switch_calls == []
    assert mock_call_later == []


async def test_stop_cancels_pending_reeval(manager, mock_call_later):
    manager.is_running = True
    manager.last_on = datetime.now()

    await manager.apply_heat_demand(0.0)
    assert len(mock_call_later) == 1
    unsub = mock_call_later[0].unsub

    await manager.stop()

    unsub.assert_called_once()
    assert manager._pending_reeval_unsub is None


async def test_update_from_state_records_last_off(manager):
    manager.is_running = True
    manager.last_off = None

    await manager.update_from_state("off")

    assert manager.is_running is False
    assert manager.last_off is not None
    manager.coordinator.async_save_runtime_state.assert_awaited()
    manager.coordinator.async_refresh_entities.assert_awaited()


async def test_update_from_state_records_last_on(manager):
    manager.is_running = False
    manager.last_on = None

    await manager.update_from_state("on")

    assert manager.is_running is True
    assert manager.last_on is not None
