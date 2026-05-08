"""Build PP&D requirement-to-process review queue items.

This module is intentionally deterministic and fixture-friendly. It accepts normalized
page/form/PDF records and emits pending review queue items shaped for later guardrail
compilation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


_RULE_PREFIXES = {
    "DOCUMENT_RULE": "document_rules",
    "FEE_TRIGGER": "fee_triggers",
    "DEADLINE": "deadlines",
    "EXCEPTION": "exceptions",
}


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_id: str
    title: str
    url: str
    locator: str
    quote: str


@dataclass
class PermitFamilyDraft:
    permit_family: str
    stages: list[str] = field(default_factory=list)
    document_rules: list[dict[str, Any]] = field(default_factory=list)
    fee_triggers: list[dict[str, Any]] = field(default_factory=list)
    deadlines: list[dict[str, Any]] = field(default_factory=list)
    exceptions: list[dict[str, Any]] = field(default_factory=list)
    evidence: dict[str, Evidence] = field(default_factory=dict)


def load_normalized_records(path: str | Path) -> list[dict[str, Any]]:
    """Load normalized PP&D records from a JSON fixture or crawler artifact."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    records = payload.get("records") or payload.get("pages") or payload.get("documents") or []
    return [record for record in records if isinstance(record, dict)]


def build_review_queue(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert normalized source records into pending permit-family review items."""
    drafts: dict[str, PermitFamilyDraft] = {}

    for record in records:
        text = str(record.get("text") or "")
        if not text.strip():
            continue

        source_family = str(record.get("permit_family") or "").strip()
        current_family = source_family or "Unclassified PP&D Requirement"
        draft = drafts.setdefault(current_family, PermitFamilyDraft(current_family))

        for line_number, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue

            key, value = _split_marker(line)
            if key == "PERMIT_FAMILY" and value:
                current_family = value
                draft = drafts.setdefault(current_family, PermitFamilyDraft(current_family))
                continue

            if key == "STAGE" and value:
                for stage in _split_stages(value):
                    if stage not in draft.stages:
                        draft.stages.append(stage)
                continue

            target = _RULE_PREFIXES.get(key)
            if target and value:
                evidence = _make_evidence(record, line_number, line)
                draft.evidence[evidence.evidence_id] = evidence
                getattr(draft, target).append(_parse_rule_value(value, evidence.evidence_id))

    return [_draft_to_queue_item(draft) for draft in sorted(drafts.values(), key=lambda item: item.permit_family)]


def _split_marker(line: str) -> tuple[str, str]:
    if ":" not in line:
        return "", ""
    key, value = line.split(":", 1)
    return key.strip().upper().replace(" ", "_"), value.strip()


def _split_stages(value: str) -> list[str]:
    return [part.strip() for part in value.replace("->", ">").split(">") if part.strip()]


def _parse_rule_value(value: str, evidence_id: str) -> dict[str, Any]:
    parts = [part.strip() for part in value.split("|") if part.strip()]
    rule: dict[str, Any] = {"label": parts[0] if parts else value, "evidence_ids": [evidence_id]}
    for part in parts[1:]:
        if "=" in part:
            key, raw = part.split("=", 1)
            rule[key.strip()] = raw.strip()
        else:
            rule.setdefault("qualifiers", []).append(part)
    return rule


def _make_evidence(record: dict[str, Any], line_number: int, quote: str) -> Evidence:
    source_id = str(record.get("source_id") or record.get("id") or record.get("url") or "unknown-source")
    title = str(record.get("title") or "Untitled PP&D source")
    url = str(record.get("url") or "")
    locator = f"line:{line_number}"
    digest = hashlib.sha256(f"{source_id}\n{locator}\n{quote}".encode("utf-8")).hexdigest()[:16]
    return Evidence(
        evidence_id=f"ev_{digest}",
        source_id=source_id,
        title=title,
        url=url,
        locator=locator,
        quote=quote,
    )


def _draft_to_queue_item(draft: PermitFamilyDraft) -> dict[str, Any]:
    stages = draft.stages or ["Requirement Review"]
    return {
        "review_status": "pending_review",
        "permit_family": draft.permit_family,
        "stage_graph": {
            "nodes": [{"id": _stage_id(stage), "label": stage} for stage in stages],
            "edges": [
                {"from": _stage_id(stages[index]), "to": _stage_id(stages[index + 1])}
                for index in range(len(stages) - 1)
            ],
        },
        "document_rules": draft.document_rules,
        "fee_triggers": draft.fee_triggers,
        "deadlines": draft.deadlines,
        "exceptions": draft.exceptions,
        "source_evidence": [evidence.__dict__ for evidence in sorted(draft.evidence.values(), key=lambda item: item.evidence_id)],
    }


def _stage_id(stage: str) -> str:
    normalized = "".join(character.lower() if character.isalnum() else "-" for character in stage)
    return "stage_" + "-".join(part for part in normalized.split("-") if part)
