"""Deterministic guardrails for previewing DevHub action plans.

This module is intentionally fixture-friendly and side-effect free. It does not
control a browser, persist session state, or inspect private DevHub data. It only
classifies a proposed action plan before any executor is allowed to run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

REVERSIBLE_DRAFT_ACTIONS = frozenset({"reversible_draft_fill", "save_draft"})
FAIL_CLOSED_ACTIONS = frozenset(
    {
        "official_upload",
        "certification",
        "submission",
        "payment",
        "cancellation",
        "inspection_scheduling",
        "mfa",
        "captcha",
        "account_creation",
    }
)
MIN_SELECTOR_CONFIDENCE = 0.85


@dataclass(frozen=True)
class ActionPreviewDecision:
    """Result of a guarded action preview evaluation."""

    allowed: bool
    action_type: str
    status: str
    reasons: tuple[str, ...]
    required: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action_type": self.action_type,
            "status": self.status,
            "reasons": list(self.reasons),
            "required": list(self.required),
        }


def evaluate_guarded_action_preview(action_plan: Mapping[str, Any]) -> ActionPreviewDecision:
    """Evaluate whether a proposed DevHub action may proceed to preview.

    Reversible draft work may proceed only when the plan is grounded in source
    evidence, user case facts, selector confidence, user attendance, and a
    concrete preview. Consequential official actions always fail closed.
    """

    action_type = _string_value(action_plan.get("action_type"))
    if action_type in FAIL_CLOSED_ACTIONS:
        return ActionPreviewDecision(
            allowed=False,
            action_type=action_type,
            status="refused_fail_closed",
            reasons=(f"{action_type} is an official or account-security action",),
            required=("manual_user_handoff", "action_specific_confirmation"),
        )

    if action_type not in REVERSIBLE_DRAFT_ACTIONS:
        normalized = action_type or "unknown"
        return ActionPreviewDecision(
            allowed=False,
            action_type=normalized,
            status="refused_unknown_action",
            reasons=("action_type is not an approved reversible draft action",),
            required=("supported_action_type",),
        )

    missing = _missing_reversible_requirements(action_plan)
    if missing:
        return ActionPreviewDecision(
            allowed=False,
            action_type=action_type,
            status="blocked_missing_guardrails",
            reasons=tuple(f"missing or invalid {name}" for name in missing),
            required=tuple(missing),
        )

    return ActionPreviewDecision(
        allowed=True,
        action_type=action_type,
        status="preview_ready",
        reasons=(),
        required=(
            "source_evidence",
            "user_case_facts",
            "selector_confidence",
            "attendance",
            "preview",
        ),
    )


def _missing_reversible_requirements(action_plan: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []

    if not _has_source_evidence(action_plan.get("source_evidence")):
        missing.append("source_evidence")
    if not _has_user_case_facts(action_plan.get("user_case_facts")):
        missing.append("user_case_facts")
    if not _has_selector_confidence(action_plan.get("selector_confidence")):
        missing.append("selector_confidence")
    if action_plan.get("attendance") is not True:
        missing.append("attendance")
    if not _has_preview(action_plan.get("preview")):
        missing.append("preview")

    return missing


def _has_source_evidence(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    if not value:
        return False
    for item in value:
        if not isinstance(item, Mapping):
            return False
        if not _string_value(item.get("source_id")):
            return False
        if not _string_value(item.get("citation")):
            return False
    return True


def _has_user_case_facts(value: Any) -> bool:
    if not isinstance(value, Mapping) or not value:
        return False
    return all(_string_value(key) and item not in (None, "") for key, item in value.items())


def _has_selector_confidence(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return float(value) >= MIN_SELECTOR_CONFIDENCE


def _has_preview(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    fields = value.get("fields")
    if not isinstance(fields, Sequence) or isinstance(fields, (str, bytes)):
        return False
    if not fields:
        return False
    for field in fields:
        if not isinstance(field, Mapping):
            return False
        if not _string_value(field.get("selector")):
            return False
        if "proposed_value" not in field:
            return False
    return True


def _string_value(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


__all__ = [
    "ActionPreviewDecision",
    "FAIL_CLOSED_ACTIONS",
    "MIN_SELECTOR_CONFIDENCE",
    "REVERSIBLE_DRAFT_ACTIONS",
    "evaluate_guarded_action_preview",
]
