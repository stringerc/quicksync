"""Derive empty-vault / footer messaging from retrieval results."""

from __future__ import annotations

from typing import Any


def vault_footer_and_flags(
    retrieval: dict[str, Any],
    search_case_law: bool,
    chunk_ids: list[str],
) -> tuple[bool, str | None, bool]:
    """
    Returns (empty_vault, footer_note, retrieval_skipped_api).
    retrieval_skipped_api = CourtListener was not queried (toggle off or empty query).
    """
    vault_empty = len(chunk_ids) == 0
    cl_not_run = bool(retrieval.get("retrieval_skipped")) or not search_case_law
    q_executed = bool(retrieval.get("query_executed"))
    footer_note: str | None = None
    if vault_empty:
        if retrieval.get("retrieval_failed"):
            hs = retrieval.get("http_status")
            detail = (retrieval.get("error_detail") or "").strip()
            if hs in (401, 403):
                footer_note = (
                    "CourtListener rejected the request (auth). Check COURTLISTENER_TOKEN in `.env`, "
                    "rotate the token at courtlistener.com if needed, and restart the server."
                )
            elif hs == 429:
                footer_note = "CourtListener rate-limited this request. Wait a minute and retry, or turn off case search."
            elif hs == 400 and detail:
                footer_note = (
                    "CourtListener could not parse this search. Try shorter or simpler wording in your message. "
                    f"Detail: {detail[:280]}"
                )
            elif hs is not None and 500 <= int(hs) < 600:
                footer_note = (
                    "CourtListener had a server error while searching. Retry in a few minutes, or turn off case search."
                )
            elif retrieval.get("network_error"):
                footer_note = (
                    "Could not reach CourtListener (network). Check your connection, DNS, or firewall; "
                    "or turn off case search for a general answer."
                )
            elif detail:
                footer_note = f"Case-law search failed (CourtListener). {detail[:400]}"
            else:
                footer_note = (
                    "Case-law search failed (API). Retry later, or turn off case search for a general answer."
                )
        elif q_executed and search_case_law:
            footer_note = (
                "No opinions were added to the vault for this search. Try different keywords, "
                "paste an excerpt into the vault (e.g. Lexis paste), or ask a broader question."
            )
    return vault_empty, footer_note, cl_not_run
