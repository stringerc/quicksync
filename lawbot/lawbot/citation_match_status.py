"""
Deterministic citation *text* overlap: user message vs SOURCE CHUNKS (retrieved + vault).

This is **not** Shepard's/KeyCite, not holding verification, not pin-cite checking — only
whether a citation-like span from the user's paste appears in loaded excerpt/label text.
"""

from __future__ import annotations

import re

from lawbot.citation_extract import extract_citation_candidates


def _combined_corpus(chunks: list[dict]) -> str:
    parts: list[str] = []
    for c in chunks or []:
        parts.append((c.get("excerpt") or "") + "\n" + (c.get("label") or ""))
    return "\n".join(parts).lower()


def build_citation_match_status(user_message: str, chunks: list[dict]) -> str | None:
    """
    Markdown section for the LLM bundle, or None if not useful.
    """
    msg = (user_message or "").strip()
    if len(msg) < 400:
        return None
    extracted = extract_citation_candidates(msg, max_items=28)
    if not extracted:
        return None

    corpus = _combined_corpus(chunks)
    has_chunks = bool((chunks or []) and corpus.strip())

    lines: list[str] = [
        "## CITATION MATCH STATUS (server — not KeyCite / not Shepard's)",
        "",
        "Lawbot **does not** verify whether cases are still good law or whether reporter lines are correct. "
        "Below is **automatic string overlap**: whether each **extracted** cite-like span appears in **SOURCE CHUNK** "
        "text or labels loaded **this turn** (CourtListener retrieval + vault).",
        "",
    ]

    if not has_chunks:
        lines.append(
            "- **No opinion excerpts loaded** — nothing to match against. "
            "Enable **Look up real court cases**, paste **Lexis/Westlaw excerpts** into the vault, or use **Verify citations** mode for a structured audit."
        )
        lines.append("")
        return "\n".join(lines).strip()

    for e in extracted:
        raw = e.raw.strip()
        if len(raw) > 140:
            disp = raw[:137] + "…"
        else:
            disp = raw
        key = raw.lower()
        if key in corpus:
            st = "**Match** — this span appears verbatim in a loaded excerpt or label (holding **not** verified)."
        elif e.kind == "case_name":
            toks = re.split(r"\s+v\.?\s+", key, maxsplit=1)
            left = (toks[0] or "").strip()
            right = (toks[1] or "").strip() if len(toks) > 1 else ""
            r0 = right.split()[0] if right else ""
            if left and r0 and len(left) > 2 and len(r0) > 1 and left in corpus and r0 in corpus:
                st = "**Partial** — both sides' names appear in loaded text (confirm same case and reporter)."
            elif left and len(left) > 3 and left in corpus:
                st = "**Partial** — first party name appears in loaded text (confirm full cite)."
            else:
                st = "**No substring match** — loaded excerpts do not contain this case string; **not verified**."
        else:
            st = "**No substring match** — loaded excerpts do not contain this exact cite text; **not verified**."

        lines.append(f"- `{disp}` ({e.kind}) — {st}")

    lines.append("")
    lines.append(
        "**For KeyCite/Shepard's treatment** and **pin cites**, use your **Westlaw/Lexis** subscription — Lawbot cannot run those products."
    )
    return "\n".join(lines).strip()
