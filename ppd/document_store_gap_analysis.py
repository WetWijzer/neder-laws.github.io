"""Deterministic document-store gap analysis helpers for PP&D fixtures.

The functions in this module intentionally operate on plain dictionaries so they
can be used by daemon checks, tests, or future adapters without changing shared
contracts.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _doc_id(document: dict[str, Any]) -> str:
    return str(document.get("id") or document.get("document_id") or document.get("url") or "")


def _fact_key(fact: dict[str, Any]) -> str:
    return str(fact.get("key") or fact.get("id") or fact.get("name") or "")


def analyze_document_store_gap(packet: dict[str, Any], *, today: date | None = None) -> dict[str, Any]:
    """Return a deterministic gap-analysis packet for known facts and documents.

    Expected input keys are intentionally small:
    - known_facts: list of {key, value, required, document_ids, observed_at}
    - documents: list of {id, title, facts, status, observed_at, stale_after_days}
    - required_facts: list of required fact keys
    - required_documents: list of required document ids
    - blocked_actions: optional list of blocked action dictionaries
    """

    analysis_date = today or date.today()
    facts = [fact for fact in _as_list(packet.get("known_facts")) if isinstance(fact, dict)]
    documents = [doc for doc in _as_list(packet.get("documents")) if isinstance(doc, dict)]
    required_facts = {str(item) for item in _as_list(packet.get("required_facts")) if str(item)}
    required_documents = {str(item) for item in _as_list(packet.get("required_documents")) if str(item)}

    fact_keys = {_fact_key(fact) for fact in facts if _fact_key(fact)}
    document_ids = {_doc_id(document) for document in documents if _doc_id(document)}

    evidence_by_fact: dict[str, list[str]] = {}
    values_by_fact: dict[str, set[str]] = {}
    matched_documents: list[dict[str, Any]] = []
    stale_evidence: list[dict[str, Any]] = []

    for fact in facts:
        key = _fact_key(fact)
        if not key:
            continue
        values_by_fact.setdefault(key, set()).add(str(fact.get("value")))
        for document_id in _as_list(fact.get("document_ids")):
            document_id_text = str(document_id)
            if document_id_text:
                evidence_by_fact.setdefault(key, []).append(document_id_text)

    for document in documents:
        document_id = _doc_id(document)
        if not document_id:
            continue
        supported_facts = [str(item) for item in _as_list(document.get("facts")) if str(item)]
        if supported_facts:
            matched_documents.append(
                {
                    "document_id": document_id,
                    "title": str(document.get("title") or document_id),
                    "facts": sorted(supported_facts),
                }
            )
        observed_at = _parse_date(document.get("observed_at"))
        stale_after_days = document.get("stale_after_days")
        if observed_at is not None and isinstance(stale_after_days, int):
            age_days = (analysis_date - observed_at).days
            if age_days > stale_after_days:
                stale_evidence.append(
                    {
                        "document_id": document_id,
                        "observed_at": observed_at.isoformat(),
                        "age_days": age_days,
                        "stale_after_days": stale_after_days,
                    }
                )

    missing_facts = sorted(required_facts - fact_keys)
    missing_documents = sorted(required_documents - document_ids)
    conflicting_evidence = [
        {"fact": key, "values": sorted(values)}
        for key, values in sorted(values_by_fact.items())
        if len(values) > 1
    ]

    blocked_actions = [
        dict(action)
        for action in _as_list(packet.get("blocked_actions"))
        if isinstance(action, dict)
    ]

    review_packets = []
    if missing_facts or missing_documents or stale_evidence or conflicting_evidence or blocked_actions:
        review_packets.append(
            {
                "id": str(packet.get("packet_id") or "document-store-gap-review"),
                "known_fact_count": len(fact_keys),
                "matched_document_count": len(matched_documents),
                "missing_fact_count": len(missing_facts),
                "missing_document_count": len(missing_documents),
                "stale_evidence_count": len(stale_evidence),
                "conflicting_evidence_count": len(conflicting_evidence),
                "blocked_action_count": len(blocked_actions),
            }
        )

    return {
        "analysis_date": analysis_date.isoformat(),
        "known_facts": sorted(fact_keys),
        "matched_documents": sorted(matched_documents, key=lambda item: item["document_id"]),
        "missing_facts": missing_facts,
        "missing_documents": missing_documents,
        "stale_evidence": sorted(stale_evidence, key=lambda item: item["document_id"]),
        "conflicting_evidence": conflicting_evidence,
        "blocked_actions": blocked_actions,
        "review_packets": review_packets,
        "evidence_by_fact": {key: sorted(set(value)) for key, value in sorted(evidence_by_fact.items())},
    }
