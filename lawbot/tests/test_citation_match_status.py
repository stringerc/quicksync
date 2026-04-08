"""Citation substring match report (not KeyCite)."""

from __future__ import annotations

import unittest

from lawbot.citation_match_status import build_citation_match_status


class TestCitationMatchStatus(unittest.TestCase):
    def test_no_chunks_lists_empty(self):
        msg = "Per Kellos v. Sawilowsky, 254 Ga. 4 (1985), the standard applies.\n" * 30
        s = build_citation_match_status(msg, [])
        assert s is not None
        self.assertIn("No opinion excerpts loaded", s)

    def test_substring_match_in_excerpt(self):
        msg = (
            "The court in Kellos v. Sawilowsky, 254 Ga. 4, 5, 325 S.E.2d 757 (1985), held the standard.\n" * 20
        )
        chunks = [
            {
                "chunk_id": "chk_1",
                "label": "Kellos v. Sawilowsky",
                "excerpt": "Kellos v. Sawilowsky, 254 Ga. 4, 5, 325 S.E.2d 757 (1985) — standard of care …",
                "source_url": "https://example.com",
            }
        ]
        s = build_citation_match_status(msg, chunks)
        assert s is not None
        self.assertIn("Match**", s)


if __name__ == "__main__":
    unittest.main()
