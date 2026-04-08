"""
Measurable, deterministic checks on assistant drafts (no LLM — rules only).

Weighted scoring emphasizes anti-garbage checks (placeholders, vault quotes) over layout heuristics.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass

# Higher = more important for weighted_score_percent (shipping gate uses this).
CHECK_WEIGHTS: dict[str, int] = {
    "non_empty": 2,
    "no_placeholders": 5,
    "no_internal_labels": 3,
    "no_duplicate_blocks": 2,
    "long_reply_structure": 1,
    "fee_1311_substance": 3,
    "editor_overview_depth": 2,
    "vault_quote_ids": 4,
}


@dataclass
class QualityCheck:
    id: str
    passed: bool
    detail: str


# Placeholders and fake chunk ids the model must not emit to users.
# Note: Bare "TBD" is intentionally omitted — real pleadings use "TBD — fees (at trial)" etc.
# We only flag vague filler like "grant TBD relief" (see tests/fixtures/golden/bad_tbd.txt).
_PLACEHOLDER = re.compile(
    r"(\b(TODO|FIXME|placeholder|lorem\s+ipsum)\b|"
    r"\[insert|\[your\s+name|\[party\s+name|"
    r"chk_[Xx\?]{4,}|chk_[A-Za-z0-9]*XXXX)",
    re.I,
)

# Vague "TBD" used as a stand-in for real relief or remedy (drafting error).
_BAD_TBD_FILLER = re.compile(r"\bTBD\s+(relief|remedy)\b", re.I)

_INTERNAL_LABEL = re.compile(
    r"\b(SOURCE\s+CHUNKS|allowed_chunk_ids|allowed chunk ids)\b",
    re.I,
)

_NUMBERED_OR_HEADING = re.compile(
    r"(^|\n)(#{1,3}\s+|\d+\.\s+.{3,})",
    re.MULTILINE,
)

_QUOTE_CHUNK_ATTR = re.compile(r'<quote\s+chunk="([^"]+)"', re.IGNORECASE)

_FEE_1311_CUE = re.compile(r"13-6-11|COUNT\s+FOUR", re.IGNORECASE)


def _drafting_heavy_user_message(user_message: str) -> bool:
    u = (user_message or "").strip().lower()
    if len(u) > 1200:
        return True
    return bool(
        re.search(
            r"\b(motion|filing|brief|answer|counterclaim|complaint|pleading|"
            r"strengthen|rewrite|draft|magistrate|court)\b",
            u,
        )
    )


def _paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    return parts


def _has_duplicate_paragraph(text: str, min_len: int = 120) -> tuple[bool, str]:
    paras = _paragraphs(text)
    seen: set[str] = set()
    for p in paras:
        if len(p) < min_len:
            continue
        key = p[:500]
        if key in seen:
            return True, "Repeated paragraph block detected (same text appears twice)."
        seen.add(key)
    return False, ""


def _fee_1311_substance_check(text: str) -> QualityCheck:
    """
    When a § 13-6-11 / Count Four block exists, expect multiple sentences and at least two statutory-prong hooks.
    Heuristic only — not legal advice.
    """
    if len(text) < 2000:
        return QualityCheck(
            id="fee_1311_substance",
            passed=True,
            detail="Skipped — reply shorter than drafting threshold.",
        )
    m = _FEE_1311_CUE.search(text)
    if not m:
        return QualityCheck(
            id="fee_1311_substance",
            passed=True,
            detail="Skipped — no § 13-6-11 / Count Four.",
        )
    chunk = text[m.start() : m.start() + 5000]
    low = chunk.lower()
    prong_hits = sum(
        [
            "bad faith" in low or "bad-faith" in low,
            "stubborn" in low,
            ("unnecessary" in low and "expense" in low) or "trouble and expense" in low,
        ]
    )
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", chunk) if len(s.strip()) > 22]
    substantive = len(sentences) >= 5
    ok = prong_hits >= 2 and substantive
    return QualityCheck(
        id="fee_1311_substance",
        passed=ok,
        detail=(
            "Fee count: multiple sentences and at least two § 13-6-11 prongs (bad faith / stubbornly litigious / unnecessary trouble & expense) appear developed."
            if ok
            else "Fee count under § 13-6-11 may be thin — add labeled subparts (a)(b)(c) with fact-specific conduct per prong."
        ),
    )


def _editor_overview_depth_check(text: str) -> QualityCheck:
    """Flag generic Editor's overview language without concrete PART / ¶ anchors."""
    if len(text) < 3500:
        return QualityCheck(
            id="editor_overview_depth",
            passed=True,
            detail="Skipped — medium-length reply.",
        )
    if "## Editor's overview" not in text and "Editor's overview (not for filing)" not in text:
        return QualityCheck(
            id="editor_overview_depth",
            passed=True,
            detail="Skipped — no Editor's overview section.",
        )
    tail = text.split("Editor's overview", 1)[-1][:7000]
    low = tail.lower()
    vague_a = "minor reorganization" in low or ("reorganization" in low and "clarity" in low)
    vague_b = "preserves all" in low and "original" in low
    vague_c = "may also increase" in low and "risk" in low and "omit" in low
    boilerplate_hits = sum([vague_a, vague_b, vague_c])
    has_concrete = bool(re.search(r"PART\s+[IVX]{1,5}|¶\s*\d+", tail)) or tail.count("- ") >= 4
    if boilerplate_hits >= 2 and not has_concrete:
        return QualityCheck(
            id="editor_overview_depth",
            passed=False,
            detail="Editor's overview looks boilerplate — list concrete PARTs/¶s and specific edits (avoid vague 'reorganization' / 'preserves all' alone).",
        )
    if boilerplate_hits >= 2:
        return QualityCheck(
            id="editor_overview_depth",
            passed=False,
            detail="Editor's overview may rely on generic phrasing — strengthen Preservation checklist and Delta with named sections.",
        )
    return QualityCheck(
        id="editor_overview_depth",
        passed=True,
        detail="Editor's overview block present (spot-check for concrete PART/¶ detail).",
    )


