from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ppd.document_store_gap_analysis import analyze_document_store_gap


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "document_store_gap_analysis" / "sample_packet.json"


def test_document_store_gap_analysis_covers_review_categories() -> None:
    packet = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    result = analyze_document_store_gap(packet, today=date(2026, 5, 8))

    assert result["known_facts"] == ["permit_number", "site_address"]
    assert result["matched_documents"] == [
        {
            "document_id": "permit-summary",
            "title": "Permit Summary",
            "facts": ["permit_number", "site_address"],
        },
        {
            "document_id": "zoning-map",
            "title": "Zoning Map Evidence",
            "facts": ["site_address"],
        },
    ]
    assert result["missing_facts"] == ["intake_status", "zoning_overlay"]
    assert result["missing_documents"] == ["intake-checklist"]
    assert result["stale_evidence"] == [
        {
            "document_id": "zoning-map",
            "observed_at": "2026-01-01",
            "age_days": 127,
            "stale_after_days": 30,
        }
    ]
    assert result["conflicting_evidence"] == [
        {
            "fact": "site_address",
            "values": ["1120 SW 5th Ave", "1120 SW Fifth Ave"],
        }
    ]
    assert result["blocked_actions"] == [
        {
            "action": "submit_application",
            "reason": "Requires authenticated user confirmation",
        }
    ]
    assert result["review_packets"] == [
        {
            "id": "fixture-gap-review",
            "known_fact_count": 2,
            "matched_document_count": 2,
            "missing_fact_count": 2,
            "missing_document_count": 1,
            "stale_evidence_count": 1,
            "conflicting_evidence_count": 1,
            "blocked_action_count": 1,
        }
    ]
    assert result["evidence_by_fact"] == {
        "permit_number": ["permit-summary"],
        "site_address": ["legacy-address-note", "permit-summary", "zoning-map"],
    }
