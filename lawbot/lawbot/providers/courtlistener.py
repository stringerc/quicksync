"""
CourtListener REST API — https://www.courtlistener.com/help/api/rest/
Requires COURTLISTENER_TOKEN for authenticated rate limits.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# New CourtListener API tokens are denied on v3 search; use v4 (see migration guide).
BASE = "https://www.courtlistener.com/api/rest/v4"

DEFAULT_HEADERS = {
    "User-Agent": "Lawbot/1.0 (legal research; courtlistener API)",
    "Accept": "application/json",
}


def _auth_headers(token: str | None) -> dict[str, str]:
    h = dict(DEFAULT_HEADERS)
    if token:
        h["Authorization"] = f"Token {token}"
    return h


async def _get_json(url: str, params: dict[str, Any] | None, token: str | None) -> Any:
    headers = _auth_headers(token)
    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            async with httpx.AsyncClient(timeout=90.0, follow_redirects=True) as client:
                r = await client.get(url, params=params, headers=headers)
                r.raise_for_status()
                return r.json()
        except httpx.HTTPStatusError as e:
            code = e.response.status_code
            body = (e.response.text or "")[:300]
            logger.warning("CourtListener HTTP %s %s — %s", code, url, body)
            if code in (429, 502, 503, 504) and attempt == 0:
                await asyncio.sleep(2.0)
                continue
            raise
        except httpx.RequestError as e:
            last_exc = e
            logger.warning("CourtListener network error (attempt %s): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(1.5)
                continue
            raise last_exc
    raise last_exc  # pragma: no cover


def opinion_id_from_search_hit(hit: dict[str, Any]) -> int | None:
    """Resolve an opinion PK from a v3 flat hit or a v4 cluster-shaped hit (nested opinions)."""
    for key in ("id", "pk", "opinion_id"):
        v = hit.get(key)
        if v is None:
            continue
        try:
            return int(v)
        except (TypeError, ValueError):
            continue
    opinions = hit.get("opinions")
    if isinstance(opinions, list) and opinions:
        first = opinions[0]
        if isinstance(first, dict):
            oid = first.get("id") or first.get("pk")
            if oid is not None:
                try:
                    return int(oid)
                except (TypeError, ValueError):
                    pass
    sib = hit.get("sibling_ids")
    if isinstance(sib, list) and sib:
        try:
            return int(sib[0])
        except (TypeError, ValueError):
            pass
    return None


async def search_opinions(query: str, token: str | None, limit: int = 5) -> list[dict[str, Any]]:
    params = {"q": query, "type": "o", "order_by": "score desc"}
    data = await _get_json(f"{BASE}/search/", params, token)
    results = data.get("results") or []
    return results[:limit]


def excerpt_from_search_hit(hit: dict[str, Any]) -> tuple[str | None, str, str | None]:
    """
    Public search results include opinion snippets without fetching /opinions/{id}/.
    Returns (excerpt_or_none, case_label, absolute_url_or_none).
    """
    label = (hit.get("caseName") or hit.get("caseNameFull") or "Opinion").strip()
    raw_url = hit.get("absolute_url")
    page_url: str | None = None
    if raw_url:
        page_url = raw_url if raw_url.startswith("http") else "https://www.courtlistener.com" + raw_url
    opinions = hit.get("opinions") or []
    snippet = ""
    if opinions and isinstance(opinions[0], dict):
        snippet = (opinions[0].get("snippet") or "").strip()
    if not snippet:
        snippet = (hit.get("snippet") or "").strip()
    if len(snippet) < 40:
        return None, label, page_url
    return snippet, label, page_url


async def fetch_opinion_cluster(opinion_id: int, token: str | None) -> dict[str, Any]:
    return await _get_json(f"{BASE}/opinions/{opinion_id}/", None, token)


async def opinions_cited_forward_count(cited_opinion_id: int, token: str | None) -> int | None:
    """
    How many opinions in CourtListener's database cite ``cited_opinion_id`` (forward citations).

    This is **not** Westlaw KeyCite (no treatment flags, history, or editorial signals).
    See https://www.courtlistener.com/help/api/rest/citations/
    """
    try:
        data = await _get_json(
            f"{BASE}/opinions-cited/",
            {"cited_opinion": cited_opinion_id, "page_size": 1},
            token,
        )
        c = data.get("count")
        if c is None:
            return None
        return int(c)
    except httpx.HTTPStatusError as e:
        logger.info(
            "CourtListener opinions-cited unavailable for opinion %s: HTTP %s",
            cited_opinion_id,
            e.response.status_code,
        )
        return None
    except Exception as e:
        logger.warning("CourtListener opinions-cited error for %s: %s", cited_opinion_id, e)
        return None


async def opinion_plaintext_best_effort(opinion: dict[str, Any], token: str | None) -> tuple[str, str | None]:
    """
    Returns (text, source_url) for vault storage.
    """
    text = (opinion.get("plain_text") or opinion.get("html") or "").strip()
    url = opinion.get("absolute_url")
    if url and not url.startswith("http"):
        url = "https://www.courtlistener.com" + url
    if len(text) < 50 and opinion.get("cluster"):
        cluster_id = opinion["cluster"]
        if isinstance(cluster_id, str) and cluster_id.isdigit():
            cluster_id = int(cluster_id)
        if isinstance(cluster_id, int):
            try:
                c = await _get_json(f"{BASE}/clusters/{cluster_id}/", None, token)
                text = text or (c.get("case_name") or "")
            except Exception:
                pass
    return text, url
