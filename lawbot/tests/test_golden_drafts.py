"""
Golden-file regression: synthetic drafts in tests/fixtures/golden/ + manifest.json.

Run in CI: scripts/ci_quality.sh or unittest discover.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from lawbot.draft_quality_gate import analyze_draft_quality, draft_quality_to_json_line

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "golden"


class TestGoldenDraftFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))

    def test_manifest_cases_run_clean(self):
        for case in self.manifest["cases"]:
            with self.subTest(case=case["id"]):
                ans = (FIXTURE_DIR / case["answer_file"]).read_text(encoding="utf-8")
                usr = (FIXTURE_DIR / case["user_file"]).read_text(encoding="utf-8")
                r = analyze_draft_quality(
                    ans,
                    user_message=usr,
                    document_mode=True,
                    citation_audit=case.get("citation_audit", False),
                    vault_chunk_ids=case.get("vault_chunk_ids"),
                )
                # Log line for CI dashboards (one JSON object per case).
                line = draft_quality_to_json_line(r)
                self.assertIn("score_percent", line)
                if case.get("expect_all_pass"):
                    self.assertTrue(r["all_passed"], msg=f"{case['id']}: {r['checks']}")
                    self.assertGreaterEqual(
                        r["score_percent"],
                        case["min_weighted_score"],
                        msg=case["id"],
                    )
                else:
                    self.assertFalse(r["all_passed"], msg=case["id"])
                    mx = case.get("max_weighted_score")
                    if mx is not None:
                        self.assertLessEqual(
                            r["score_percent"],
                            mx,
                            msg=f"{case['id']} weighted score too high",
                        )


if __name__ == "__main__":
    unittest.main()
