"""Automatic verification appendix (no network)."""

import unittest

from lawbot.verification_bundle import (
    build_verification_appendix,
    extract_ocga_sections,
)


class TestVerificationBundle(unittest.TestCase):
    def test_extract_ocga_sections(self):
        t = "See O.C.G.A. § 9-11-9.1 and O.C.G.A. § 13-6-11 for fees."
        s = extract_ocga_sections(t)
        self.assertIn("9-11-9.1", s)
        self.assertIn("13-6-11", s)

    def test_build_appendix_includes_statute_and_opinion_rows(self):
        app = build_verification_appendix(
            user_message="Counterclaim under O.C.G.A. § 51-1-30.",
            retrieved_chunks=[
                {
                    "chunk_id": "chk_a",
                    "label": "Smith v. Jones",
                    "source_url": "https://www.courtlistener.com/opinion/12345/x/",
                    "excerpt": "Held that …",
                    "opinion_id": 12345,
                }
            ],
            profile={"jurisdiction": "Georgia"},
            document_mode=True,
            audit_mode=False,
            meta_connectivity=False,
            search_case_law=True,
        )
        self.assertIsNotNone(app)
        assert app is not None
        self.assertIn("AUTOMATIC VERIFICATION LINKS", app)
        self.assertIn("51-1-30", app)
        self.assertIn("scholar.google.com", app)
        self.assertIn("courtlistener.com/opinion/12345", app)
        self.assertIn("Shepard", app)

    def test_audit_mode_skips(self):
        self.assertIsNone(
            build_verification_appendix(
                user_message="long " * 200,
                retrieved_chunks=[],
                profile={},
                document_mode=True,
                audit_mode=True,
                meta_connectivity=False,
                search_case_law=True,
            )
        )


if __name__ == "__main__":
    unittest.main()
