"""retrieval_query helpers."""

from __future__ import annotations

import unittest

from lawbot.retrieval_query import augment_courtlistener_query, dedupe_chunks


class TestRetrievalQuery(unittest.TestCase):
    def test_augment_adds_jurisdiction(self):
        q = augment_courtlistener_query("fee collection malpractice", {"jurisdiction": "Georgia"})
        self.assertIn("Georgia", q)

    def test_augment_no_duplicate_state(self):
        q = augment_courtlistener_query("Georgia contract law", {"jurisdiction": "Georgia"})
        self.assertEqual(q.count("Georgia"), 1)

    def test_dedupe_chunks(self):
        a = {"chunk_id": "c1", "label": "X", "excerpt": "same text here"}
        b = {"chunk_id": "c2", "label": "X", "excerpt": "same text here"}
        c = {"chunk_id": "c3", "label": "Y", "excerpt": "different"}
        out, ids = dedupe_chunks([a, b, c], ["c1", "c2", "c3"])
        self.assertEqual(len(out), 2)
        self.assertEqual(ids, ["c1", "c3"])


if __name__ == "__main__":
    unittest.main()
