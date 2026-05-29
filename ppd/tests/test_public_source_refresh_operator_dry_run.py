from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.public_source_refresh_operator_dry_run import (
    build_public_source_refresh_operator_dry_run_transcript,
)


class PublicSourceRefreshOperatorDryRunTest(unittest.TestCase):
    def test_builds_metadata_only_operator_transcript_from_fixture_packets(self) -> None:
        fixture_path = (
            Path(__file__).parent
            / "fixtures"
            / "public_source_refresh_operator_dry_run"
            / "input_packets.json"
        )
        packets = json.loads(fixture_path.read_text(encoding="utf-8"))

        transcript = build_public_source_refresh_operator_dry_run_transcript(
            packets["source_refresh_runbook_candidate"],
            packets["public_source_refresh_batch_packet"],
            packets["public_source_refresh_intake_evidence_packet"],
            packets["source_registry_schedule_update_candidate"],
            reviewer="ppd-reviewer",
            owner="ppd-source-refresh-owner",
        )

        self.assertEqual(
            transcript["packet_type"],
            "public_source_refresh_operator_dry_run_transcript",
        )
        self.assertEqual(transcript["mode"], "fixture_first_dry_run")
        self.assertEqual(transcript["sources"], ["portland-auditor-code"])
        self.assertEqual(transcript["reviewer"], "ppd-reviewer")
        self.assertEqual(transcript["owner"], "ppd-source-refresh-owner")
        self.assertEqual(
            [step["order"] for step in transcript["ordered_simulated_operator_steps"]],
            [1, 2, 3, 4, 5],
        )
        self.assertIn(
            "fixture://allowlist/portland-auditor-code.json",
            transcript["allowlist_evidence_refs"],
        )
        self.assertIn(
            "fixture://robots/portland-auditor-code.txt",
            transcript["robots_evidence_refs"],
        )
        self.assertTrue(transcript["abort_or_rollback_checkpoints"])
        self.assertEqual(
            transcript["attestations"],
            {
                "no_fetch": True,
                "no_processor": True,
                "no_download": True,
                "no_schedule_mutation": True,
                "metadata_only_observations": True,
            },
        )


if __name__ == "__main__":
    unittest.main()
