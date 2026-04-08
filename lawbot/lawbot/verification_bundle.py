"""
Automatic “outside counsel checklist” links appended to document-mode prompts.

Does **not** call Westlaw **KeyCite** or Lexis **Shepard’s** (those require paid subscriptions / TR contracts).
May append **CourtListener** forward-citation **counts** when ``citation_graph_counts`` is provided — still **not** KeyCite treatment flags.
Also builds deterministic URLs from retrieved chunks and statute-like strings.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote_plus

from lawbot.gwinnett_magistrate import GWINNETT_MAGISTRATE_CIVIL_FORMS_URL

_MAX_APPENDIX_CHARS = 6000
_MAX_OCGA_LINKS = 10
_MAX_OPINION_ROWS = 8

# Georgia Code sections as commonly written in filings (e.g. 9-11-9.1, 13-6-11).
_OCGA_RE = re.compile(
    r"O\.C\.G\.A\.?\s*§?\s*(\d+(?:-\d+)*(?:\.\d+)?)",
    re.IGNORECASE,
)


def _dedupe_preserve(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        k = x.strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(x.strip())
    return out


def extract_ocga_sections(text: str) -> list[str]:
    if not text:
        return []
    found = _OCGA_RE.findall(text)
    return _dedupe_preserve(found)[:_MAX_OCGA_LINKS]


def _courtlistener_opinion_url(chunk: dict[str, Any]) -> str | None:
    u = (chunk.get("source_url") or "").strip()
    if u.startswith("http"):
        return u
    oid = chunk.get("opinion_id")
    if oid is not None:
        try:
            n = int(oid)
            return f"https://www.courtlistener.com/opinion/{n}/"
        except (TypeError, ValueError):
            pass
    return None


def _scholar_search_url(label: str) -> str:
    q = quote_plus((label or "case").strip()[:200])
    return f"https://scholar.google.com/scholar?q={q}&hl=en&as_sdt=4%2C60"


def _ocga_search_url(section: str) -> str:
    q = quote_plus(f"O.C.G.A. § {section} Georgia")
    return f"https://duckduckgo.com/?q={q}"


def build_verification_appendix(
    *,
    user_message: str,
    retrieved_chunks: list[dict[str, Any]],
    profile: dict[str, str],
    document_mode: bool,
    audit_mode: bool,
    meta_connectivity: bool,
    search_case_law: bool,
    citation_graph_counts: dict[int, int] | None = None,
) -> str | None:
    """
    Markdown block for the user bundle (internal). Returns None when not applicable.

    ``citation_graph_counts`` is optional precomputed CourtListener forward-citation counts
    (opinion_id -> count). Not KeyCite.
    """
    if not document_mode or audit_mode or meta_connectivity or not search_case_law:
        return None

    msg = user_message or ""
    blob = msg + " " + " ".join(str(v) for v in (profile or {}).values())
    low = blob.lower()
    if (
        len(msg) < 160
        and not retrieved_chunks
        and "gwinnett" not in low
        and not extract_ocga_sections(msg)
    ):
        return None

    cg = citation_graph_counts or {}
    lines: list[str] = [
        "## AUTOMATIC VERIFICATION LINKS (for counsel — do not file verbatim; do not paste long URL lists into the caption)",
        "",
        "**Limits:** Lawbot does **not** run **Westlaw KeyCite** or Lexis **Shepard’s** (paid citators). "
        + (
            "Optional **CourtListener** forward-citation counts appear below when available — they show how often later opinions cite a case in that database; they are **not** KeyCite treatment history. "
            if cg
            else ""
        )
        + "Use your licensed research tools for citator work before relying on any authority. Other links are **starting points** only.",
        "",
    ]

    ocga = extract_ocga_sections(msg)
    if ocga:
        lines.append("### Georgia statutes named in your message (search / confirm current text)")
        for sec in ocga:
            lines.append(f"- **O.C.G.A. § {sec}** — open search: {_ocga_search_url(sec)}")
        lines.append("")

    if retrieved_chunks:
        lines.append("### Retrieved judicial opinions (this turn)")
        for i, c in enumerate(retrieved_chunks[:_MAX_OPINION_ROWS], start=1):
            label = (c.get("label") or f"Opinion {i}").strip()
            cl_url = _courtlistener_opinion_url(c)
            scholar = _scholar_search_url(label)
            row = f"{i}. **{label}** — Google Scholar search: {scholar}"
            if cl_url:
                row += f" | CourtListener: {cl_url}"
            oid = c.get("opinion_id")
            try:
                oi = int(oid) if oid is not None else None
            except (TypeError, ValueError):
                oi = None
            if oi is not None and oi in cg:
                row += (
                    f" | **CourtListener cites:** {cg[oi]} later opinion(s) cite this decision "
                    f"(forward graph — **not** KeyCite)"
                )
            lines.append(f"- {row}")
        lines.append(
            "- **KeyCite / Shepard’s:** run in **Westlaw** or **Lexis** in your subscription — Lawbot cannot execute those products."
        )
        lines.append("")
    elif ocga or "gwinnett" in blob.lower():
        lines.append("### Retrieved opinions")
        lines.append(
            "- No opinion excerpts were loaded into SOURCE CHUNKS this turn — enable case search or paste a vault excerpt; "
            "still run a citator on any case you cite from your draft."
        )
        lines.append("")

    if "gwinnett" in blob.lower():
        lines.append("### Gwinnett / local forms hub (verify current PDFs)")
        lines.append(f"- Magistrate civil forms index: {GWINNETT_MAGISTRATE_CIVIL_FORMS_URL}")
        lines.append("")

    lines.append(
        "**For the assistant:** Mention briefly in **Editor's overview → Honest limits** that these links exist; "
        "do **not** reproduce more than one short line of URLs in the filed pleading body."
    )

    out = "\n".join(lines).strip()
    if len(out) > _MAX_APPENDIX_CHARS:
        out = out[: _MAX_APPENDIX_CHARS] + "\n\n[Truncated — keep verification steps short.]"
    return out
