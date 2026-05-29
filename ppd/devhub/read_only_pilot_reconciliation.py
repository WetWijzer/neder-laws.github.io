from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.read_only_pilot_operator_checklist import validate_operator_checklist
from ppd.devhub.read_only_pilot_result_intake import validate_pilot_result_intake
from ppd.release_gate_status import validate_release_gate_status_packet


REQUIRED_PACKET_TYPE = "ppd.devhub_read_only_pilot_readiness_reconciliation.v1"
REQUIRED_PACKET_ID = "devhub-read-only-pilot-readiness-reconciliation-v1"
REQUIRED_ABORT_TERMS = (
    "automated login",
    "credential",
    "mfa",
    "captcha",
    "account creation",
    "private field value",
    "upload",
    "submit",
    "certify",
    "payment",
    "schedule",
    "cancel",
    "browser artifact",
)
REQUIRED_SECTIONS = (
    "redacted_observed_surfaces",
    "safe_read_only_coverage_gaps",
    "manual_handoff_notes",
    "abort_reasons",
    "next_attended_session_prerequisites",
)
ALLOWED_OBSERVATION_KEYS = {
    "surface_id",
    "source_observation_id",
    "redacted_heading",
    "redacted_labels",
    "status_category",
    "journal_event_id",
}
FORBIDDEN_KEYS = {
    "auth_state",
    "auth_state_path",
    "browser_context",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "field_value",
    "har",
    "har_path",
    "local_path",
    "password",
    "private_field_value",
    "raw_authenticated_text",
    "raw_dom",
    "screenshot",
    "screenshot_path",
    "session_state",
    "storage_state",
    "storage_state_path",
    "trace",
    "trace_path",
}
FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b"),
    re.compile(r"/(?:home|Users|tmp|var/tmp)/"),
    re.compile(r"\b(?:auth_state\.json|storage_state\.json|trace\.zip)\b", re.IGNORECASE),
    re.compile(r"\.har\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class ReconciliationValidationResult:
    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def load_reconciliation_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("read-only pilot reconciliation packet must be a JSON object")
    return data


def assert_valid_reconciliation_packet(
    packet: Mapping[str, Any],
    operator_checklist: Mapping[str, Any],
    pilot_result_intake: Mapping[str, Any],
    release_gate_status: Mapping[str, Any],
) -> None:
    result = validate_reconciliation_packet(packet, operator_checklist, pilot_result_intake, release_gate_status)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def validate_reconciliation_packet(
    packet: Mapping[str, Any],
    operator_checklist: Mapping[str, Any],
    pilot_result_intake: Mapping[str, Any],
    release_gate_status: Mapping[str, Any],
) -> ReconciliationValidationResult:
    errors: list[str] = []
    packet_id = _text(packet.get("packet_id"))

    _merge_source_errors(errors, "operator_checklist", validate_operator_checklist(operator_checklist).errors)
    _merge_source_errors(errors, "pilot_result_intake", validate_pilot_result_intake(pilot_result_intake).errors)
    _merge_source_errors(errors, "release_gate_status", validate_release_gate_status_packet(release_gate_status).errors)

    _require(errors, packet_id == REQUIRED_PACKET_ID, "packet_id must identify the read-only pilot reconciliation packet")
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == "fixture_first_reconciliation", "mode must be fixture_first_reconciliation")
    _require(errors, packet.get("fixture_first") is True, "fixture_first must be true")
    _require(errors, packet.get("read_only_only") is True, "read_only_only must be true")
    _require(errors, packet.get("metadata_only") is True, "metadata_only must be true")
    _require(errors, packet.get("launches_devhub") is False, "launches_devhub must be false")
    _require(errors, packet.get("launches_playwright") is False, "launches_playwright must be false")
    _require(errors, packet.get("live_session_authorized") is False, "live_session_authorized must be false")
    _require(errors, packet.get("official_actions_enabled") is False, "official_actions_enabled must be false")
    _require(errors, packet.get("stores_private_values") is False, "stores_private_values must be false")
    _require(errors, packet.get("stores_browser_artifacts") is False, "stores_browser_artifacts must be false")

    _validate_source_links(errors, packet.get("source_packets"), operator_checklist, pilot_result_intake, release_gate_status)
    _validate_observed_surfaces(errors, packet.get("redacted_observed_surfaces"))
    _validate_coverage_gaps(errors, packet.get("safe_read_only_coverage_gaps"))
    _validate_manual_handoff_notes(errors, packet.get("manual_handoff_notes"))
    _validate_abort_reasons(errors, packet.get("abort_reasons"))
    _validate_prerequisites(errors, packet.get("next_attended_session_prerequisites"))
    _validate_release_blocker_consumed(errors, release_gate_status)
    _scan_for_forbidden_content(errors, packet, "packet")

    return ReconciliationValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(_dedupe(errors)))


