from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


REQUIRED_PACKET_ID = 'devhub-attended-read-only-pilot-runbook-v1'
REQUIRED_STEP_IDS = (
    'prepare_fixture_packet',
    'manual_login_handoff',
    'confirm_read_only_scope',
    'capture_redacted_observation',
    'monitor_abort_conditions',
    'write_commit_safe_journal',
    'post_action_hardening_review',
    'close_without_artifacts',
)
REQUIRED_JOURNAL_EVENTS = (
    'DevHub attended preflight',
    'manual handoff',
    'redacted read-only observation',
    'refused action',
    'post-action hardening review',
)
REQUIRED_ABORT_TERMS = (
    'credential',
    'mfa',
    'captcha',
    'payment',
    'submit',
    'certify',
    'upload',
    'schedule',
    'cancel',
    'private account data',
    'browser artifact',
    'timeout',
)
REQUIRED_FORBIDDEN_FIELDS = (
    'credentials',
    'cookies',
    'auth_state',
    'screenshot',
    'trace',
    'har',
    'raw_dom',
    'raw_authenticated_text',
    'private_field_value',
    'payment_details',
    'local_private_file_path',
)
REQUIRED_ALLOWED_FIELDS = (
    'stable_surface_id',
    'page_heading',
    'accessible_landmark_summary',
    'synthetic_record_status_label',
    'operator_decision_code',
    'redacted_timestamp',
)


@dataclass(frozen=True)
class RunbookValidationResult:
    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def load_runbook_packet(path: str | Path) -> dict[str, Any]:
    packet_path = Path(path)
    with packet_path.open('r', encoding='utf-8') as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ValueError('runbook packet must be a JSON object')
    return packet


def validate_runbook_packet(packet: Mapping[str, Any]) -> RunbookValidationResult:
    errors: list[str] = []
    packet_id = _text(packet.get('packet_id'))

    _require(errors, packet_id == REQUIRED_PACKET_ID, 'packet_id must identify the attended read-only pilot runbook')
    _require(errors, packet.get('packet_type') == 'devhub_attended_read_only_pilot_runbook', 'packet_type must be devhub_attended_read_only_pilot_runbook')
    _require(errors, packet.get('mode') == 'fixture_first', 'mode must be fixture_first')
    _require(errors, packet.get('read_only_only') is True, 'runbook must be read-only only')
    _require(errors, packet.get('launches_playwright') is False, 'runbook must not launch Playwright')
    _require(errors, packet.get('stores_browser_artifacts') is False, 'runbook must not store browser artifacts')
    _require(errors, packet.get('stores_private_session_state') is False, 'runbook must not store private session state')

    source_inputs = _mapping(packet.get('source_inputs'))
    _require(errors, source_inputs.get('attended_pilot_preflight') == 'devhub-attended-pilot-synthetic-readonly-review-v1', 'source_inputs must reference the attended pilot preflight packet')
    _require(errors, source_inputs.get('read_only_observation_checklist') == 'devhub_read_only_observation_checklist', 'source_inputs must reference the read-only observation checklist')

    steps = _sequence(packet.get('operator_steps'))
    step_ids = tuple(_text(_mapping(step).get('step_id')) for step in steps)
    missing_steps = [step_id for step_id in REQUIRED_STEP_IDS if step_id not in step_ids]
    if missing_steps:
        errors.append('operator_steps missing required steps: ' + ', '.join(missing_steps))
    for index, step in enumerate(steps):
        _validate_step(index, _mapping(step), errors)

    capture = _mapping(packet.get('redacted_observation_capture'))
    _require_all_present(errors, _string_tuple(capture.get('allowed_fields')), REQUIRED_ALLOWED_FIELDS, 'redacted observation allowed_fields')
    _require_all_present(errors, _string_tuple(capture.get('forbidden_fields')), REQUIRED_FORBIDDEN_FIELDS, 'redacted observation forbidden_fields')
    _require(errors, capture.get('raw_values_allowed') is False, 'redacted observation must reject raw values')
    _require(errors, capture.get('screenshots_allowed') is False, 'redacted observation must reject screenshots')
    _require(errors, capture.get('dom_capture_allowed') is False, 'redacted observation must reject DOM capture')

    abort_conditions = _string_tuple(packet.get('abort_conditions'))
    _require_all_terms(errors, abort_conditions, REQUIRED_ABORT_TERMS, 'abort_conditions')

    journal_templates = _mapping(packet.get('journal_templates'))
    for event_type in REQUIRED_JOURNAL_EVENTS:
        template = _mapping(journal_templates.get(event_type))
        _require(errors, template.get('event_type') == event_type, f'journal template missing {event_type}')
        _require(errors, template.get('commit_safe') is True, f'journal template {event_type} must be commit-safe')
        _require(errors, template.get('stores_private_values') is False, f'journal template {event_type} must not store private values')
        _require(errors, template.get('stores_browser_artifacts') is False, f'journal template {event_type} must not store browser artifacts')

    hardening = _mapping(packet.get('post_action_hardening_review'))
    _require(errors, hardening.get('required') is True, 'post-action hardening review must be required')
    _require(errors, hardening.get('official_state_changed') is False, 'post-action hardening must confirm no official state changed')
    _require(errors, hardening.get('next_actions_limited_to') == ['read_only', 'local_preview'], 'post-action hardening must limit next actions')

    return RunbookValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(errors))


def assert_valid_runbook_packet(packet: Mapping[str, Any]) -> None:
    result = validate_runbook_packet(packet)
    if not result.ok:
        raise AssertionError('; '.join(result.errors))


def _validate_step(index: int, step: Mapping[str, Any], errors: list[str]) -> None:
    prefix = f'operator_steps[{index}]'
    if not _text(step.get('step_id')):
        errors.append(f'{prefix}.step_id is required')
    if not _text(step.get('operator_action')):
        errors.append(f'{prefix}.operator_action is required')
    if step.get('automated') is not False:
        errors.append(f'{prefix}.automated must be false')
    if step.get('playwright_allowed') is not False:
        errors.append(f'{prefix}.playwright_allowed must be false')
    if step.get('stores_browser_artifacts') is not False:
        errors.append(f'{prefix}.stores_browser_artifacts must be false')


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(item for item in _sequence(value) if isinstance(item, str))


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return ''


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _require_all_present(errors: list[str], values: tuple[str, ...], required: tuple[str, ...], label: str) -> None:
    present = {value.casefold() for value in values}
    missing = [value for value in required if value.casefold() not in present]
    if missing:
        errors.append(f'{label} missing: ' + ', '.join(missing))


def _require_all_terms(errors: list[str], values: tuple[str, ...], terms: tuple[str, ...], label: str) -> None:
    haystack = '\n'.join(values).casefold()
    missing = [term for term in terms if term.casefold() not in haystack]
    if missing:
        errors.append(f'{label} missing required terms: ' + ', '.join(missing))
