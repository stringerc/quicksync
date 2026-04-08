"""
Targeted CourtListener query bundles for filing / strengthen tasks (Georgia-heavy defaults).

Merged with audit queries in chat_turn; capped per turn to limit latency.
"""

from __future__ import annotations

import re
from typing import Any

# Hard cap on distinct queries per turn (each may hit CourtListener once).
MAX_TOTAL_RETRIEVAL_QUERIES = 10


def effective_max_queries(message_len: int) -> int:
    """Shorter cap for huge pastes — retrieval is sequential and dominates wall time."""
    n = max(0, int(message_len or 0))
    if n > 50_000:
        return 5
    if n > 25_000:
        return 7
    return MAX_TOTAL_RETRIEVAL_QUERIES

# Base pack when message looks like civil litigation / malpractice / fees (Georgia).
_DEFAULT_GA_PACK = [
    "Cox-Ott Barnes Thornburg Georgia attorney reasonable care legal malpractice",
    "White v. Rolley Georgia legal malpractice case within case",
    "Georgia legal malpractice attorney standard of care discovery",
    "Georgia magistrate counterclaim transfer jurisdiction",
    "O.C.G.A. 15-10-45 magistrate transfer counterclaim Georgia",
]

# When fee / contract / setoff themes appear.
_FEE_PACK = [
    "Georgia attorney fees collection malpractice counterclaim",
    "O.C.G.A. 13-6-11 bad faith attorney fees Georgia",
]

_CIVIL_LIT = re.compile(
    r"\b("
    r"answer|counterclaim|malpractice|discovery|magistrate|attorney|plaintiff|defendant|"
    r"motion|brief|pleading|fee|contract|setoff|O\.C\.G\.A|gwinnett"
    r")\b",
    re.I,
)


def _looks_like_filing_task(message: str) -> bool:
    m = (message or "").strip()
    if len(m) < 200:
        return False
    return bool(_CIVIL_LIT.search(m))


def build_authority_pass_queries(message: str, profile: dict[str, Any] | None = None) -> list[str]:
    """
    Return focused queries (deduped) for authority pass. Profile jurisdiction augments when helpful.
    """
    out: list[str] = []
    seen: set[str] = set()

    def add(q: str) -> None:
        q = " ".join(q.split())
        if len(q) < 8:
            return
        key = q.lower()[:220]
        if key in seen:
            return
        seen.add(key)
        out.append(q)

    if not _looks_like_filing_task(message):
        return out

    low = (message or "").lower()
    for q in _DEFAULT_GA_PACK:
        add(q)
    if re.search(r"\b(fee|fees|13-6-11|setoff|collection|invoice|bill)\b", low):
        for q in _FEE_PACK:
            add(q)

    # County / superior hints (CourtListener keyword search — not a guarantee of venue binding).
    if "gwinnett" in low:
        add("Gwinnett County Georgia State Court civil procedure")
    if "superior court" in low and ("georgia" in low or "gwinnett" in low):
        add("Georgia Superior Court civil discovery procedure")

    return out


def merge_queries_with_authority_cap(
    base_queries: list[str],
    message: str,
    profile: dict[str, Any] | None,
    *,
    include_authority_pass: bool,
    max_queries: int = MAX_TOTAL_RETRIEVAL_QUERIES,
) -> list[str]:
    """Append authority-pack queries to base list without duplicates; cap length."""
    out: list[str] = []
    seen: set[str] = set()

    def push(q: str) -> None:
        q = " ".join((q or "").split())
        if len(q) < 3:
            return
        k = q.lower()[:240]
        if k in seen:
            return
        seen.add(k)
        out.append(q)

    for q in base_queries or []:
        push(q)
        if len(out) >= max_queries:
            return out

    if not include_authority_pass:
        return out

    for q in build_authority_pass_queries(message, profile):
        push(q)
        if len(out) >= max_queries:
            break

    return out
