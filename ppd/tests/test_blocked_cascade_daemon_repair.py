import json
from datetime import datetime, timezone
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "blocked_cascade" / "tranche5_item2.json"


def _parse_instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fresh_validated_daemon_repair(blocked_task, repair_attempts):
    blocked_at = _parse_instant(blocked_task["blocked_at"])
    for repair in repair_attempts:
        if repair.get("kind") != "daemon-repair":
            continue
        if not repair.get("validated", False):
            continue
        if _parse_instant(repair["created_at"]) > blocked_at:
            return repair
    return None


def _blocked_task_state(blocked_task, repair_attempts):
    repair = _fresh_validated_daemon_repair(blocked_task, repair_attempts)
    if repair is None:
        return "parked"
    return "repair-validated"


def test_blocked_ppd_work_stays_parked_without_fresh_validated_daemon_repair():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    blocked_task = fixture["blocked_task"]
    stale_or_failed_repairs = fixture["repair_attempts"][:2]

    assert _blocked_task_state(blocked_task, stale_or_failed_repairs) == "parked"


def test_blocked_ppd_work_unparks_after_fresh_validated_daemon_repair():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    blocked_task = fixture["blocked_task"]
    repair_attempts = fixture["repair_attempts"]

    assert _blocked_task_state(blocked_task, repair_attempts) == "repair-validated"
    assert _fresh_validated_daemon_repair(blocked_task, repair_attempts)["id"] == "repair-fresh-valid"
