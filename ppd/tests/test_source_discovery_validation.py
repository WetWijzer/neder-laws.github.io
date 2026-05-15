import json
from pathlib import Path

from ppd.crawler.source_discovery_validation import validate_discovery_records


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_discovery_validation" / "records.json"


def test_source_discovery_records_match_expected_policy_decisions() -> None:
    records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    findings = validate_discovery_records(records)

    by_id = {finding.record_id: finding for finding in findings}
    assert set(by_id) == {record["record_id"] for record in records}
    for record in records:
        finding = by_id[record["record_id"]]
        assert finding.decision == record["expected_decision"]
        assert finding.reason_code == record["expected_reason_code"]


def test_source_discovery_findings_are_serializable() -> None:
    records = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    serialized = [finding.as_dict() for finding in validate_discovery_records(records)]

    assert serialized[0] == {
        "record_id": "ppd-landing",
        "url": "https://www.portland.gov/ppd",
        "decision": "allow",
        "reason_code": "allowed_public_source",
        "message": "Discovery URL is within the deterministic PP&D public source policy.",
    }
