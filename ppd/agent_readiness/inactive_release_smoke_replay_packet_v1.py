from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PACKET_TYPE = "ppd.fixture_first_inactive_release_smoke_replay.v1"
PACKET_VERSION = "v1"
INACTIVE_MANIFEST_PACKET_TYPE = "ppd.inactive_release_candidate_manifest.v1"
MODE = "offline_fixture_replay_against_inactive_release_candidate_manifest_only"
REQUIRED_SCENARIO_TYPES = {
    "missing_information",
    "blocked_action",
    "next_safe_action",
    "reversible_draft",
    "exact_confirmation",
}
REQUIRED_OUTCOMES = {"pass", "hold", "reject"}
EXACT_OFFLINE_VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]
REQUIRED_BOUNDARY_FLAGS = (
    "fixture_first",
    "inactive_manifest_only",
    "no_private_user_facts",
    "no_live_crawling",
    "no_devhub_access",
    "no_browser_automation",
    "no_form_filling",
    "no_uploads",
    "no_submissions",
    "no_certifications",
    "no_payments",
    "no_scheduling",
    "no_release_activation",
    "no_active_prompt_mutation",
    "no_active_guardrail_mutation",
    "no_active_process_model_mutation",
    "no_active_requirement_mutation",
    "no_active_contract_mutation",
    "no_active_source_mutation",
    "no_active_archive_mutation",
    "no_active_document_mutation",
    "no_active_devhub_surface_mutation",
    "no_active_crawler_mutation",
    "no_active_release_mutation",
    "no_active_daemon_state_mutation",
)
REQUIRED_ACTION_CONTROL_FLAGS = (
    "requires_devhub",
    "uses_browser",
    "fills_form",
    "uploads",
    "submits",
    "certifies",
    "pays_fee",
    "schedules",
    "mutates_release_state",
)
FORBIDDEN_KEY_TOKENS = (
    "applicant",
    "auth_state",
    "browser_state",
    "card_number",
    "cookie",
    "credential",
    "devhub_session",
    "downloaded_artifact",
    "downloaded_document",
    "email",
    "har",
    "password",
    "payment_detail",
    "permit_number",
    "phone",
    "private_path",
    "raw_artifact",
    "raw_crawl",
    "raw_download",
    "raw_html",
    "raw_pdf",
    "screenshot",
    "session_state",
    "site_address",
    "storage_state",
    "tax_account",
    "token",
    "trace",
    "warc_payload",
)
PRIVATE_OR_ARTIFACT_VALUE_TOKENS = (
    "/home/",
    "/users/",
    "c:/users/",
    "c:\\users\\",
    "auth state",
    "browser state",
    "cookie jar",
    "downloaded artifact",
    "downloaded document",
    "har file",
    "private devhub",
    "private file",
    "raw body",
    "raw crawl",
    "raw html",
    "raw pdf",
    "session storage",
    "storage state",
    "trace.zip",
    "warc payload",
)
LIVE_OR_DEVHUB_CLAIM_TOKENS = (
    "authenticated devhub",
    "browser automation completed",
    "crawler started",
    "devhub access completed",
    "devhub accessed",
    "devhub automation completed",
    "devhub login completed",
    "devhub observation completed",
    "devhub session opened",
    "live crawl completed",
    "live crawl performed",
    "live devhub",
    "public crawl completed",
)
OFFICIAL_ACTION_TOKENS = (
    "application submitted",
    "certification completed",
    "certified acknowledgement",
    "certify acknowledgement completed",
    "click submit completed",
    "fee paid",
    "fee payment completed",
    "final action completed",
    "inspection scheduled",
    "official action completed",
    "official action performed",
    "paid fees",
    "payment completed",
    "permit submitted",
    "schedule inspection completed",
    "submit payment completed",
    "submit permit completed",
    "submission completed",
    "upload completed",
    "upload corrections completed",
    "uploaded corrections",
    "uploaded plans",
)
RELEASE_ACTIVATION_TOKENS = (
    "active release enabled",
    "activated release",
    "candidate promoted",
    "release activated",
    "release activation completed",
    "release activation enabled",
    "release promoted",
    "release promotion completed",
)
ACTIVE_MUTATION_KEYS = {
    "active_archive_mutation",
    "active_contract_mutation",
    "active_crawler_mutation",
    "active_daemon_state_mutation",
    "active_devhub_surface_mutation",
    "active_document_mutation",
    "active_guardrail_mutation",
    "active_manifest_mutation",
    "active_process_model_mutation",
    "active_process_mutation",
    "active_prompt_mutation",
    "active_release_mutation",
    "active_requirement_mutation",
    "active_source_mutation",
    "active_surface_mutation",
    "active_mutation",
    "mutation_enabled",
    "mutates_active_state",
    "release_activation_enabled",
    "release_promotion_enabled",
}


