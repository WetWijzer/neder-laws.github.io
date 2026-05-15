from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from ppd.source_index_readiness import (
    SourceIndexReadinessError,
    require_source_index_ready,
    validate_source_index_readiness,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_index_readiness"
NOW = datetime(2026, 5, 15, tzinfo=timezone.utc)


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_ready_source_index_passes() -> None:
    index = _fixture("ready_source_index.json")

    result = validate_source_index_readiness(index, now=NOW)

    assert result.ready is True
    assert result.failures == ()
    require_source_index_ready(index, now=NOW)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda index: index.pop("freshness"), "missing freshness status"),
        (lambda index: index["freshness"].update({"status": "stale"}), "stale freshness status"),
        (lambda index: index["freshness"].update({"checked_at": "2026-03-01T00:00:00Z"}), "stale freshness timestamp"),
        (lambda index: index.pop("owning_surface"), "missing owning surface"),
        (lambda index: index["sources"][0].pop("citation_spans"), "missing citation spans for source 0"),
        (lambda index: index["sources"][0]["citation_spans"][0].update({"end": 0}), "invalid citation span for source 0 span 0"),
        (lambda index: index.pop("processor"), "missing processor metadata"),
        (lambda index: index["processor"].update({"version": ""}), "missing processor metadata"),
        (lambda index: index["processor"].update({"processed_at": "2026-03-01T00:00:00Z"}), "stale processor metadata"),
    ],
)
def test_unready_source_index_blocks_requirement_extraction(mutation, expected: str) -> None:
    index = copy.deepcopy(_fixture("ready_source_index.json"))
    mutation(index)

    result = validate_source_index_readiness(index, now=NOW)

    assert result.ready is False
    assert expected in result.failures
    with pytest.raises(SourceIndexReadinessError) as exc_info:
        require_source_index_ready(index, now=NOW)
    assert expected in exc_info.value.failures
