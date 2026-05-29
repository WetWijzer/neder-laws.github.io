"""Validation for regenerated PP&D agent regression matrices.

The validator is intentionally schema-tolerant because generated matrices may be
represented as rows, cases, scenarios, or tests while the guardrail expectations
are stabilized. It rejects unsafe claims and missing evidence before a matrix can
be promoted into committed regression coverage.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath
import json
import re
from typing import Any, Iterable, Mapping, Sequence


_CURRENT_SOURCE_MAX_AGE_DAYS = 45
_CONSEQUENTIAL_WORDS = {
    "submit",
    "submission",
    "certify",
    "certification",
    "upload",
    "attach",
    "schedule",
    "cancel",
    "withdraw",
    "payment",
    "pay",
    "purchase",
    "finalize",
    "official",
    "reactivate",
    "extension",
}
_MANUAL_HANDOFF_WORDS = {
    "manual_handoff",
    "manual handoff",
    "human_handoff",
    "human handoff",
    "requires_attendance",
    "attended",
    "user_present",
}
_BLOCK_WORDS = {"blocked", "refused", "deny", "denied", "stop", "manual_handoff"}
_ALLOW_WORDS = {"allowed", "allow", "draft", "autonomous", "execute", "executed", "complete", "completed"}
_LIVE_LLM_KEYS = {
    "use_live_llm",
    "live_llm",
    "execute_live_llm",
    "run_live_llm",
    "llm_execution",
    "invoke_llm",
    "call_llm",
}
_PRIVATE_KEY_PARTS = {
    "password",
    "passwd",
    "secret",
    "token",
    "cookie",
    "credential",
    "auth_state",
    "session_state",
    "payment_detail",
    "card_number",
    "ssn",
}
_LOCAL_PATH_PATTERNS = (
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"(?:^|[\s'\"])/Users/[A-Za-z0-9._-]+/"),
    re.compile(r"(?:^|[\s'\"])/home/[A-Za-z0-9._-]+/"),
    re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\s]+", re.IGNORECASE),
)
_PRIVATE_VALUE_PATTERNS = (
    re.compile(r"PRIVATE[_ -]?VALUE", re.IGNORECASE),
    re.compile(r"BEGIN (?:RSA |OPENSSH |PRIVATE )?PRIVATE KEY", re.IGNORECASE),
    re.compile(r"(?:password|secret|token|cookie)\s*[:=]\s*[^\s,;]+", re.IGNORECASE),
)


@dataclass(frozen=True)
class MatrixValidationIssue:
    """A deterministic matrix validation failure."""

    code: str
    path: str
    message: str


class MatrixValidationError(ValueError):
    """Raised when a regenerated regression matrix violates PP&D policy."""

    def __init__(self, issues: Sequence[MatrixValidationIssue]) -> None:
        self.issues = tuple(issues)
        details = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        super().__init__(details)


def validate_agent_regression_matrix(matrix: Mapping[str, Any]) -> None:
    """Validate a regenerated PP&D agent regression matrix.

    Raises:
        MatrixValidationError: if the matrix contains uncited outcomes, private
            values, stale current sources, unsafe action downgrades, live LLM
            execution flags, unsupported DevHub claims, or enabled consequential
            controls.
    """

    issues = collect_agent_regression_matrix_issues(matrix)
    if issues:
        raise MatrixValidationError(issues)


def collect_agent_regression_matrix_issues(matrix: Mapping[str, Any]) -> list[MatrixValidationIssue]:
    """Return all deterministic validation issues for a matrix."""

    issues: list[MatrixValidationIssue] = []
    generated_at = _parse_datetime(_first_present(matrix, ("generated_at", "matrix_generated_at", "created_at")))

    for path, key, value in _walk(matrix):
        key_text = str(key).lower() if key is not None else ""
        value_text = _compact_text(value)

        if key_text in _LIVE_LLM_KEYS and _truthy(value):
            issues.append(MatrixValidationIssue("live_llm_execution_flag", path, "live LLM execution must be disabled in committed regression matrices"))

        if any(part in key_text for part in _PRIVATE_KEY_PARTS) and value not in (None, "", False):
            issues.append(MatrixValidationIssue("private_value", path, "private values and authentication material are not allowed in committed matrices"))

        if isinstance(value, str):
            if any(pattern.search(value) for pattern in _LOCAL_PATH_PATTERNS):
                issues.append(MatrixValidationIssue("local_private_path", path, "local private file paths are not allowed in committed matrices"))
            if any(pattern.search(value) for pattern in _PRIVATE_VALUE_PATTERNS):
                issues.append(MatrixValidationIssue("private_value", path, "private values are not allowed in committed matrices"))

    for case_path, case in _iter_cases(matrix):
        expected = _expected_payload(case)
        expected_path = f"{case_path}.expected" if expected is not None else case_path
        if expected is not None and _has_expected_content(expected) and not _has_citation(case, expected):
            issues.append(MatrixValidationIssue("uncited_expected_outcome", expected_path, "expected outcomes must cite source evidence"))

        action_text = _action_text(case)
        expected_text = _compact_text(expected if expected is not None else case)
        if _is_consequential(case, action_text) and _is_downgraded_to_allowed(expected_text):
            issues.append(MatrixValidationIssue("blocked_action_downgrade", expected_path, "consequential or financial actions must remain blocked or handoff-gated"))

        if _requires_manual_handoff(case, action_text) and not _mentions_any(expected_text, _MANUAL_HANDOFF_WORDS):
            issues.append(MatrixValidationIssue("missing_manual_handoff_expectation", expected_path, "blocked DevHub or unsupported actions must expect manual handoff"))

        if _claims_devhub_automation(case, action_text, expected_text):
            issues.append(MatrixValidationIssue("devhub_automation_claim", expected_path, "committed matrices must not claim autonomous DevHub consequential execution"))

    for source_path, source in _iter_sources(matrix):
        freshness = str(_first_present(source, ("freshness_status", "status", "freshness")) or "").lower()
        if freshness == "current" and _source_is_stale(source, generated_at):
            issues.append(MatrixValidationIssue("stale_source_marked_current", source_path, "stale or superseded source evidence cannot be marked current"))

    for control_path, control in _iter_controls(matrix):
        if _control_is_enabled_consequential(control):
            issues.append(MatrixValidationIssue("enabled_consequential_control", control_path, "consequential, financial, or official controls must not be enabled in regression expectations"))

    return issues


def load_and_validate_agent_regression_matrix(path: str) -> Mapping[str, Any]:
    """Load a JSON matrix file and validate it."""

    with open(path, "r", encoding="utf-8") as handle:
        matrix = json.load(handle)
    if not isinstance(matrix, Mapping):
        raise MatrixValidationError([MatrixValidationIssue("invalid_matrix", "$", "matrix root must be a JSON object")])
    validate_agent_regression_matrix(matrix)
    return matrix


def _iter_cases(matrix: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    for key in ("cases", "rows", "scenarios", "tests", "regressions"):
        value = matrix.get(key)
        if isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, Mapping):
                    yield f"$.{key}[{index}]", item
    if any(key in matrix for key in ("expected", "expected_outcome", "expected_outcomes", "outcome")):
        yield "$", matrix


def _iter_sources(matrix: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    for key in ("sources", "source_registry", "source_evidence", "evidence"):
        value = matrix.get(key)
        if isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, Mapping):
                    yield f"$.{key}[{index}]", item
        elif isinstance(value, Mapping):
            for source_key, item in value.items():
                if isinstance(item, Mapping):
                    yield f"$.{key}.{source_key}", item


def _iter_controls(matrix: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    for path, key, value in _walk(matrix):
        if str(key).lower() in {"control", "controls", "ui_controls", "actions"}:
            if isinstance(value, list):
                for index, item in enumerate(value):
                    if isinstance(item, Mapping):
                        yield f"{path}[{index}]", item
            elif isinstance(value, Mapping):
                yield path, value


def _walk(value: Any, path: str = "$", key: object | None = None) -> Iterable[tuple[str, object | None, Any]]:
    yield path, key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            yield from _walk(child_value, f"{path}.{child_key}", child_key)
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{path}[{index}]", index)


def _expected_payload(case: Mapping[str, Any]) -> Any:
    return _first_present(case, ("expected_outcome", "expected_outcomes", "expected", "outcome", "then", "assertions"))


def _has_expected_content(expected: Any) -> bool:
    return expected not in (None, "", [], {})


def _has_citation(case: Mapping[str, Any], expected: Any) -> bool:
    citation_keys = ("citation", "citations", "source_evidence_id", "source_evidence_ids", "source_ids", "evidence", "evidence_ids", "sources")
    for container in (expected, case):
        if isinstance(container, Mapping):
            for key in citation_keys:
                value = container.get(key)
                if isinstance(value, str) and value.strip():
                    return True
                if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) > 0:
                    return True
    return False


def _action_text(case: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for key in ("action", "action_name", "requested_action", "user_request", "workflow", "surface", "classification", "action_policy"):
        value = case.get(key)
        if value is not None:
            parts.append(_compact_text(value))
    return " ".join(parts).lower()


def _is_consequential(case: Mapping[str, Any], action_text: str) -> bool:
    classification = _compact_text(_first_present(case, ("classification", "action_class", "action_policy", "risk"))).lower()
    if any(word in classification for word in ("consequential", "financial", "official")):
        return True
    return _mentions_any(action_text, _CONSEQUENTIAL_WORDS)


def _is_downgraded_to_allowed(expected_text: str) -> bool:
    lowered = expected_text.lower()
    return _mentions_any(lowered, _ALLOW_WORDS) and not _mentions_any(lowered, _BLOCK_WORDS)


def _requires_manual_handoff(case: Mapping[str, Any], action_text: str) -> bool:
    unsupported = _compact_text(_first_present(case, ("unsupported", "requires_attendance", "requires_manual_handoff"))).lower()
    if any(word in unsupported for word in ("true", "manual", "attended", "unsupported")):
        return True
    return _mentions_any(action_text, {"mfa", "captcha", "account creation", "password recovery", "payment", "submit", "upload", "schedule", "certify", "cancel"})


def _claims_devhub_automation(case: Mapping[str, Any], action_text: str, expected_text: str) -> bool:
    combined = f"{action_text} {expected_text} {_compact_text(case)}".lower()
    if "devhub" not in combined:
        return False
    if not _mentions_any(combined, _CONSEQUENTIAL_WORDS):
        return False
    return _mentions_any(combined, {"completed", "executed", "automated", "submitted", "uploaded", "scheduled", "paid", "purchased"})


def _source_is_stale(source: Mapping[str, Any], generated_at: datetime | None) -> bool:
    explicit_stale = _first_present(source, ("stale", "is_stale", "superseded", "superseded_by", "stale_as_of"))
    if explicit_stale not in (None, "", False, [], {}):
        return True
    reference_time = generated_at or datetime.now(timezone.utc)
    seen_at = _parse_datetime(_first_present(source, ("last_seen_at", "last_verified_at", "verified_at", "captured_at")))
    if seen_at is None:
        return False
    return (reference_time - seen_at).days > _CURRENT_SOURCE_MAX_AGE_DAYS


def _control_is_enabled_consequential(control: Mapping[str, Any]) -> bool:
    if not _truthy(_first_present(control, ("enabled", "is_enabled", "active"))):
        return False
    text = _compact_text(control).lower()
    return _mentions_any(text, _CONSEQUENTIAL_WORDS) or _mentions_any(text, {"consequential", "financial", "official"})


def _first_present(mapping: Mapping[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "enabled", "on"}
    return bool(value)


def _compact_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return " ".join(f"{key} {_compact_text(child)}" for key, child in value.items())
    if isinstance(value, list):
        return " ".join(_compact_text(child) for child in value)
    return str(value)


def _mentions_any(text: str, words: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in words)


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def public_path_name(path: str) -> str:
    """Return a stable public basename without exposing private path parents."""

    if "\\" in path:
        return PureWindowsPath(path).name
    return PurePosixPath(path).name
