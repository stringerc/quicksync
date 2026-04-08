"""
Human-readable “what happened this turn” for transparency (plain language) + light metrics.
Does not duplicate the full audit object — use audit for technical detail.
"""

from __future__ import annotations

from typing import Any


def _sec(ms: int) -> str:
    if ms < 1000:
        return f"{ms} ms"
    return f"{ms / 1000:.1f} s"


def build_turn_receipt(
    *,
    session_id: str,
    duration_ms: int,
    out: dict[str, Any],
    audit: dict[str, Any],
    meta_connectivity: bool,
    phase_timings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a small JSON-safe dict for the API and UI. Wording targets ~5th grade reading level
    for `summary_lines` (short sentences, no legalese in the receipt itself).
    """
    if out.get("error"):
        err = str(out.get("error") or "unknown error")[:240]
        return {
            "session_id": session_id,
            "duration_ms": duration_ms,
            "duration_human": _sec(duration_ms),
            "summary_lines": [
                "We could not finish this reply.",
                f"Detail: {err}",
            ],
            "speed_tips": ["Try a shorter question or check that the AI service is running."],
            "quality_line": "Fix the error, then ask again.",
        }

    lines: list[str] = []
    speed_tips: list[str] = []

    if meta_connectivity:
        lines.append("Ran a quick system check (no case search this time).")
        return {
            "session_id": session_id,
            "duration_ms": duration_ms,
            "duration_human": _sec(duration_ms),
            "summary_lines": lines,
            "speed_tips": [],
            "quality_line": "Connection check only — ask a real question when you are ready.",
        }

    if out.get("retrieval_skipped") and not audit.get("strengthen_always_retrieves"):
        lines.append("Skipped looking up new court cases on purpose (faster).")
        speed_tips.append('Turn on "Look up real court cases" when you need authorities.')
    elif audit.get("vault_chunk_count", 0) > 0:
        n = int(audit["vault_chunk_count"])
        lines.append(f"Used {n} piece{'s' if n != 1 else ''} of court text in this answer.")
    else:
        lines.append("No court text was found to attach — the answer still follows safety rules.")

    sr = int(audit.get("session_rag_excerpts") or 0)
    if sr > 0:
        lines.append(f"Pulled {sr} snippet{'s' if sr != 1 else ''} from earlier in this chat.")

    if audit.get("two_phase_filing_applied"):
        lines.append("Used two-step drafting (fact check, then quotes) for stronger filings.")
        speed_tips.append("You can turn off two-step drafting in Extra settings for a quicker reply when you do not need that.")

    if out.get("polish_second_pass_applied"):
        lines.append("Tightened wording in a second pass for readability.")
    elif out.get("polish_second_pass_reason"):
        lines.append("Skipped the extra wording pass this time (faster).")

    if out.get("verification_ok") is True and audit.get("vault_chunk_count", 0) > 0:
        quality_line = "Quotes were checked against the text you loaded."
    elif out.get("verification_ok") is False:
        quality_line = "Some quotes need a quick human check — see the warning above the answer."
    else:
        quality_line = "Always double-check anything before you file it."

    if audit.get("paste_only_no_research_effective") and audit.get("strengthen_always_retrieves"):
        lines.append("Your task needed case law — search ran even though paste-only was on.")

    duration_line = f"Total time for this reply: {_sec(duration_ms)}."
    lines.append(duration_line)

    if phase_timings and isinstance(phase_timings, dict):
        r_ms = phase_timings.get("retrieval_ms")
        ttft = phase_timings.get("llm_ttft_ms")
        if isinstance(r_ms, (int, float)) and r_ms > 0:
            lines.append(f"Server timing: lookup and context ~{_sec(int(r_ms))}.")
        if isinstance(ttft, (int, float)) and ttft > 0:
            lines.append(f"First model token after ~{_sec(int(ttft))} (after context was ready).")
        emb = phase_timings.get("embed_ms")
        if isinstance(emb, (int, float)) and emb > 0:
            lines.append(f"Embedding this question for session memory took ~{_sec(int(emb))}.")

    if duration_ms > 120_000 and not speed_tips:
        speed_tips.append("Very long pastes take longer. Shorter questions or turning off case search can speed things up.")

    receipt: dict[str, Any] = {
        "session_id": session_id,
        "duration_ms": duration_ms,
        "duration_human": _sec(duration_ms),
        "summary_lines": lines,
        "speed_tips": speed_tips[:3],
        "quality_line": quality_line,
    }
    if phase_timings:
        receipt["phase_timings"] = phase_timings
    return receipt