def _vault_quote_chunk_ids_valid(text: str, allowed_chunk_ids: list[str]) -> QualityCheck:
    """When the vault has chunks, every <quote chunk="id"> must reference an allowed id."""
    if not allowed_chunk_ids:
        return QualityCheck(
            id="vault_quote_ids",
            passed=True,
            detail="Skipped — no vault chunks attached to this turn.",
        )
    found = _QUOTE_CHUNK_ATTR.findall(text)
    if not found:
        return QualityCheck(
            id="vault_quote_ids",
            passed=True,
            detail="No `<quote chunk>` tags in answer (OK for this turn).",
        )
    allowed = set(allowed_chunk_ids)
    bad = [cid for cid in found if cid not in allowed]
    if bad:
        return QualityCheck(
            id="vault_quote_ids",
            passed=False,
            detail=f"Quote tags use ids not in this turn's vault: {bad[:6]!r}",
        )
    return QualityCheck(
        id="vault_quote_ids",
        passed=True,
        detail="All `<quote chunk>` ids are in the loaded vault set.",
    )


def _compute_scores(checks: list[QualityCheck], vault_chunk_ids: list[str]) -> tuple[int, int, int]:
    """Returns (unweighted_percent, weighted_percent, checks_passed_count)."""
    n = len(checks)
    passed_n = sum(1 for c in checks if c.passed)
    unweighted = int(round(100.0 * passed_n / n)) if n else 0

    w_num = 0
    w_den = 0
    for c in checks:
        w = CHECK_WEIGHTS.get(c.id, 1)
        if c.id == "vault_quote_ids" and not vault_chunk_ids:
            w = 0
        # Skipped heuristics should not move the weighted score (denominator inflation).
        if c.id in ("fee_1311_substance", "editor_overview_depth") and "Skipped" in c.detail:
            w = 0
        if w <= 0:
            continue
        w_den += w
        if c.passed:
            w_num += w
    weighted = int(round(100.0 * w_num / w_den)) if w_den else 0
    return unweighted, weighted, passed_n


