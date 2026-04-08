"""
Session-scoped embedding RAG: retrieve relevant prior chat excerpts for the current question,
and ingest each turn's user + assistant text for future turns.
"""

from __future__ import annotations

import json
import logging
import math
import sqlite3
from typing import Any

from lawbot.citation_vault import CitationVault
from lawbot.config import settings
from lawbot.embedding_client import embed_texts, embed_query

log = logging.getLogger(__name__)

SOURCE = "session_memory_rag"


def merge_chunk_lists(first: list[dict[str, Any]], second: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """Concatenate chunk dict lists, deduping by chunk_id (first list wins)."""
    seen: set[str] = set()
    out_c: list[dict[str, Any]] = []
    out_ids: list[str] = []
    for ch in first + second:
        cid = (ch.get("chunk_id") or "").strip()
        if not cid or cid in seen:
            continue
        seen.add(cid)
        out_c.append(ch)
        out_ids.append(cid)
    return out_c, out_ids


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na * nb)


def chunk_text(text: str, max_chars: int) -> list[str]:
    t = (text or "").strip()
    if not t:
        return []
    parts: list[str] = []
    for para in t.split("\n\n"):
        p = para.strip()
        if not p:
            continue
        if len(p) <= max_chars:
            parts.append(p)
            continue
        start = 0
        while start < len(p):
            parts.append(p[start : start + max_chars])
            start += max_chars
    merged: list[str] = []
    buf = ""
    for p in parts:
        if not buf:
            buf = p
        elif len(buf) + 2 + len(p) <= max_chars:
            buf = f"{buf}\n\n{p}"
        else:
            if len(buf) >= 40:
                merged.append(buf)
            buf = p
    if buf and len(buf) >= 40:
        merged.append(buf)
    return merged


def _prune_old_embeddings(conn: sqlite3.Connection, session_id: str) -> None:
    max_rows = max(1, settings.session_rag_max_stored_chunks)
    row = conn.execute(
        "SELECT COUNT(*) FROM session_embedding_chunks WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    n = int(row[0] if row else 0)
    excess = n - max_rows
    if excess <= 0:
        return
    conn.execute(
        """
        DELETE FROM session_embedding_chunks WHERE rowid IN (
          SELECT rowid FROM session_embedding_chunks
          WHERE session_id = ?
          ORDER BY created_at ASC
          LIMIT ?
        )
        """,
        (session_id, excess),
    )


async def retrieve_session_context_isolated(
    db_path: str,
    session_id: str,
    query: str,
    embed_ms_accum: dict[str, float] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Same as retrieve_session_context but uses a dedicated SQLite connection so this can run
    in parallel with retrieve_for_query_conn on another connection (lower latency).
    """
    conn = sqlite3.connect(db_path, timeout=60.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        return await retrieve_session_context(conn, session_id, query, embed_ms_accum=embed_ms_accum)
    finally:
        conn.close()


async def retrieve_session_context(
    conn: sqlite3.Connection,
    session_id: str,
    query: str,
    embed_ms_accum: dict[str, float] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """
    Returns (chunks, chunk_ids) for vault-backed excerpts from this session's embedding index.
    """
    if not settings.session_rag_enabled():
        return [], []
    q = (query or "").strip()
    if len(q) < settings.session_rag_min_message_chars:
        return [], []
    try:
        q_emb = await embed_query(q, embed_ms_accum=embed_ms_accum)
    except Exception as e:
        log.warning("session RAG embed query failed: %s", e)
        return [], []
    if not q_emb:
        return [], []
    rows = conn.execute(
        """
        SELECT vault_chunk_id, embedding_json FROM session_embedding_chunks
        WHERE session_id = ?
        """,
        (session_id,),
    ).fetchall()
    if not rows:
        return [], []
    scored: list[tuple[float, str]] = []
    for row in rows:
        vid = row[0]
        try:
            emb = json.loads(row[1] or "[]")
        except Exception:
            continue
        if not isinstance(emb, list):
            continue
        c = _cosine(q_emb, [float(x) for x in emb])
        scored.append((c, vid))
    scored.sort(key=lambda x: -x[0])
    k = max(1, min(settings.session_rag_top_k, 16))
    top_ids: list[str] = []
    for c, vid in scored[:k]:
        if c >= 0.08:
            top_ids.append(vid)

    vault = CitationVault(conn)
    chunks: list[dict[str, Any]] = []
    chunk_ids: list[str] = []
    for vid in top_ids:
        row = vault.get_chunk(vid)
        if not row:
            continue
        chunks.append(
            {
                "chunk_id": row["id"],
                "label": row["citation_label"] or "Earlier in this chat",
                "source_url": row["source_url"],
                "excerpt": row["verbatim_text"],
            }
        )
        chunk_ids.append(row["id"])
    return chunks, chunk_ids


async def ingest_turn(
    conn: sqlite3.Connection,
    session_id: str,
    user_text: str,
    assistant_text: str,
) -> None:
    """Embed and store chunks from the completed turn (for the next user message)."""
    if not settings.session_rag_enabled():
        return
    blob = f"{(user_text or '').strip()}\n\n---\n\n{(assistant_text or '').strip()}".strip()
    if len(blob) < settings.session_rag_min_message_chars:
        return
    parts = chunk_text(blob, settings.session_rag_chunk_max_chars)
    if not parts:
        return
    try:
        embeddings = await embed_texts(parts)
    except Exception as e:
        log.warning("session RAG ingest embed failed: %s", e)
        return
    vault = CitationVault(conn)
    for p, emb in zip(parts, embeddings, strict=False):
        if not emb:
            continue
        cid = vault.store_chunk(
            source_system=SOURCE,
            verbatim_text=p,
            source_url=None,
            citation_label="Earlier in this chat",
            raw_meta={"session_id": session_id},
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO session_embedding_chunks (session_id, vault_chunk_id, embedding_json, created_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (session_id, cid, json.dumps(emb)),
        )
    _prune_old_embeddings(conn, session_id)
    conn.commit()
