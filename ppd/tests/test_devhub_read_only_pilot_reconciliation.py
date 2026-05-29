from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.devhub.read_only_pilot_operator_checklist import load_operator_checklist
from ppd.devhub.read_only_pilot_reconciliation import (
    REQUIRED_PACKET_ID,
    assert_valid_reconciliation_packet,
    load_reconciliation_packet,
    validate_reconciliation_packet,
)
from ppd.devhub.read_only_pilot_result_intake import load_pilot_result_intake
from ppd.release_gate_status import load_release_gate_status_packet


FIXTURE_DIR = Path(__file__).parent / "fixtures"
PACKET_PATH = FIXTURE_DIR / "devhub" / "read_only_pilot_reconciliation_packet.json"
OPERATOR_CHECKLIST_PATH = FIXTURE_DIR / "devhub" / "read_only_pilot_operator_checklist.json"
PILOT_RESULT_INTAKE_PATH = FIXTURE_DIR / "devhub" / "read_only_pilot_result_intake.json"
RELEASE_GATE_STATUS_PATH = FIXTURE_DIR / "release_gate_status" / "status_packet.json"


def _inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    return (
        load_reconciliation_packet(PACKET_PATH),
        load_operator_checklist(OPERATOR_CHECKLIST_PATH),
        load_pilot_result_intake(PILOT_RESULT_INTAKE_PATH),
        load_release_gate_status_packet(RELEASE_GATE_STATUS_PATH),
    )


def _errors(packet: dict[str, object]) -> tuple[str, ...]:
    _, operator_checklist, pilot_result_intake, release_gate_status = _inputs()
    return validate_reconciliation_packet(packet, operator_checklist, pilot_result_intake, release_gate_status).errors


def test_read_only_pilot_reconciliation_fixture_is_valid() -> None:
    packet, operator_checklist, pilot_result_intake, release_gate_status = _inputs()

    result = validate_reconciliation_packet(packet, operator_checklist, pilot_result_intake, release_gate_status)

    assert result.packet_id == REQUIRED_PACKET_ID
    assert result.ok is True
    assert result.errors == ()
    assert_valid_reconciliation_packet(packet, operator_checklist, pilot_result_intake, release_gate_status)


def test_reconciliation_consumes_required_source_packets() -> None:
    packet, operator_checklist, pilot_result_intake, release_gate_status = _inputs()

    packet["source_packets"]["operator_checklist"]["consumed"] = False

    errors = validate_reconciliation_packet(packet, operator_checklist, pilot_result_intake, release_gate_status).errors
    assert "source_packets.operator_checklist.consumed must be true" in errors


def test_reconciliation_rejects_devhub_or_playwright_launch() -> None:
    packet, _, _, _ = _inputs()
    packet["launches_devhub"] = True
    packet["launches_playwright"] = True

    errors = _errors(packet)

    assert "launches_devhub must be false" in errors
    assert "launches_playwright must be false" in errors


def test_reconciliation_records_only_redacted_observed_surfaces() -> None:
    packet, _, _, _ = _inputs()
    observed = packet["redacted_observed_surfaces"]
    assert isinstance(observed, list)
    observed[0]["redacted_heading"] = "Applicant email person@example.test"

    errors = _errors(packet)

    assert "redacted_observed_surfaces[0].redacted_heading must be a redacted token" in errors
    assert any("private value" in error for error in errors)


def test_reconciliation_requires_safe_read_only_coverage_gaps() -> None:
    packet, _, _, _ = _inputs()
    gaps = packet["safe_read_only_coverage_gaps"]
    assert isinstance(gaps, list)
    gaps[0]["safe_to_follow_up_read_only"] = False

    errors = _errors(packet)

    assert "safe_read_only_coverage_gaps[0].safe_to_follow_up_read_only must be true" in errors


def test_reconciliation_requires_manual_handoff_notes_to_stay_non_launching() -> None:
    packet, _, _, _ = _inputs()
    notes = packet["manual_handoff_notes"]
    assert isinstance(notes, list)
    notes[0]["launches_devhub"] = True

    errors = _errors(packet)

    assert "manual_handoff_notes[0].launches_devhub must be false" in errors


def test_reconciliation_requires_abort_reason_coverage() -> None:
    packet, _, _, _ = _inputs()
    packet["abort_reasons"] = [
        {
            "reason_id": "abort-too-small",
            "trigger": "Abort on credential handling only.",
            "operator_response": "Stop.",
            "records_only_redacted_metadata": True,
        }
    ]

    errors = _errors(packet)

    assert "abort_reasons missing required term: mfa" in errors
    assert "abort_reasons missing required term: upload" in errors
    assert "abort_reasons missing required term: browser artifact" in errors


def test_reconciliation_requires_next_attended_session_prerequisites_to_block_launch() -> None:
    packet, _, _, _ = _inputs()
    prereqs = packet["next_attended_session_prerequisites"]
    assert isinstance(prereqs, list)
    prereqs[0]["live_devhub_launch_allowed"] = True

    errors = _errors(packet)

    assert "next_attended_session_prerequisites[0].live_devhub_launch_allowed must be false" in errors


def test_reconciliation_rejects_private_or_session_keys_anywhere() -> None:
    packet, _, _, _ = _inputs()
    packet = deepcopy(packet)
    packet["redacted_observed_surfaces"][0]["screenshot_path"] = "redacted-token-only"

    errors = _errors(packet)

    assert "redacted_observed_surfaces[0] contains disallowed field(s): screenshot_path" in errors
    assert any("forbidden private/session field" in error for error in errors)


def test_assert_valid_reconciliation_packet_raises_stable_error() -> None:
    packet, operator_checklist, pilot_result_intake, release_gate_status = _inputs()
    packet["official_actions_enabled"] = True

    with pytest.raises(AssertionError, match="official_actions_enabled must be false"):
        assert_valid_reconciliation_packet(packet, operator_checklist, pilot_result_intake, release_gate_status)
