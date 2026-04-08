"""Tests for heuristic citation extraction."""

import unittest

from lawbot.citation_extract import extract_citation_candidates, extracted_to_json_rows


class TestCitationExtract(unittest.TestCase):
    def test_ocga(self):
        t = "Under O.C.G.A. § 9-3-25 malpractice claims must be timely."
        xs = extract_citation_candidates(t)
        kinds = {x.kind for x in xs}
        self.assertIn("statute", kinds)
        self.assertTrue(any("O.C.G.A." in x.raw for x in xs))

    def test_case_name(self):
        t = "See Kellos v. Sawilowsky for the standard of care."
        xs = extract_citation_candidates(t)
        self.assertTrue(any("Kellos" in x.raw and "case_name" == x.kind for x in xs))

    def test_reporter_ga(self):
        t = "The court held 254 Ga. 4, 325 S.E.2d 757 (1985)."
        xs = extract_citation_candidates(t)
        self.assertTrue(any(x.kind == "reporter" for x in xs))

    def test_dedupe(self):
        t = "O.C.G.A. § 1-2-3. O.C.G.A. § 1-2-3."
        xs = extract_citation_candidates(t)
        self.assertEqual(len([x for x in xs if "O.C.G.A." in x.raw]), 1)

    def test_extracted_to_json_rows(self):
        xs = extract_citation_candidates("Kellos v. Sawilowsky")
        rows = extracted_to_json_rows(xs)
        self.assertTrue(all("raw" in r and "kind" in r for r in rows))


if __name__ == "__main__":
    unittest.main()
