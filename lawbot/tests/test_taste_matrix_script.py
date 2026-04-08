"""Unit tests for taste matrix heuristics (scripts/run_taste_matrix logic duplicated minimally)."""

from __future__ import annotations

import re
import unittest


def _body_after_audit_header(text: str) -> str:
    t = text or ""
    if "**Sources in vault:**" in t[:1200]:
        segs = t.split("\n\n", 2)
        if len(segs) >= 3:
            return segs[2]
    return t


_REDFLAGS = [
    (r"SOURCE\s+CHUNKS", "echoes internal label SOURCE CHUNKS"),
    (r"O\.C\.G\.A\.", "mentions O.C.G.A."),
]


def _score_answer(text: str) -> tuple[int, list[str]]:
    flags: list[str] = []
    scored = _body_after_audit_header(text)
    for rx, msg in _REDFLAGS:
        if re.search(rx, scored, re.I):
            flags.append(msg)
    return (len(flags), flags)


class TestTasteHeuristics(unittest.TestCase):
    def test_audit_header_not_ocga_false_positive(self):
        blob = (
            "**Sources in vault:** None loaded for this question.\n\n"
            "**Verified citations:** Not available — I cannot list or confirm O.C.G.A. sections.\n\n"
            "Here is the real answer with no statute spam."
        )
        n, fl = _score_answer(blob)
        self.assertNotIn("mentions O.C.G.A.", fl)

    def test_ocga_in_body_flags(self):
        blob = "**Sources in vault:** None.\n\n**Verified citations:** None.\n\nSee O.C.G.A. § 1 for fun."
        n, fl = _score_answer(blob)
        self.assertTrue(any("O.C.G.A" in f for f in fl))


if __name__ == "__main__":
    unittest.main()
