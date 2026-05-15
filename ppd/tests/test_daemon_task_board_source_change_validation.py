"""Regression tests for daemon task-board completion source-change validation."""

from __future__ import annotations

import json
from pathlib import Path

from ppd.daemon.proposal_source_change_validation import (
    validate_task_board_completion_source_changes,
)


_FIXTURES = Path(__file__).parent / "fixtures" / "daemon_validation"


def _fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_rejects_task_board_completion_without_visible_source_change() -> None:
    findings = validate_task_board_completion_source_changes(
        _fixture("task_board_completion_without_source_change.json")
    )

    assert [finding.code for finding in findings] == [
        "task_board_completion_without_source_change"
    ]


def test_allows_task_board_completion_with_visible_source_change() -> None:
    findings = validate_task_board_completion_source_changes(
        _fixture("task_board_completion_with_source_change.json")
    )

    assert findings == []


def test_allows_supervisor_only_plan_next_tasks_backlog_update() -> None:
    findings = validate_task_board_completion_source_changes(
        _fixture("plan_next_tasks_backlog_update.json")
    )

    assert findings == []


def test_rejects_plan_next_tasks_when_it_marks_work_complete() -> None:
    findings = validate_task_board_completion_source_changes(
        _fixture("plan_next_tasks_completion_update.json")
    )

    assert [finding.code for finding in findings] == [
        "task_board_completion_in_plan_next_tasks"
    ]
