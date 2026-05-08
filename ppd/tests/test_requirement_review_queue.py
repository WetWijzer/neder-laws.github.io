from pathlib import Path

from ppd.requirement_review_queue import build_review_queue, load_normalized_records


FIXTURE = Path(__file__).parent / "fixtures" / "requirement_review_queue" / "sample_normalized_pages.json"


def test_build_review_queue_extracts_stage_graph_and_guardrail_inputs():
    queue = build_review_queue(load_normalized_records(FIXTURE))

    assert len(queue) == 1
    item = queue[0]
    assert item["review_status"] == "pending_review"
    assert item["permit_family"] == "Residential Building Permit"
    assert item["stage_graph"]["nodes"] == [
        {"id": "stage_intake", "label": "Intake"},
        {"id": "stage_plan-review", "label": "Plan Review"},
        {"id": "stage_issuance", "label": "Issuance"},
    ]
    assert item["stage_graph"]["edges"] == [
        {"from": "stage_intake", "to": "stage_plan-review"},
        {"from": "stage_plan-review", "to": "stage_issuance"},
    ]
    assert item["document_rules"][0]["label"] == "Site plan required"
    assert item["document_rules"][0]["stage"] == "Intake"
    assert item["fee_triggers"][0]["label"] == "Plan review fee due"
    assert item["deadlines"][0]["days"] == "180"
    assert item["exceptions"][0]["label"] == "Historic resource review may add routing"
    assert item["source_evidence"]
    assert all(evidence["evidence_id"].startswith("ev_") for evidence in item["source_evidence"])


def test_build_review_queue_is_deterministic():
    records = load_normalized_records(FIXTURE)
    assert build_review_queue(records) == build_review_queue(records)
