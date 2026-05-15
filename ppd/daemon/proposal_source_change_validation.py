"""Validation helpers for PP&D daemon task-board completion proposals."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ProposalSourceChangeFinding:
    """A deterministic validation finding for a proposed file replacement."""

    code: str
    message: str
    path: str | None = None


_TASK_BOARD_PATH_PARTS = {
    "task_board",
    "task-board",
    "tasks",
    "supervisor",
    "backlog",
}

_SOURCE_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
}


_COMPLETION_MARKERS = (
    "[x]",
    "[X]",
    "status: complete",
    "status: completed",
    "status=complete",
    "status=completed",
    "\"status\": \"complete\"",
    "\"status\": \"completed\"",
    "'status': 'complete'",
    "'status': 'completed'",
)


_BACKLOG_ONLY_MARKERS = (
    "plan_next_tasks",
    "next_tasks",
    "backlog",
)


def validate_task_board_completion_source_changes(
    proposal: Mapping[str, Any],
) -> list[ProposalSourceChangeFinding]:
    """Reject task-board completion proposals that contain no committed source change.

    The daemon receives proposed complete file replacements. This validator keeps the
    rule intentionally simple and deterministic: if a proposal visibly marks work
    complete in a task-board-like file, it must also include at least one committed
    application/domain source replacement outside task-board, docs-plan, and fixture
    files. Supervisor-only backlog planning updates remain allowed when they are
    confined to plan_next_tasks-style content and do not mark work complete.
    """

    files = _proposal_files(proposal)
    if not files:
        return []

    task_board_files = [file for file in files if _is_task_board_file(file[0])]
    if not task_board_files:
        return []

    marks_complete = any(_content_marks_work_complete(content) for _, content in task_board_files)
    if not marks_complete:
        return []

    if _is_supervisor_only_backlog_update(proposal, files):
        return [
            ProposalSourceChangeFinding(
                code="task_board_completion_in_plan_next_tasks",
                message="plan_next_tasks updates may add or reorder backlog work, but may not mark application/domain work complete.",
                path=task_board_files[0][0],
            )
        ]

    if _has_visible_committed_source_change(files):
        return []

    return [
        ProposalSourceChangeFinding(
            code="task_board_completion_without_source_change",
            message="Task-board completion proposals must include a visible committed application/domain source change.",
            path=task_board_files[0][0],
        )
    ]


def _proposal_files(proposal: Mapping[str, Any]) -> list[tuple[str, str]]:
    raw_files = proposal.get("files", [])
    if not isinstance(raw_files, Sequence) or isinstance(raw_files, (str, bytes)):
        return []

    files: list[tuple[str, str]] = []
    for raw_file in raw_files:
        if not isinstance(raw_file, Mapping):
            continue
        path = raw_file.get("path")
        content = raw_file.get("content")
        if isinstance(path, str) and isinstance(content, str):
            files.append((path, content))
    return files


def _is_task_board_file(path: str) -> bool:
    posix = PurePosixPath(path)
    lowered_parts = {part.lower() for part in posix.parts}
    lowered_name = posix.name.lower()
    if lowered_parts & _TASK_BOARD_PATH_PARTS:
        return True
    return "task" in lowered_name and "board" in lowered_name


def _content_marks_work_complete(content: str) -> bool:
    return any(marker in content for marker in _COMPLETION_MARKERS)


def _has_visible_committed_source_change(files: Iterable[tuple[str, str]]) -> bool:
    for path, content in files:
        if not content.strip():
            continue
        if not path.startswith("ppd/"):
            continue
        if _is_task_board_file(path):
            continue
        if _is_fixture_path(path):
            continue
        if _is_docs_plan_path(path):
            continue
        suffix = PurePosixPath(path).suffix.lower()
        if suffix in _SOURCE_SUFFIXES:
            return True
    return False


def _is_fixture_path(path: str) -> bool:
    return "/fixtures/" in path or path.startswith("ppd/tests/fixtures/")


def _is_docs_plan_path(path: str) -> bool:
    return path == "docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md"


def _is_supervisor_only_backlog_update(
    proposal: Mapping[str, Any], files: Sequence[tuple[str, str]]
) -> bool:
    if "plan_next_tasks" in proposal:
        return True

    summary = proposal.get("summary", "")
    impact = proposal.get("impact", "")
    text_fields = "\n".join(
        value for value in (summary, impact) if isinstance(value, str)
    )
    file_text = "\n".join(content for _, content in files)
    combined = f"{text_fields}\n{file_text}"
    return any(marker in combined for marker in _BACKLOG_ONLY_MARKERS)
