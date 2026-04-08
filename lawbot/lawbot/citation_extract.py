"""
Heuristic extraction of citation-like strings from user text (for audit mode).

This is not a full Bluebook parser — it surfaces candidates for targeted retrieval
and for the model to reconcile against SOURCE CHUNKS.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedCitation:
    raw: str
    kind: str  # statute | case_name | reporter | lexis | usc | other


def _norm_key(s: str) -> str:
    return " ".join(s.split()).lower()[:500]


# Longer / more specific patterns first.
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"O\.C\.G\.A\.\s*§?\s*[\d\-\.]+(?:\s*\([^)]{0,48}\))?",
            re.IGNORECASE,
        ),
        "statute",
    ),
    (
        re.compile(r"\d+\s+U\.S\.C\.\s*§?\s*[\d\w\-\.]+", re.IGNORECASE),
        "usc",
    ),
    (
        re.compile(
            r"\d+\s+[A-Za-z.\s]+\s+LEXIS\s+\d+",
            re.IGNORECASE,
        ),
        "lexis",
    ),
    (
        re.compile(
            r"\d+\s+(?:Ga\.(?:\s+App\.?)?|F\.(?:3d|2d|4th)|U\.S\.)\s+\d+",
            re.IGNORECASE,
        ),
        "reporter",
    ),
    (
        re.compile(r"\d+\s+S\.E\.2d\s+\d+", re.IGNORECASE),
        "reporter",
    ),
    (
        re.compile(
            r"\b[A-Z][a-zA-Z0-9'\-]{0,40}\s+v\.?\s+[A-Z][a-zA-Z0-9'\-]{0,40}\b",
        ),
        "case_name",
    ),
]


def extract_citation_candidates(text: str, *, max_items: int = 40) -> list[ExtractedCitation]:
    """
    Return deduplicated citation-like spans found in *text*, newest/longest preference by scan order.
    """
    if not (text or "").strip():
        return []
    seen: set[str] = set()
    out: list[ExtractedCitation] = []

    for rx, kind in _PATTERNS:
        for m in rx.finditer(text):
            raw = m.group(0).strip()
            if len(raw) < 4:
                continue
            key = _norm_key(raw)
            if key in seen:
                continue
            seen.add(key)
            out.append(ExtractedCitation(raw=raw, kind=kind))
            if len(out) >= max_items:
                return out
    return out


def extracted_to_json_rows(items: list[ExtractedCitation]) -> list[dict[str, str]]:
    return [{"raw": x.raw, "kind": x.kind} for x in items]
