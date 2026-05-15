from pathlib import Path

import pytest

from ppd.devhub.dry_run_transcript import (
    DryRunTranscriptError,
    validate_transcript,
    validate_transcript_file,
)


FIXTURES = Path(__file__).parent / "fixtures" / "devhub_dry_run"


def test_valid_attended_dry_run_transcript_passes() -> None:
    result = validate_transcript_file(FIXTURES / "valid_attended_transcript.json")

    assert result.event_count == 2
    assert result.surfaces == ("devhub_authenticated_home", "devhub_public")
    assert result.warnings == ("no artifacts recorded",)


def test_rejects_browser_actions() -> None:
    with pytest.raises(DryRunTranscriptError, match="forbidden browser or consequential event"):
        validate_transcript_file(FIXTURES / "invalid_browser_action_transcript.json")


def test_rejects_screenshots_and_persisted_artifacts() -> None:
    with pytest.raises(DryRunTranscriptError, match="forbidden artifact kind"):
        validate_transcript_file(FIXTURES / "invalid_artifact_transcript.json")


def test_rejects_saved_auth_state_even_without_path() -> None:
    transcript = {
        "transcript_version": "devhub-attended-dry-run-v1",
        "session_mode": "attended_dry_run",
        "created_at": "2026-05-14T00:00:00Z",
        "browser_launched": False,
        "auth_state_saved": True,
        "artifacts": [],
        "events": [
            {
                "event_type": "attended_preflight_check",
                "performed_by": "validator",
                "surface": "devhub_authenticated_home",
                "requires_attendance": True,
                "browser_action": False,
                "description": "No browser is launched by the validator.",
            }
        ],
    }

    with pytest.raises(DryRunTranscriptError, match="auth_state_saved must be false"):
        validate_transcript(transcript)


def test_rejects_private_fields_anywhere_in_transcript() -> None:
    transcript = {
        "transcript_version": "devhub-attended-dry-run-v1",
        "session_mode": "attended_dry_run",
        "created_at": "2026-05-14T00:00:00Z",
        "browser_launched": False,
        "auth_state_saved": False,
        "artifacts": [],
        "events": [
            {
                "event_type": "attended_preflight_check",
                "performed_by": "validator",
                "surface": "devhub_authenticated_home",
                "requires_attendance": True,
                "browser_action": False,
                "description": "A private field nested below should make this invalid.",
                "credentials": {"username": "redacted"},
            }
        ],
    }

    with pytest.raises(DryRunTranscriptError, match="forbidden private field"):
        validate_transcript(transcript)


def test_rejects_playwright_launch_markers() -> None:
    transcript = {
        "transcript_version": "devhub-attended-dry-run-v1",
        "session_mode": "attended_dry_run",
        "created_at": "2026-05-14T00:00:00Z",
        "browser_launched": True,
        "auth_state_saved": False,
        "artifacts": [],
        "events": [
            {
                "event_type": "attended_preflight_check",
                "performed_by": "validator",
                "surface": "devhub_public",
                "requires_attendance": True,
                "browser_action": False,
                "description": "A dry-run validator must not launch Playwright."
            }
        ],
    }

    with pytest.raises(DryRunTranscriptError, match="browser_launched must be false"):
        validate_transcript(transcript)
