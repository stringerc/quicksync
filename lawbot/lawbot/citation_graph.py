"""
CourtListener citation graph (forward citations) — not Westlaw KeyCite.

KeyCite is a Thomson Reuters product and requires a Westlaw subscription / API contract.
We optionally call CourtListener's ``opinions-cited`` API so users see how often later cases
cite a retrieved opinion. This does **not** provide KeyCite-style treatment history.
"""

from __future__ import annotations

import asyncio
from typing import Any

from lawbot.config import settings
from lawbot.providers.courtlistener import opinions_cited_forward_count

_MAX_OPINIONS_TO_QUERY = 8


async def enrich_opinion_forward_citation_counts(chunks: list[dict[str, Any]]) -> dict[int, int]:
    """
    For each distinct ``opinion_id`` on retrieved chunks, fetch forward citation count.

    Returns mapping ``opinion_id -> count`` (only IDs where the API returned a count).
    Requires ``COURTLISTENER_TOKEN`` for most deployments (anonymous may 401).
    """
    mode = (settings.lawbot_citation_graph or "auto").strip().lower()
    if mode == "never":
        return {}
    token = (settings.courtlistener_token or "").strip() or None
    if not token:
        return {}

    ids: list[int] = []
    for c in chunks or []:
        oid = c.get("opinion_id")
        if oid is None:
            continue
        try:
            n = int(oid)
        except (TypeError, ValueError):
            continue
        if n not in ids:
            ids.append(n)
    ids = ids[:_MAX_OPINIONS_TO_QUERY]
    if not ids:
        return {}

    async def one(oid: int) -> tuple[int, int | None]:
        cnt = await opinions_cited_forward_count(oid, token)
        return oid, cnt

    pairs = await asyncio.gather(*[one(i) for i in ids])
    out: dict[int, int] = {}
    for oid, cnt in pairs:
        if cnt is not None:
            out[oid] = cnt
    return out
