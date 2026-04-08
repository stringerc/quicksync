from __future__ import annotations

from typing import Any

import httpx

from lawbot.cl_cache import get_cached, put_cached
from lawbot.citation_vault import CitationVault
from lawbot.config import settings
from lawbot.providers import courtlistener
from lawbot.providers.courtlistener import excerpt_from_search_hit, opinion_id_from_search_hit
from lawbot.retrieval_query import augment_courtlistener_query, dedupe_chunks

MIN_CHARS_FULL_OPINION = 80
MIN_CHARS_SNIPPET = 120


def _http_error_payload(exc: httpx.HTTPStatusError) -> dict[str, Any]:
    detail: str | None = None
    try:
        j = exc.response.json()
        d = j.get("detail")
        if isinstance(d, str):
            detail = d[:500]
        elif d is not None:
            detail = str(d)[:500]
    except Exception:
        detail = (exc.response.text or "")[:300] or None
    return {
        "chunks": [],
        "chunk_ids": [],
        "retrieval_failed": True,
        "query_executed": True,
        "http_status": exc.response.status_code,
        "error_detail": detail,
    }


async def retrieve_for_query_conn(
    conn,
    user_query: str,
    profile: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Pull candidate opinions from CourtListener and store excerpts in the vault.

    Search is available without an API token; full opinion text requires a token.
    When no token (or fetch fails), we still use **snippets** from search hits so the
    vault can contain verifiable quotes.

    On network/API failure at the search step, returns empty chunks so chat can continue.
    """
    q = augment_courtlistener_query((user_query or "").strip(), profile)
    if not q:
        return {"chunks": [], "chunk_ids": [], "retrieval_skipped": True, "query_executed": False}

    cached = get_cached(conn, q)
    if cached is not None:
        return cached

    vault = CitationVault(conn)
    token = (settings.courtlistener_token or "").strip() or None
    chunks: list[dict[str, Any]] = []
    chunk_ids: list[str] = []

    async def _search(qs: str) -> list[dict[str, Any]]:
        return await courtlistener.search_opinions(qs, token, limit=5)

    try:
        hits = await _search(q)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400 and len(q) > 100:
            try:
                short_q = " ".join(q.split())[:100]
                hits = await _search(short_q)
            except httpx.HTTPStatusError as e2:
                return _http_error_payload(e2)
        else:
            return _http_error_payload(e)
    except httpx.RequestError:
        return {
            "chunks": [],
            "chunk_ids": [],
            "retrieval_failed": True,
            "query_executed": True,
            "network_error": True,
        }

    for h in hits:
        oid_int = opinion_id_from_search_hit(h)
        label = (h.get("caseName") or "Unknown case").strip()
        excerpt: str | None = None
        url: str | None = None
        source = "courtlistener"

        if token and oid_int is not None:
            try:
                op = await courtlistener.fetch_opinion_cluster(oid_int, token)
                text, url = await courtlistener.opinion_plaintext_best_effort(op, token)
                label = (op.get("caseName") or op.get("case_name") or label).strip()
                if text and len(text.strip()) >= MIN_CHARS_FULL_OPINION:
                    excerpt = text.strip()[:12000]
            except httpx.HTTPStatusError:
                pass
            except Exception:
                pass

        if excerpt is None or len(excerpt) < MIN_CHARS_FULL_OPINION:
            sn, lab, page_url = excerpt_from_search_hit(h)
            if sn and len(sn) >= MIN_CHARS_SNIPPET:
                excerpt = sn[:12000]
                label = lab or label
                url = page_url or url
                source = "courtlistener_search_snippet"
            elif sn and len(sn) >= 40:
                # Last resort: shorter snippet (still labeled as preview text)
                excerpt = sn[:12000]
                label = lab or label
                url = page_url or url
                source = "courtlistener_search_snippet"

        if not excerpt or len(excerpt) < 40:
            continue

        cid = vault.store_chunk(
            source_system=source,
            verbatim_text=excerpt,
            source_url=url,
            citation_label=str(label),
            raw_meta={"opinion_id": oid_int} if oid_int else {},
        )
        chunk_ids.append(cid)
        chunks.append(
            {
                "chunk_id": cid,
                "label": label,
                "source_url": url,
                "excerpt": excerpt,
                "opinion_id": oid_int,
            }
        )
        if len(chunks) >= 3:
            break

    chunks, chunk_ids = dedupe_chunks(chunks, chunk_ids)
    payload = {"chunks": chunks, "chunk_ids": chunk_ids, "query_executed": True}
    put_cached(conn, q, payload)
    return payload
