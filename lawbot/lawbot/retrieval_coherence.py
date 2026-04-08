"""
Heuristic coherence score for case-law retrieval (Resonance-style CWSC-lite).

Low scores on short, non-legal messages reduce parallel CourtListener fan-out so
``hello``-style traffic does not run large multi-query bundles when unnecessary.
"""

from __future__ import annotations

import re

# Overlap with authority_retrieval._CIVIL_LIT — expanded slightly for general legal Qs.
_LEGALISH = re.compile(
    r"\b("
    r"statute|regulation|court|plaintiff|defendant|petition|motion|brief|pleading|"
    r"malpractice|discovery|jurisdiction|appeal|contract|negligence|custody|"
    r"O\.C\.G\.A|U\.S\.C|Fed\.?\s*R\.?\s*Civ|rule\s+\d+|cite|citation|"
    r"answer|counterclaim|magistrate|summons|subpoena|deposition|"
    r"ga\b|georgia|federal|circuits?"
    r")\b",
    re.I,
)


def coherence_score_for_retrieval(
    message: str,
    *,
    document_mode: bool,
    explicit_research_query: str | None,
) -> float:
    """
    Return 0..1 — higher means more likely the user needs broad case-law retrieval.
    Deterministic; no LLM calls.
    """
    m = (message or "").strip()
    if explicit_research_query and str(explicit_research_query).strip():
        return 0.85
    if document_mode and len(m) >= 2000:
        return 0.78
    if document_mode and len(m) >= 400:
        return 0.65
    if len(m) < 40:
        return 0.22
    if len(m) < 160:
        return 0.38
    if _LEGALISH.search(m):
        return 0.72
    return 0.48


def apply_coherence_query_cap(
    queries_ran: list[str],
    *,
    coherence: float,
    include_authority_pack: bool,
    force_authority: bool,
    threshold: float = 0.45,
) -> tuple[list[str], bool]:
    """
    If coherence is low and multiple queries were planned, keep only the first query
    (primary retrieval) unless authority pack or force is active.

    Returns (possibly shortened list, trimmed_flag).
    """
    if force_authority or include_authority_pack:
        return list(queries_ran), False
    if coherence >= threshold or len(queries_ran) <= 1:
        return list(queries_ran), False
    return [queries_ran[0]], True
