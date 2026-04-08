"""CourtListener retrieval payload cache (SQLite)."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from typing import Any

from lawbot.config import settings


def _query_key(normalized_query: str) -> str:
    return hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()


def get_cached(conn: sqlite3.Connection, normalized_query: str) -> dict[str, Any] | None:
    if not settings.cl_search_cache_enabled or settings.cl_search_cache_ttl_seconds <= 0:
        return None
    qk = _query_key(normalized_query)
    row = conn.execute(
        "SELECT response_json, created_at FROM cl_search_cache WHERE query_key = ?",
        (qk,),
    ).fetchone()
    if not row:
        return None
    created = float(row[1] or 0)
    if time.time() - created > float(settings.cl_search_cache_ttl_seconds):
        conn.execute("DELETE FROM cl_search_cache WHERE query_key = ?", (qk,))
        conn.commit()
        return None
    try:
        return json.loads(row[0])
    except Exception:
        return None


def put_cached(conn: sqlite3.Connection, normalized_query: str, payload: dict[str, Any]) -> None:
    if not settings.cl_search_cache_enabled or settings.cl_search_cache_ttl_seconds <= 0:
        return
    qk = _query_key(normalized_query)
    conn.execute(
        """
        INSERT OR REPLACE INTO cl_search_cache (query_key, response_json, created_at)
        VALUES (?, ?, ?)
        """,
        (qk, json.dumps(payload), time.time()),
    )
    conn.commit()
