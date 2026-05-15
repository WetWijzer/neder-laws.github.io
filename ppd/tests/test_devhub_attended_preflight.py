from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.devhub.attended_preflight import (
    load_attended_preflight_fixture,
    validate_attended_preflight_fixture,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "attended_preflight_valid.json"


def _valid_fixture() -> dict:
    return load_attended_preflight_fixture(FIXTURE_PATH)


def test_fixture_only_attended_preflight_passes_without_browser_launch() -> None:
    result = validate_attended_preflight_fixture(_valid_fixture())

    assert result.preflight_passed is True
    assert result.browser_action_plan_allowed is True
    assert result.browser_launch_allowed is False
    assert result.issues == ()
    assert "devhub.dashboard.permit_requests" in result.matched_surfaces
    assert "devhub.application.review_checkpoint" in result.matched_surfaces


def test_manual_login_handoff_is_required_before_plan_is_allowed() -> None:
    fixture = _valid_fixture()
    fixture["manual_login_handoff"] = {
        "required": False,
        "requires_user_attendance": False,
        "actor": "automation",
        "credential_storage": "allowed",
        "session_state_storage": "allowed",
        "account_creation_allowed": True,
    }

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("manual login handoff" in issue for issue in result.issues)
    assert any("credential storage" in issue for issue in result.issues)
    assert any("account creation" in issue for issue in result.issues)


def test_mfa_captcha_and_account_creation_refusals_are_mandatory() -> None:
    fixture = _valid_fixture()
    fixture["refused_action_policies"] = {
        "mfa": {
            "decision": "handoff",
            "automate": True,
            "requires_user_handoff": False,
        }
    }

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("mfa policy must refuse automation" in issue for issue in result.issues)
    assert any("captcha policy must refuse automation" in issue for issue in result.issues)
    assert any("account_creation policy must refuse automation" in issue for issue in result.issues)


def test_surface_map_matching_is_required_for_planned_actions() -> None:
    fixture = _valid_fixture()
    fixture["candidate_browser_action_plan"]["actions"][0]["surface_id"] = "devhub.unknown.surface"

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("must match a known surface" in issue for issue in result.issues)


def test_selector_confidence_thresholds_block_low_confidence_surfaces_and_actions() -> None:
    fixture = _valid_fixture()
    fixture["surface_map"][0]["selector_confidence"] = 0.84
    fixture["candidate_browser_action_plan"][1]["selector_confidence"] = 0.8

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("surface 'devhub.dashboard.permit_requests' selector confidence below threshold" in issue for issue in result.issues)
    assert any("planned action 'fixture-review-continue-button' selector confidence below threshold" in issue for issue in result.issues)


def test_exact_confirmation_checkpoint_must_exist_before_action_plan() -> None:
    fixture = _valid_fixture()
    fixture["exact_confirmation_checkpoints"] = []

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert any("at least one exact confirmation checkpoint is required" in issue for issue in result.issues)
    assert any("must reference an exact confirmation checkpoint" in issue for issue in result.issues)


def test_browser_launch_remains_blocked_even_if_fixture_requests_it() -> None:
    fixture = deepcopy(_valid_fixture())
    fixture["candidate_browser_action_plan"]["browser_launch_allowed"] = True

    result = validate_attended_preflight_fixture(fixture)

    assert result.preflight_passed is False
    assert result.browser_action_plan_allowed is False
    assert result.browser_launch_allowed is False
    assert any("must not allow browser launch" in issue for issue in result.issues)
