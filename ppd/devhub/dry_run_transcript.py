"""Deterministic validator for attended DevHub dry-run transcripts.

The validator is intentionally side-effect free. It only accepts already-created
JSON transcript data and rejects records that imply browser automation, persisted
authentication state, screenshots, traces, HAR files, credentials, or private
session artifacts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


class DryRunTranscriptError(ValueError):
    """Raised when a DevHub dry-run transcript violates the safe contract."""


@dataclass(frozen=True)
class DryRunValidationResult:
    """Validated transcript summary safe to include in deterministic tests."""

    event_count: int
    surfaces: tuple[str, ...]
    warnings: tuple[str, ...] = ()


FORBIDDEN_ARTIFACT_KINDS = {
    "auth_state",
    "browser_context",
    "cookie_jar",
    "download",
    "har",
    "raw_crawl_output",
    "screenshot",
    "session_file",
    "storage_state",
    "trace",
    "video",
}

FORBIDDEN_EVENT_TYPES = {
    "browser_action",
    "browser_launch",
    "captcha",
    "certify",
    "click",
    "download",
    "fill",
    "launch_playwright",
    "mfa",
    "payment",
    "press",
    "save_auth_state",
    "schedule_inspection",
    "screenshot",
    "select_option",
    "submit",
    "trace",
    "upload",
}

FORBIDDEN_FIELD_NAMES = {
    "access_token",
    "auth_state_path",
    "captcha_solution",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "download_path",
    "har_path",
    "local_private_path",
    "mfa_code",
    "password",
    "payment_details",
    "private_file_path",
    "raw_page_html",
    "screenshot_path",
    "session_path",
    "storage_state_path",
    "trace_path",
    "video_path",
}

ALLOWED_TOP_LEVEL_FIELDS = {
    "artifacts",
    "auth_state_saved",
    "browser_launched",
    "created_at",
    "events",
    "notes",
    "session_mode",
    "transcript_version",
}

REQUIRED_VERSION = "devhub-attended-dry-run-v1"
REQUIRED_SESSION_MODE = "attended_dry_run"


def load_transcript(path: str | Path) -> Mapping[str, Any]:
    """Load a transcript JSON file without touching browser/session state."""

    transcript_path = Path(path)
    with transcript_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise DryRunTranscriptError("transcript must be a JSON object")
    return data


def validate_transcript_file(path: str | Path) -> DryRunValidationResult:
    """Load and validate an attended DevHub dry-run transcript fixture."""

    return validate_transcript(load_transcript(path))


def validate_transcript(transcript: Mapping[str, Any]) -> DryRunValidationResult:
    """Validate a side-effect-free attended DevHub dry-run transcript."""

    _validate_top_level_shape(transcript)
    _validate_no_forbidden_fields(transcript, path="transcript")

    artifacts = transcript.get("artifacts", [])
    events = transcript.get("events", [])
    assert isinstance(artifacts, list)
    assert isinstance(events, list)

    _validate_artifacts(artifacts)
    surfaces = _validate_events(events)

    warnings: list[str] = []
    if not artifacts:
        warnings.append("no artifacts recorded")

    return DryRunValidationResult(
        event_count=len(events),
        surfaces=tuple(sorted(surfaces)),
        warnings=tuple(warnings),
    )


def _validate_top_level_shape(transcript: Mapping[str, Any]) -> None:
    unknown = sorted(set(transcript) - ALLOWED_TOP_LEVEL_FIELDS)
    if unknown:
        raise DryRunTranscriptError(f"unknown top-level field(s): {', '.join(unknown)}")

    if transcript.get("transcript_version") != REQUIRED_VERSION:
        raise DryRunTranscriptError("transcript_version must be devhub-attended-dry-run-v1")
    if transcript.get("session_mode") != REQUIRED_SESSION_MODE:
        raise DryRunTranscriptError("session_mode must be attended_dry_run")
    if transcript.get("browser_launched") is not False:
        raise DryRunTranscriptError("browser_launched must be false for dry-run validation")
    if transcript.get("auth_state_saved") is not False:
        raise DryRunTranscriptError("auth_state_saved must be false for dry-run validation")

    events = transcript.get("events")
    if not isinstance(events, list) or not events:
        raise DryRunTranscriptError("events must be a non-empty array")

    artifacts = transcript.get("artifacts", [])
    if not isinstance(artifacts, list):
        raise DryRunTranscriptError("artifacts must be an array when present")


def _validate_artifacts(artifacts: Sequence[Any]) -> None:
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, Mapping):
            raise DryRunTranscriptError(f"artifact {index} must be an object")
        kind = _normal_text(artifact.get("kind"))
        if kind in FORBIDDEN_ARTIFACT_KINDS:
            raise DryRunTranscriptError(f"forbidden artifact kind: {kind}")
        if artifact.get("persisted") is True:
            raise DryRunTranscriptError(f"artifact {index} must not be persisted")


def _validate_events(events: Sequence[Any]) -> set[str]:
    surfaces: set[str] = set()
    for index, event in enumerate(events):
        if not isinstance(event, Mapping):
            raise DryRunTranscriptError(f"event {index} must be an object")

        event_type = _normal_text(event.get("event_type"))
        if not event_type:
            raise DryRunTranscriptError(f"event {index} missing event_type")
        if event_type in FORBIDDEN_EVENT_TYPES:
            raise DryRunTranscriptError(f"forbidden browser or consequential event: {event_type}")

        if event.get("performed_by") not in {"human", "validator", "plan"}:
            raise DryRunTranscriptError(f"event {index} performed_by must be human, validator, or plan")
        if event.get("requires_attendance") is not True:
            raise DryRunTranscriptError(f"event {index} must require attendance")
        if event.get("browser_action") is not False:
            raise DryRunTranscriptError(f"event {index} browser_action must be false")

        surface = _normal_text(event.get("surface"))
        if not surface:
            raise DryRunTranscriptError(f"event {index} missing surface")
        surfaces.add(surface)

    return surfaces


def _validate_no_forbidden_fields(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if not isinstance(key, str):
                raise DryRunTranscriptError(f"{path} contains a non-string field name")
            normalized = _normal_text(key)
            if normalized in FORBIDDEN_FIELD_NAMES:
                raise DryRunTranscriptError(f"forbidden private field at {path}.{key}")
            _validate_no_forbidden_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_forbidden_fields(child, f"{path}[{index}]")


def _normal_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("-", "_").replace(" ", "_")
