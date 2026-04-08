"""CourtListener retrieval cache."""

import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from lawbot.cl_cache import get_cached, put_cached
from lawbot.db import connect


class TestClSearchCache(TestCase):
    def test_put_get_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "t.db"
            conn = connect(p)
            try:
                payload = {
                    "chunks": [{"chunk_id": "chk_x", "label": "A", "excerpt": "hi"}],
                    "chunk_ids": ["chk_x"],
                    "query_executed": True,
                }
                put_cached(conn, "miranda warning", payload)
                got = get_cached(conn, "miranda warning")
                self.assertEqual(got, payload)
            finally:
                conn.close()

    def test_expired_cache_miss(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "t.db"
            conn = connect(p)
            try:
                with patch("lawbot.cl_cache.time.time", return_value=1_000_000.0):
                    put_cached(conn, "q1", {"chunks": [], "chunk_ids": [], "query_executed": True})
                with patch("lawbot.cl_cache.settings.cl_search_cache_ttl_seconds", 60):
                    with patch("lawbot.cl_cache.time.time", return_value=1_000_000.0 + 120.0):
                        self.assertIsNone(get_cached(conn, "q1"))
            finally:
                conn.close()

    def test_different_queries_different_keys(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "t.db"
            conn = connect(p)
            try:
                put_cached(conn, "alpha", {"chunks": [], "chunk_ids": [], "query_executed": True, "tag": "a"})
                put_cached(conn, "beta", {"chunks": [], "chunk_ids": [], "query_executed": True, "tag": "b"})
                self.assertEqual(get_cached(conn, "alpha")["tag"], "a")
                self.assertEqual(get_cached(conn, "beta")["tag"], "b")
            finally:
                conn.close()
