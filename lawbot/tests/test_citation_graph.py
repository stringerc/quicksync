"""CourtListener citation graph helper (mocked HTTP)."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from lawbot.config import settings
from lawbot.citation_graph import enrich_opinion_forward_citation_counts
from lawbot.verification_bundle import build_verification_appendix


class TestCitationGraph(unittest.IsolatedAsyncioTestCase):
    async def test_enrich_merges_counts(self):
        chunks = [
            {"chunk_id": "a", "label": "X v. Y", "opinion_id": 100, "excerpt": "t", "source_url": None},
        ]
        with (
            patch.object(settings, "courtlistener_token", "test-token"),
            patch.object(settings, "lawbot_citation_graph", "auto"),
            patch(
                "lawbot.citation_graph.opinions_cited_forward_count",
                new_callable=AsyncMock,
                side_effect=lambda oid, tok: 42 if oid == 100 else None,
            ),
        ):
            out = await enrich_opinion_forward_citation_counts(chunks)
        self.assertEqual(out, {100: 42})

    def test_appendix_includes_forward_count_line(self):
        app = build_verification_appendix(
            user_message="long " * 200 + "\nO.C.G.A. § 9-11-1\n",
            retrieved_chunks=[
                {
                    "chunk_id": "chk_x",
                    "label": "Test Case",
                    "opinion_id": 999,
                    "excerpt": "Held …",
                    "source_url": "https://www.courtlistener.com/opinion/999/x/",
                }
            ],
            profile={},
            document_mode=True,
            audit_mode=False,
            meta_connectivity=False,
            search_case_law=True,
            citation_graph_counts={999: 7},
        )
        assert app is not None
        self.assertIn("7 later opinion", app)
        self.assertIn("not** KeyCite", app)


if __name__ == "__main__":
    unittest.main()
