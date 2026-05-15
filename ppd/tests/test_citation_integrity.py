from pathlib import Path

import pytest

from ppd.citations.citation_integrity import validate_citation_integrity_files

FIXTURES = Path(__file__).parent / "fixtures" / "citation_integrity"


def _failure_codes(citations_name):
    failures = validate_citation_integrity_files(
        FIXTURES / "source_registry.json",
        FIXTURES / "document_records.json",
        FIXTURES / citations_name,
    )
    return {failure.code for failure in failures}


def test_valid_committed_public_citation_fixture_has_no_failures():
    failures = validate_citation_integrity_files(
        FIXTURES / "source_registry.json",
        FIXTURES / "document_records.json",
        FIXTURES / "valid_citations.json",
    )
    assert failures == []


@pytest.mark.parametrize(
    ("fixture_name", "expected_code"),
    [
        ("missing_span_citations.json", "missing_span"),
        ("stale_source_citations.json", "stale_source_id"),
        ("private_authenticated_citations.json", "private_authenticated_evidence"),
    ],
)
def test_invalid_citation_fixtures_fail_with_explicit_codes(fixture_name, expected_code):
    assert expected_code in _failure_codes(fixture_name)