def _validate_source_links(
    errors: list[str],
    value: Any,
    operator_checklist: Mapping[str, Any],
    pilot_result_intake: Mapping[str, Any],
    release_gate_status: Mapping[str, Any],
) -> None:
    links = _mapping(value)
    expected = {
        "operator_checklist": _text(operator_checklist.get("packet_id")),
        "pilot_result_intake": _text(pilot_result_intake.get("packet_id")),
        "release_gate_status": _text(release_gate_status.get("packet_id")),
    }
    for key, packet_id in expected.items():
        link = _mapping(links.get(key))
        _require(errors, link.get("packet_id") == packet_id, f"source_packets.{key}.packet_id must match consumed packet")
        _require(errors, link.get("consumed") is True, f"source_packets.{key}.consumed must be true")
        _require(errors, _text(link.get("path")).startswith("ppd/tests/fixtures/"), f"source_packets.{key}.path must point to a committed PP&D fixture")


def _validate_observed_surfaces(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("redacted_observed_surfaces must be a non-empty list")
        return
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"redacted_observed_surfaces[{index}]"
        unknown = sorted(set(item) - ALLOWED_OBSERVATION_KEYS)
        if unknown:
            errors.append(f"{path} contains disallowed field(s): " + ", ".join(unknown))
        for field in ("surface_id", "source_observation_id", "redacted_heading", "status_category", "journal_event_id"):
            _require(errors, bool(_text(item.get(field))), f"{path}.{field} is required")
        _require(errors, _text(item.get("redacted_heading")).startswith("[REDACTED_HEADING:"), f"{path}.redacted_heading must be a redacted token")
        labels = item.get("redacted_labels")
        _require(errors, _text_list(labels), f"{path}.redacted_labels must be a non-empty list")
        for label in _text_list(labels):
            _require(errors, label.startswith("[REDACTED_LABEL:"), f"{path}.redacted_labels must contain only redacted tokens")


def _validate_coverage_gaps(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("safe_read_only_coverage_gaps must be a non-empty list")
        return
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"safe_read_only_coverage_gaps[{index}]"
        for field in ("gap_id", "scope", "reason"):
            _require(errors, bool(_text(item.get(field))), f"{path}.{field} is required")
        _require(errors, item.get("observed") is False, f"{path}.observed must be false")
        _require(errors, item.get("safe_to_follow_up_read_only") is True, f"{path}.safe_to_follow_up_read_only must be true")
        _require(errors, item.get("no_live_devhub_needed") is True, f"{path}.no_live_devhub_needed must be true")


def _validate_manual_handoff_notes(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("manual_handoff_notes must be a non-empty list")
        return
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"manual_handoff_notes[{index}]"
        _require(errors, bool(_text(item.get("note_id"))), f"{path}.note_id is required")
        _require(errors, item.get("category") == "manual_handoff", f"{path}.category must be manual_handoff")
        _require(errors, bool(_text(item.get("note"))), f"{path}.note is required")
        _require(errors, item.get("attended_session_required") is True, f"{path}.attended_session_required must be true")
        _require(errors, item.get("launches_devhub") is False, f"{path}.launches_devhub must be false")


def _validate_abort_reasons(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("abort_reasons must be a non-empty list")
        return
    combined = "\n".join(_text(_mapping(row).get("trigger")) for row in rows).casefold()
    for term in REQUIRED_ABORT_TERMS:
        if term.casefold() not in combined:
            errors.append("abort_reasons missing required term: " + term)
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"abort_reasons[{index}]"
        _require(errors, bool(_text(item.get("reason_id"))), f"{path}.reason_id is required")
        _require(errors, bool(_text(item.get("trigger"))), f"{path}.trigger is required")
        _require(errors, bool(_text(item.get("operator_response"))), f"{path}.operator_response is required")
        _require(errors, item.get("records_only_redacted_metadata") is True, f"{path}.records_only_redacted_metadata must be true")


def _validate_prerequisites(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("next_attended_session_prerequisites must be a non-empty list")
        return
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"next_attended_session_prerequisites[{index}]"
        for field in ("prerequisite_id", "required_before", "acceptance_criteria"):
            _require(errors, bool(_text(item.get(field))), f"{path}.{field} is required")
        _require(errors, item.get("attended_operator_required") is True, f"{path}.attended_operator_required must be true")
        _require(errors, item.get("live_devhub_launch_allowed") is False, f"{path}.live_devhub_launch_allowed must be false")


def _validate_release_blocker_consumed(errors: list[str], release_gate_status: Mapping[str, Any]) -> None:
    blockers = _sequence(release_gate_status.get("open_blockers"))
    if not any(_mapping(blocker).get("area") == "devhub_pilot_result_intake_readiness" for blocker in blockers):
        errors.append("release gate status must include the DevHub pilot result intake readiness blocker")


def _scan_for_forbidden_content(errors: list[str], value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.casefold() in FORBIDDEN_KEYS:
                errors.append(f"{path}.{key_text} contains forbidden private/session field")
            _scan_for_forbidden_content(errors, child, f"{path}.{key_text}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_content(errors, child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                errors.append(f"{path} contains private value or browser artifact reference")
                break


def _merge_source_errors(errors: list[str], label: str, source_errors: Sequence[str]) -> None:
    for error in source_errors:
        errors.append(f"{label}: {error}")


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _text_list(value: Any) -> tuple[str, ...]:
    return tuple(item for item in _sequence(value) if isinstance(item, str) and item.strip())


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)
