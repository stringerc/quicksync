"""Session RAG helpers (no live embedding API)."""

from unittest import TestCase

from lawbot.session_rag import SOURCE, chunk_text, merge_chunk_lists, _cosine


class TestSessionRagHelpers(TestCase):
    def test_cosine_identical(self):
        v = [0.1, 0.2, 0.3]
        self.assertAlmostEqual(_cosine(v, v), 1.0, places=5)

    def test_cosine_orthogonal(self):
        self.assertAlmostEqual(_cosine([1.0, 0.0], [0.0, 1.0]), 0.0, places=5)

    def test_chunk_text_splits_long_paragraph(self):
        s = "x" * 2500
        parts = chunk_text(s, max_chars=1000)
        self.assertGreaterEqual(len(parts), 2)
        self.assertTrue(all(len(p) <= 1000 for p in parts))

    def test_merge_chunk_lists_dedupes(self):
        a = [{"chunk_id": "c1", "label": "A", "excerpt": "a"}]
        b = [{"chunk_id": "c1", "label": "dup", "excerpt": "b"}, {"chunk_id": "c2", "label": "B", "excerpt": "c"}]
        mc, mids = merge_chunk_lists(a, b)
        self.assertEqual(mids, ["c1", "c2"])

    def test_source_constant(self):
        self.assertEqual(SOURCE, "session_memory_rag")