class InactiveReleaseSmokeReplayPacketV1Error(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("invalid inactive release smoke replay packet v1: " + "; ".join(self.errors))


def load_inactive_release_smoke_replay_packet_v1(path: Path) -> dict[str, Any]:
    packet = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise InactiveReleaseSmokeReplayPacketV1Error(["packet must be an object"])
    assert_valid_inactive_release_smoke_replay_packet_v1(packet)
    return packet


def assert_valid_inactive_release_smoke_replay_packet_v1(packet: Mapping[str, Any]) -> None:
    errors = validate_inactive_release_smoke_replay_packet_v1(packet)
    if errors:
        raise InactiveReleaseSmokeReplayPacketV1Error(errors)


def validate_inactive_release_smoke_replay_packet_v1(packet: Mapping[str, Any]) -> list[str]:
    if not isinstance(packet, Mapping):
        return ["packet must be an object"]

    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append("packet_version must be v1")
    if packet.get("mode") != MODE:
        errors.append(f"mode must be {MODE}")
    if packet.get("validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("validation_commands must contain only the exact offline self-test command")

    errors.extend(_validate_boundaries(packet.get("boundaries")))
    evidence_ids = _validate_candidate_manifest(packet.get("inactive_release_candidate_manifest"), errors)
    errors.extend(_validate_replay_scenarios(packet.get("replay_scenarios"), evidence_ids))
    errors.extend(_scan_for_forbidden_content(packet))
    return errors


def _validate_boundaries(boundaries: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(boundaries, Mapping):
        return ["boundaries must be an object"]
    for flag in REQUIRED_BOUNDARY_FLAGS:
        if boundaries.get(flag) is not True:
            errors.append(f"boundaries.{flag} must be true")
    return errors


def _validate_candidate_manifest(manifest: Any, errors: list[str]) -> set[str]:
    if not isinstance(manifest, Mapping):
        errors.append("inactive_release_candidate_manifest must be an object")
        return set()

    if manifest.get("packet_type") != INACTIVE_MANIFEST_PACKET_TYPE:
        errors.append(f"inactive_release_candidate_manifest.packet_type must be {INACTIVE_MANIFEST_PACKET_TYPE}")
    if not _nonempty_text(manifest.get("manifest_id")):
        errors.append("inactive_release_candidate_manifest.manifest_id must be a non-empty candidate manifest reference")
    if manifest.get("candidate_status") != "inactive_pending_reviewer_signoff":
        errors.append("inactive_release_candidate_manifest.candidate_status must remain inactive_pending_reviewer_signoff")
    if manifest.get("release_activation_enabled") is not False:
        errors.append("inactive_release_candidate_manifest.release_activation_enabled must be false")
    if manifest.get("release_promotion_enabled") is not False:
        errors.append("inactive_release_candidate_manifest.release_promotion_enabled must be false")

    evidence_ids = set(_string_list(manifest.get("immutable_evidence_ids")))
    if not evidence_ids:
        errors.append("inactive_release_candidate_manifest.immutable_evidence_ids must be a non-empty list")
    for evidence_id in sorted(evidence_ids):
        if not _is_immutable_evidence_id(evidence_id):
            errors.append(f"inactive_release_candidate_manifest.immutable_evidence_ids contains invalid evidence id: {evidence_id}")
    return evidence_ids


def _validate_replay_scenarios(scenarios: Any, evidence_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("replay_scenarios must be a non-empty list")
        scenarios = []

    seen_scenario_types: set[str] = set()
    seen_outcomes: set[str] = set()
    for index, scenario in enumerate(scenarios):
        path = f"replay_scenarios[{index}]"
        if not isinstance(scenario, Mapping):
            errors.append(f"{path} must be an object")
            continue
        scenario_type = scenario.get("scenario_type")
        outcome = scenario.get("outcome")
        if isinstance(scenario_type, str):
            seen_scenario_types.add(scenario_type)
        if isinstance(outcome, str):
            seen_outcomes.add(outcome)
        errors.extend(_validate_scenario(scenario, path, evidence_ids))

    missing_scenarios = REQUIRED_SCENARIO_TYPES - seen_scenario_types
    if missing_scenarios:
        errors.append("missing required scenario types: " + ", ".join(sorted(missing_scenarios)))
    missing_outcomes = REQUIRED_OUTCOMES - seen_outcomes
    if missing_outcomes:
        errors.append("missing required replay outcomes: " + ", ".join(sorted(missing_outcomes)))
    return errors


def _validate_scenario(scenario: Mapping[str, Any], path: str, evidence_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if scenario.get("scenario_type") not in REQUIRED_SCENARIO_TYPES:
        errors.append(f"{path}.scenario_type must be one of the required scenario types")
    if scenario.get("outcome") not in REQUIRED_OUTCOMES:
        errors.append(f"{path}.outcome must be pass, hold, or reject")
    for field in ("scenario_id", "agent_facing_prompt", "expected_agent_response", "decision_reason"):
        if not _nonempty_text(scenario.get(field)):
            errors.append(f"{path}.{field} must be non-empty text")

    citation_references = _string_list(scenario.get("citation_references"))
    if not citation_references:
        errors.append(f"{path}.citation_references must be a non-empty list")
    for citation in citation_references:
        if citation not in evidence_ids:
            errors.append(f"{path}.citation_references contains unknown inactive manifest evidence id: {citation}")

    if scenario.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append(f"{path}.offline_validation_commands must contain only the exact offline self-test command")

    action_controls = scenario.get("action_controls")
    if not isinstance(action_controls, Mapping):
        errors.append(f"{path}.action_controls must be an object")
    else:
        for flag in REQUIRED_ACTION_CONTROL_FLAGS:
            if action_controls.get(flag) is not False:
                errors.append(f"{path}.action_controls.{flag} must be false")
    return errors


def _scan_for_forbidden_content(value: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            lowered_key = key_text.lower().replace("-", "_")
            if lowered_key in ACTIVE_MUTATION_KEYS and nested is not False:
                errors.append(f"{nested_path} contains an active mutation or release activation flag")
            if any(token in lowered_key for token in FORBIDDEN_KEY_TOKENS) and _truthy(nested):
                errors.append(f"{nested_path} contains a forbidden private, session, browser, raw, or downloaded artifact key")
            errors.extend(_scan_for_forbidden_content(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            errors.extend(_scan_for_forbidden_content(nested, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered_value = value.lower()
        if any(token in lowered_value for token in PRIVATE_OR_ARTIFACT_VALUE_TOKENS):
            errors.append(f"{path} contains forbidden private, session, browser, raw, or downloaded artifact content")
        if any(token in lowered_value for token in LIVE_OR_DEVHUB_CLAIM_TOKENS):
            errors.append(f"{path} contains a forbidden live crawl or DevHub execution claim")
        if any(token in lowered_value for token in OFFICIAL_ACTION_TOKENS):
            errors.append(f"{path} contains a forbidden official-action completion claim")
        if any(token in lowered_value for token in RELEASE_ACTIVATION_TOKENS):
            errors.append(f"{path} contains a forbidden release activation or promotion claim")
    return errors


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _truthy(value: Any) -> bool:
    if value is None or value is False or value == "":
        return False
    if isinstance(value, Mapping) and not value:
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and not value:
        return False
    return True


def _is_immutable_evidence_id(value: str) -> bool:
    prefix = "ev:ppd-fixture:"
    marker = ":sha256:"
    if not value.startswith(prefix) or marker not in value:
        return False
    slug, digest = value[len(prefix):].rsplit(marker, 1)
    return bool(slug) and all(ch.islower() or ch.isdigit() or ch == "-" for ch in slug) and len(digest) == 64 and all(ch in "0123456789abcdef" for ch in digest)
