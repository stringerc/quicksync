"""
Audit mode: build targeted CourtListener queries and merge retrieval results.
"""

from __future__ import annotations

from typing import Any

from lawbot.citation_extract import ExtractedCitation
from lawbot.intent import prepare_case_law_search


MAX_AUDIT_QUERIES = 6


def _sanitize_q(q: str) -> str:
    q = " ".join(q.split())
    if len(q) > 2000:
        q = q[:2000]
    return q


def build_audit_queries(
    message: str,
    extracted: list[ExtractedCitation],
    profile: dict[str, str],
    explicit_research_query: str | None,
) -> list[str]:
    """
    Build up to MAX_AUDIT_QUERIES distinct search strings for CourtListener.
    Order: explicit research query (if any), then high-signal extracts, then fallback message-based query.
    """
    out: list[str] = []
    seen: set[str] = set()

    def add(q: str) -> None:
        q = _sanitize_q(q.strip())
        if len(q) < 3:
            return
        key = q.lower()[:240]
        if key in seen:
            return
        seen.add(key)
        out.append(q)

    if explicit_research_query and explicit_research_query.strip():
        add(explicit_research_query.strip())

    priority_kinds = frozenset({"statute", "usc", "lexis", "reporter", "case_name"})
    for e in extracted:
        if e.kind not in priority_kinds:
            continue
        add(e.raw)
        if len(out) >= MAX_AUDIT_QUERIES:
            return out

    base = prepare_case_law_search(message, None, profile)
    if base:
        add(base)

    return out[:MAX_AUDIT_QUERIES]


def merge_retrieval_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Merge multiple retrieve_for_query_conn payloads, deduplicating chunks by chunk_id.
    Preserves flags needed by vault_footer_and_flags when the merged vault is empty.
    """
    seen: set[str] = set()
    chunks: list[dict[str, Any]] = []
    chunk_ids: list[str] = []
    any_failed = False
    any_network = False
    any_executed = False
    all_skipped = True
    http_status: int | None = None
    error_detail: str | None = None

    for r in results:
        if r.get("retrieval_failed"):
            any_failed = True
        if r.get("network_error"):
            any_network = True
        if r.get("query_executed"):
            any_executed = True
            all_skipped = False
        if not r.get("retrieval_skipped"):
            all_skipped = False
        hs = r.get("http_status")
        if hs is not None and http_status is None:
            http_status = int(hs) if isinstance(hs, (int, float)) else None
        ed = (r.get("error_detail") or "").strip()
        if ed and not error_detail:
            error_detail = ed[:500]

        for c in r.get("chunks") or []:
            cid = c.get("chunk_id")
            if not cid or cid in seen:
                continue
            seen.add(cid)
            chunks.append(c)
            chunk_ids.append(cid)

    out: dict[str, Any] = {
        "chunks": chunks,
        "chunk_ids": chunk_ids,
        "query_executed": any_executed,
    }
    if any_network:
        out["network_error"] = True
    if all_skipped and results:
        out["retrieval_skipped"] = True
    if not results:
        out["retrieval_skipped"] = True
        out["query_executed"] = False

    # API/transport failure (not merely zero hits) — only when we could not store any chunk.
    if not chunk_ids and (any_failed or any_network):
        out["retrieval_failed"] = True
        if http_status is not None:
            out["http_status"] = http_status
        if error_detail:
            out["error_detail"] = error_detail

    return out