def analyze_draft_quality(
    answer: str,
    *,
    user_message: str = "",
    document_mode: bool = True,
    citation_audit: bool = False,
    vault_chunk_ids: list[str] | None = None,
) -> dict[str, object]:
    """
    Run deterministic checks. Returns JSON-serializable dict.

    - ``score_percent`` — **weighted** score (0–100), primary metric for export gates.
    - ``score_percent_unweighted`` — equal weight per check (legacy / comparison).
    """
    text = (answer or "").strip()
    v_ids = list(vault_chunk_ids or [])
    checks: list[QualityCheck] = []

    ok_len = len(text) >= 40
    checks.append(
        QualityCheck(
            id="non_empty",
            passed=ok_len,
            detail="Answer has at least ~40 characters of content."
            if ok_len
            else "Reply is empty or too short.",
        )
    )

    ph = _PLACEHOLDER.search(text)
    bad_tbd = _BAD_TBD_FILLER.search(text)
    ok_ph = ph is None and bad_tbd is None
    if not ok_ph:
        bad = ph or bad_tbd
        ph_snip = (bad.group(0) if bad else "")[:48]
    else:
        ph_snip = ""
    checks.append(
        QualityCheck(
            id="no_placeholders",
            passed=ok_ph,
            detail="No TODO/chk_/placeholder/lorem-style tokens or vague 'TBD relief'."
            if ok_ph
            else f"Found placeholder-like token near: {ph_snip!r}",
        )
    )

    il = _INTERNAL_LABEL.search(text)
    ok_il = il is None
    checks.append(
        QualityCheck(
            id="no_internal_labels",
            passed=ok_il,
            detail="No internal system labels in user-facing text."
            if ok_il
            else f"Leaked internal label: {il.group(0)!r}",
        )
    )

    dup, dup_detail = _has_duplicate_paragraph(text)
    checks.append(
        QualityCheck(
            id="no_duplicate_blocks",
            passed=not dup,
            detail="No large duplicated paragraph blocks."
            if not dup
            else dup_detail,
        )
    )

    drafting = _drafting_heavy_user_message(user_message)
    long_answer = len(text) > 2200
    if document_mode and drafting and long_answer and not citation_audit:
        has_struct = bool(_NUMBERED_OR_HEADING.search(text))
        checks.append(
            QualityCheck(
                id="long_reply_structure",
                passed=has_struct,
                detail="Long reply uses # headings or numbered paragraphs."
                if has_struct
                else "Long reply has no Markdown headings or numbered list — consider adding structure.",
            )
        )
    else:
        if citation_audit and long_answer and drafting:
            struct_detail = "Skipped — citation-audit replies often use ** headers instead of # headings."
        else:
            struct_detail = "Skipped (short reply or non-drafting context)."
        checks.append(
            QualityCheck(
                id="long_reply_structure",
                passed=True,
                detail=struct_detail,
            )
        )

    if document_mode and not citation_audit:
        checks.append(_fee_1311_substance_check(text))
        checks.append(_editor_overview_depth_check(text))
    else:
        checks.append(
            QualityCheck(
                id="fee_1311_substance",
                passed=True,
                detail="Skipped — citation audit or non-document mode.",
            )
        )
        checks.append(
            QualityCheck(
                id="editor_overview_depth",
                passed=True,
                detail="Skipped — citation audit or non-document mode.",
            )
        )

    checks.append(_vault_quote_chunk_ids_valid(text, v_ids))

    uw, wgt, passed_n = _compute_scores(checks, v_ids)
    total = len(checks)

    return {
        "score_percent": wgt,
        "score_percent_unweighted": uw,
        "checks_passed": passed_n,
        "checks_total": total,
        "all_passed": passed_n == total,
        "checks": [asdict(c) for c in checks],
        "weights": dict(CHECK_WEIGHTS),
    }


def draft_quality_to_json_line(report: dict[str, object]) -> str:
    """One-line JSON for CI logs / dashboards."""
    return json.dumps(
        {
            "score_percent": report.get("score_percent"),
            "score_percent_unweighted": report.get("score_percent_unweighted"),
            "all_passed": report.get("all_passed"),
            "checks_total": report.get("checks_total"),
            "checks_passed": report.get("checks_passed"),
        },
        separators=(",", ":"),
    )


def build_draft_shipping(
    draft_quality: dict[str, object] | None,
    *,
    verification_ok: bool | None,
    draft_judge: dict[str, object] | None,
) -> dict[str, object] | None:
    """
    Single combined view for API clients: deterministic checks + vault quote verification,
    with optional judge folded in when ``draft_judge`` was requested.

    - ``ok`` — True only when deterministic checks pass, quotes verify, and (if judge ran) rubric passes.
    - ``judge_ok`` — ``None`` if judge was not run; otherwise whether parsed scores meet a minimal bar.
    """
    if draft_quality is None:
        return None
    det = bool(draft_quality.get("all_passed"))
    quote_ok = verification_ok is True
    judge_ok: bool | None = None
    if draft_judge:
        judge_ok = _draft_judge_acceptable(draft_judge)
    ok = det and quote_ok and (judge_ok is None or judge_ok)
    return {
        "ok": ok,
        "deterministic_ok": det,
        "quote_verification_ok": quote_ok,
        "judge_ok": judge_ok,
    }


def _draft_judge_acceptable(draft_judge: dict[str, object]) -> bool:
    if not draft_judge.get("parse_ok"):
        return False
    try:
        c = int(draft_judge.get("clarity", 0))
        s = int(draft_judge.get("structure", 0))
    except (TypeError, ValueError):
        return False
    return c >= 3 and s >= 3
