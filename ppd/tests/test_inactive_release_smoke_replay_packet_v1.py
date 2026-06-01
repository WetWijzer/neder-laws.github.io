from __future__ import annotations

import copy
import unittest
from pathlib import Path
from typing import Any

from ppd.agent_readiness.inactive_release_smoke_replay_packet_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    InactiveReleaseSmokeReplayPacketV1Error,
    assert_valid_inactive_release_smoke_replay_packet_v1,
    load_inactive_release_smoke_replay_packet_v1,
    validate_inactive_release_smoke_replay_packet_v1,
)

FIXTURE = Path(__file__).parent / "fixtures" / "inactive_release_smoke_replay_packet_v1" / "packet.json"


class InactiveReleaseSmokeReplayPacketV1Tests(unittest.TestCase):
    def test_fixture_replays_required_agent_facing_scenarios(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(FIXTURE)

        self.assertEqual(validate_inactive_release_smoke_replay_packet_v1(packet), [])
        self.assertEqual(packet["validation_commands"], EXACT_OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(
            {scenario["scenario_type"] for scenario in packet["replay_scenarios"]},
            {"missing_information", "blocked_action", "next_safe_action", "reversible_draft", "exact_confirmation"},
        )
        self.assertEqual({scenario["outcome"] for scenario in packet["replay_scenarios"]}, {"pass", "hold", "reject"})

    def test_fixture_is_inactive_offline_and_non_mutating(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(FIXTURE)

        self.assertTrue(all(packet["boundaries"].values()))
        self.assertEqual(
            packet["inactive_release_candidate_manifest"]["candidate_status"],
            "inactive_pending_reviewer_signoff",
        )
        self.assertTrue(packet["inactive_release_candidate_manifest"]["manifest_id"])
        self.assertFalse(packet["inactive_release_candidate_manifest"]["release_activation_enabled"])
        self.assertFalse(packet["inactive_release_candidate_manifest"]["release_promotion_enabled"])
        for scenario in packet["replay_scenarios"]:
            self.assertEqual(scenario["offline_validation_commands"], EXACT_OFFLINE_VALIDATION_COMMANDS)
            self.assertTrue(scenario["citation_references"])
            self.assertTrue(scenario["agent_facing_prompt"])
            self.assertTrue(scenario["expected_agent_response"])
            self.assertFalse(any(scenario["action_controls"].values()))

    def test_rejects_missing_candidate_manifest_reference(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["inactive_release_candidate_manifest"].pop("manifest_id")

        errors = validate_inactive_release_smoke_replay_packet_v1(unsafe)

        self.assertTrue(any("manifest_id must be a non-empty candidate manifest reference" in error for error in errors))

    def test_rejects_missing_required_replay_rows_and_outcomes(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["replay_scenarios"] = [
            scenario
            for scenario in unsafe["replay_scenarios"]
            if scenario["scenario_type"] not in {"missing_information", "blocked_action", "next_safe_action", "reversible_draft"}
        ]

        errors = validate_inactive_release_smoke_replay_packet_v1(unsafe)
        joined = "; ".join(errors)

        self.assertIn("missing_information", joined)
        self.assertIn("blocked_action", joined)
        self.assertIn("next_safe_action", joined)
        self.assertIn("reversible_draft", joined)
        self.assertIn("missing required replay outcomes", joined)

    def test_rejects_missing_citations_and_validation_commands(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["validation_commands"] = []
        unsafe["replay_scenarios"][0]["citation_references"] = []
        unsafe["replay_scenarios"][0]["offline_validation_commands"] = [["curl", "https://devhub.portlandoregon.gov"]]

        errors = validate_inactive_release_smoke_replay_packet_v1(unsafe)
        joined = "; ".join(errors)

        self.assertIn("validation_commands must contain only the exact offline self-test command", joined)
        self.assertIn("citation_references must be a non-empty list", joined)
        self.assertIn("offline_validation_commands must contain only the exact offline self-test command", joined)

    def test_validator_rejects_unknown_citation_live_artifact_and_enabled_action(self) -> None:
        packet = load_inactive_release_smoke_replay_packet_v1(FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["replay_scenarios"][0]["citation_references"] = ["ev:ppd-fixture:unknown:sha256:aaaaaaaa"]
        unsafe["replay_scenarios"][0]["action_controls"]["requires_devhub"] = True
        unsafe["replay_scenarios"][0]["browser_state_path"] = "state.json"

        errors = validate_inactive_release_smoke_replay_packet_v1(unsafe)

        self.assertTrue(any("unknown inactive manifest evidence id" in error for error in errors))
        self.assertTrue(any("requires_devhub must be false" in error for error in errors))
        self.assertTrue(any("forbidden private, session, browser, raw, or downloaded artifact key" in error for error in errors))
        with self.assertRaises(InactiveReleaseSmokeReplayPacketV1Error):
            assert_valid_inactive_release_smoke_replay_packet_v1(unsafe)

    def test_rejects_live_devhub_completion_activation_and_mutation_claims(self) -> None:
        cases: list[tuple[str, Any, str]] = [
            ("claim", "live crawl completed against public source", "live crawl or DevHub execution claim"),
            ("claim", "DevHub accessed for the replay", "live crawl or DevHub execution claim"),
            ("claim", "application submitted and fee paid", "official-action completion claim"),
            ("claim", "release activated for users", "release activation or promotion claim"),
            ("active_prompt_mutation", True, "active mutation or release activation flag"),
            ("downloaded_document_path", "permit.pdf", "forbidden private, session, browser, raw, or downloaded artifact key"),
            ("note", "raw crawl output was saved", "forbidden private, session, browser, raw, or downloaded artifact content"),
        ]

        for key, value, expected in cases:
            packet = load_inactive_release_smoke_replay_packet_v1(FIXTURE)
            unsafe = copy.deepcopy(packet)
            unsafe[key] = value

            errors = validate_inactive_release_smoke_replay_packet_v1(unsafe)

            self.assertTrue(any(expected in error for error in errors), f"missing {expected!r} for {key!r}: {errors}")


if __name__ == "__main__":
    unittest.main()
