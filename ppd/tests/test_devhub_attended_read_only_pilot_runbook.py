from __future__ import annotations

from pathlib import Path

import pytest

from ppd.devhub.attended_read_only_pilot_runbook import (
    REQUIRED_PACKET_ID,
    assert_valid_runbook_packet,
    load_runbook_packet,
    validate_runbook_packet,
)


FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'devhub' / 'attended_read_only_pilot_runbook_packet.json'


def test_fixture_runbook_packet_is_valid() -> None:
    packet = load_runbook_packet(FIXTURE_PATH)

    result = validate_runbook_packet(packet)

    assert result.packet_id == REQUIRED_PACKET_ID
    assert result.ok is True
    assert result.errors == ()


def test_fixture_runbook_blocks_playwright_and_browser_artifacts() -> None:
    packet = load_runbook_packet(FIXTURE_PATH)

    assert packet['launches_playwright'] is False
    assert packet['stores_browser_artifacts'] is False
    assert packet['stores_private_session_state'] is False
    assert all(step['playwright_allowed'] is False for step in packet['operator_steps'])


def test_validator_rejects_playwright_launch() -> None:
    packet = load_runbook_packet(FIXTURE_PATH)
    packet['launches_playwright'] = True

    result = validate_runbook_packet(packet)

    assert result.ok is False
    assert 'runbook must not launch Playwright' in result.errors


def test_validator_rejects_missing_scope_confirmation_step() -> None:
    packet = load_runbook_packet(FIXTURE_PATH)
    packet['operator_steps'] = [
        step for step in packet['operator_steps'] if step['step_id'] != 'confirm_read_only_scope'
    ]

    result = validate_runbook_packet(packet)

    assert result.ok is False
    assert any('confirm_read_only_scope' in error for error in result.errors)


def test_validator_rejects_incomplete_abort_conditions() -> None:
    packet = load_runbook_packet(FIXTURE_PATH)
    packet['abort_conditions'] = ['A timeout stops the pilot.']

    result = validate_runbook_packet(packet)

    assert result.ok is False
    assert any('abort_conditions missing required terms' in error for error in result.errors)


def test_assert_valid_runbook_packet_raises_stable_error() -> None:
    packet = load_runbook_packet(FIXTURE_PATH)
    packet['journal_templates']['manual handoff']['stores_private_values'] = True

    with pytest.raises(AssertionError, match='manual handoff must not store private values'):
        assert_valid_runbook_packet(packet)
