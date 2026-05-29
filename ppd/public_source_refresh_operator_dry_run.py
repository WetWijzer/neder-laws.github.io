"""Fixture-first public source refresh operator dry-run transcript builder.

This module intentionally performs no network, processor, download, or schedule mutation work.
It only combines already-captured candidate packets into a deterministic operator transcript.
"""

from __future__ import annotations

from typing import Any


def _list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _evidence_refs(*packets: dict[str, Any], key: str) -> list[str]:
    refs: list[str] = []
    for packet in packets:
        for item in _list(packet.get(key)):
            if isinstance(item, str) and item not in refs:
                refs.append(item)
            elif isinstance(item, dict):
                ref = item.get("ref") or item.get("id") or item.get("url")
                if isinstance(ref, str) and ref not in refs:
                    refs.append(ref)
    return refs


def _source_ids(*packets: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for packet in packets:
        for key in ("source_id", "source_ids"):
            for item in _list(packet.get(key)):
                if isinstance(item, str) and item not in ids:
                    ids.append(item)
        for item in _list(packet.get("sources")):
            if isinstance(item, dict):
                source_id = item.get("source_id") or item.get("id")
                if isinstance(source_id, str) and source_id not in ids:
                    ids.append(source_id)
    return ids


def build_public_source_refresh_operator_dry_run_transcript(
    source_refresh_runbook_candidate: dict[str, Any],
    public_source_refresh_batch_packet: dict[str, Any],
    public_source_refresh_intake_evidence_packet: dict[str, Any],
    source_registry_schedule_update_candidate: dict[str, Any],
    *,
    reviewer: str,
    owner: str,
) -> dict[str, Any]:
    """Return an ordered simulated operator transcript from fixture packets."""

    sources = _source_ids(
        source_refresh_runbook_candidate,
        public_source_refresh_batch_packet,
        public_source_refresh_intake_evidence_packet,
        source_registry_schedule_update_candidate,
    )
    allowlist_refs = _evidence_refs(
        source_refresh_runbook_candidate,
        public_source_refresh_batch_packet,
        public_source_refresh_intake_evidence_packet,
        source_registry_schedule_update_candidate,
        key="allowlist_evidence_refs",
    )
    robots_refs = _evidence_refs(
        source_refresh_runbook_candidate,
        public_source_refresh_batch_packet,
        public_source_refresh_intake_evidence_packet,
        source_registry_schedule_update_candidate,
        key="robots_evidence_refs",
    )

    steps = [
        {
            "order": 1,
            "name": "load-runbook-candidate",
            "simulation_only": True,
            "inputs": ["source_refresh_runbook_candidate"],
            "expected_metadata_only_observation": "Runbook candidate identifier, scope, and declared operator gates are readable from fixture metadata.",
        },
        {
            "order": 2,
            "name": "load-public-source-refresh-batch",
            "simulation_only": True,
            "inputs": ["public_source_refresh_batch_packet"],
            "expected_metadata_only_observation": "Batch packet source identifiers and refresh intent are readable without fetching source URLs.",
        },
        {
            "order": 3,
            "name": "verify-intake-evidence",
            "simulation_only": True,
            "inputs": ["public_source_refresh_intake_evidence_packet"],
            "allowlist_evidence_refs": allowlist_refs,
            "robots_evidence_refs": robots_refs,
            "expected_metadata_only_observation": "Allowlist and robots references are present as fixture references only.",
        },
        {
            "order": 4,
            "name": "preview-schedule-update-candidate",
            "simulation_only": True,
            "inputs": ["source_registry_schedule_update_candidate"],
            "expected_metadata_only_observation": "Schedule update candidate can be reviewed without mutating registry schedules.",
        },
        {
            "order": 5,
            "name": "record-reviewer-owner-attestation",
            "simulation_only": True,
            "reviewer": reviewer,
            "owner": owner,
            "expected_metadata_only_observation": "Reviewer and owner fields are attached to the dry-run transcript.",
        },
    ]

    return {
        "packet_type": "public_source_refresh_operator_dry_run_transcript",
        "mode": "fixture_first_dry_run",
        "sources": sources,
        "reviewer": reviewer,
        "owner": owner,
        "ordered_simulated_operator_steps": steps,
        "allowlist_evidence_refs": allowlist_refs,
        "robots_evidence_refs": robots_refs,
        "abort_or_rollback_checkpoints": [
            {
                "checkpoint": "missing-allowlist-or-robots-reference",
                "operator_action": "abort before any live source interaction",
            },
            {
                "checkpoint": "unexpected-non-metadata-observation",
                "operator_action": "rollback transcript draft and require fixture repair",
            },
            {
                "checkpoint": "schedule-mutation-requested",
                "operator_action": "abort dry-run and return schedule candidate to review queue",
            },
        ],
        "attestations": {
            "no_fetch": True,
            "no_processor": True,
            "no_download": True,
            "no_schedule_mutation": True,
            "metadata_only_observations": True,
        },
    }
