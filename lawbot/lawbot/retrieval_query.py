"""
Phase 5 — CourtListener query helpers: jurisdiction-aware expansion and chunk deduplication.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


def augment_courtlistener_query(query: str, profile: dict[str, str] | None) -> str:
    """Add jurisdiction hints from profile when the query looks legal but lacks a state."""
    q = (query or "").strip()
    if not q:
        return q
    prof = profile or {}
    juris = (prof.get("jurisdiction") or "").strip()
    if not juris:
        return q
    low = q.lower()
    # Already has a strong state/circuit mention
    if re.search(
        r"\b(georgia|florida|texas|california|new york|federal|11th cir|ninth circuit)\b",
        low,
    ):
        return q
    # Short query: prepend jurisdiction once
    if len(q) < 180 and juris.lower() not in low:
        return f"{juris} {q}"
    return q


def chunk_fingerprint(chunk: dict[str, Any]) -> str:
    label = (chunk.get("label") or "").strip()[:200]
    ex = (chunk.get("excerpt") or "")[:400]
    h = hashlib.sha256(f"{label}\n{ex}".encode("utf-8", errors="replace")).hexdigest()
    return h


def dedupe_chunks(chunks: list[dict[str, Any]], chunk_ids: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Drop near-duplicate chunks (same fingerprint), preserving order."""
    seen: set[str] = set()
    out_c: list[dict[str, Any]] = []
    out_ids: list[str] = []
    for i, c in enumerate(chunks):
        if i >= len(chunk_ids):
            break
        cid = chunk_ids[i]
        fp = chunk_fingerprint(c)
        if fp in seen:
            continue
        seen.add(fp)
        out_c.append(c)
        out_ids.append(cid)
    return out_c, out_ids
