from pathlib import Path

from ppd.logic.requirement_review_queue import (
    HUMAN_REVIEW_REQUIRED,
    LOW_CONFIDENCE,
    MISSING_FORMALIZATION,
    OCR_DERIVED_EVIDENCE,
    STALE_SOURCE,
    load_requirement_nodes,
    partition_requirements_for_guardrails,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_review_queue"
    / "requirement_nodes.json"
)


def test_requirement_review_queue_groups_promotion_blockers_deterministically() -> None:
    nodes = load_requirement_nodes(FIXTURE_PATH)

    partition = partition_requirements_for_guardrails(
        nodes,
        confidence_threshold=0.75,
        stale_source_ids={"SRC-STALE-FEE-GUIDE"},
    )

    review_queue = partition["review_queue"]
    assert [item["requirement_id"] for item in review_queue] == [
        "REQ-001-LOW-CONFIDENCE",
        "REQ-002-OCR-STALE",
        "REQ-003-MISSING-FORMALIZATION",
        "REQ-004-HUMAN-REVIEW",
    ]
    assert review_queue == [
        {
            "requirement_id": "REQ-001-LOW-CONFIDENCE",
            "blocker_codes": [LOW_CONFIDENCE],
            "source_evidence_ids": ["EV-001"],
            "subject": "applicant",
            "action": "prepare",
            "object": "single PDF drawing plan set",
        },
        {
            "requirement_id": "REQ-002-OCR-STALE",
            "blocker_codes": [OCR_DERIVED_EVIDENCE, STALE_SOURCE],
            "source_evidence_ids": ["EV-002"],
            "subject": "applicant",
            "action": "upload",
            "object": "supporting calculation PDF",
        },
        {
            "requirement_id": "REQ-003-MISSING-FORMALIZATION",
            "blocker_codes": [MISSING_FORMALIZATION],
            "source_evidence_ids": ["EV-003"],
            "subject": "applicant",
            "action": "pay",
            "object": "permit fees",
        },
        {
            "requirement_id": "REQ-004-HUMAN-REVIEW",
            "blocker_codes": [HUMAN_REVIEW_REQUIRED],
            "source_evidence_ids": ["EV-004"],
            "subject": "applicant",
            "action": "certify",
            "object": "permit application acknowledgement",
        },
    ]

    promotable_ids = [
        node["requirement_id"] for node in partition["promotable_requirement_nodes"]
    ]
    assert promotable_ids == ["REQ-005-PROMOTABLE"]
