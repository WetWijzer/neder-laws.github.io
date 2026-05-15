from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from ppd.devhub.guarded_action_preview import evaluate_guarded_action_preview

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub_guarded_action_preview.json"


def load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_reversible_draft_fill_preview_is_allowed_with_all_guardrails() -> None:
    fixture = load_fixture()

    decision = evaluate_guarded_action_preview(fixture["reversible_draft_fill"])

    assert decision.allowed is True
    assert decision.status == "preview_ready"
    assert decision.action_type == "reversible_draft_fill"
    assert decision.reasons == ()


def test_save_draft_preview_is_allowed_with_all_guardrails() -> None:
    fixture = load_fixture()

    decision = evaluate_guarded_action_preview(fixture["save_draft"])

    assert decision.allowed is True
    assert decision.status == "preview_ready"
    assert decision.action_type == "save_draft"
    assert decision.reasons == ()


def test_reversible_draft_fill_requires_source_evidence_user_facts_confidence_attendance_and_preview() -> None:
    fixture = load_fixture()
    base_plan = fixture["reversible_draft_fill"]
    invalid_values = {
        "source_evidence": [],
        "user_case_facts": {},
        "selector_confidence": 0.4,
        "attendance": False,
        "preview": {"fields": []},
    }

    for required_name, invalid_value in invalid_values.items():
        plan = deepcopy(base_plan)
        plan[required_name] = invalid_value

        decision = evaluate_guarded_action_preview(plan)

        assert decision.allowed is False
        assert decision.status == "blocked_missing_guardrails"
        assert required_name in decision.required


def test_save_draft_requires_source_evidence_user_facts_confidence_attendance_and_preview() -> None:
    fixture = load_fixture()
    base_plan = fixture["save_draft"]
    invalid_values = {
        "source_evidence": [],
        "user_case_facts": {},
        "selector_confidence": True,
        "attendance": False,
        "preview": None,
    }

    for required_name, invalid_value in invalid_values.items():
        plan = deepcopy(base_plan)
        plan[required_name] = invalid_value

        decision = evaluate_guarded_action_preview(plan)

        assert decision.allowed is False
        assert decision.status == "blocked_missing_guardrails"
        assert required_name in decision.required


def test_official_and_account_security_actions_fail_closed() -> None:
    fixture = load_fixture()
    reversible_plan = fixture["reversible_draft_fill"]

    for action_type in fixture["fail_closed_action_types"]:
        plan = deepcopy(reversible_plan)
        plan["action_type"] = action_type

        decision = evaluate_guarded_action_preview(plan)

        assert decision.allowed is False
        assert decision.status == "refused_fail_closed"
        assert decision.action_type == action_type
        assert "manual_user_handoff" in decision.required
        assert "action_specific_confirmation" in decision.required


def test_unknown_action_type_is_refused() -> None:
    decision = evaluate_guarded_action_preview({"action_type": "delete_permit_record"})

    assert decision.allowed is False
    assert decision.status == "refused_unknown_action"
    assert decision.required == ("supported_action_type",)
