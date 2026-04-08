"""
UPRE-style structured signals for each chat turn: regime, coverage, confidence, gates.

Deterministic where possible — no extra LLM calls. Hermes runs on the assembled response dict.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from typing import Any

from lawbot.hermes_verify import hermes_report_to_dict, run_hermes_checks
from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING, CHAT_TASK_VERIFY_CITATIONS


def classify_task_regime(
    *,
    meta_connectivity: bool,
    use_citation_audit: bool,
    document_mode: bool,
    task_hint: str | None,
    message_len: int,
) -> str:
    if meta_connectivity:
        return "connectivity"
    if use_citation_audit:
        return "citation_audit"
    if document_mode and message_len >= 8000:
        return "high_stakes_long_paste"
    if document_mode and task_hint == CHAT_TASK_STRENGTHEN_FILING:
        return "filing_draft"
    if task_hint == CHAT_TASK_VERIFY_CITATIONS:
        return "citation_audit"
    if document_mode:
        return "filing_draft"
    return "conversational"


def _citation_confidence(
    *,
    vault_chunk_count: int,
    verification_ok: bool | None,
    verification_errors: list[str] | None,
    answer: str,
) -> float:
    """Heuristic 0..1 — not a statistical confidence interval."""
    ans = answer or ""
    if vault_chunk_count <= 0:
        if "<quote" in ans.lower():
            return 0.15
        return 0.35
    if verification_ok is True:
        return min(1.0, 0.55 + 0.1 * min(vault_chunk_count, 5))
    if verification_errors:
        return 0.25
    return 0.5


def _verification_scope(vault_chunk_count: int, use_citation_audit: bool) -> str:
    if use_citation_audit:
        return "citation_audit_mode"
    if vault_chunk_count > 0:
        return "quote_substrings_vs_vault"
    return "none"


def _warning_line_count(answer: str, verification_errors: list[str] | None) -> int:
    n = len(verification_errors or [])
    if not (answer or "").strip():
        return n
    # User-visible caution blocks from server / model
    n += len(re.findall(r"\[Verification warning\]", answer, re.I))
    n += len(re.findall(r"\[Note\]", answer))
    return n


def build_turn_signals(
    conn: sqlite3.Connection | None,
    out: dict[str, Any],
    *,
    body_message: str,
    meta_connectivity: bool,
    use_citation_audit: bool,
    document_mode: bool,
    task_hint: str | None,
    chunk_ids: list[str],
    queries_ran: list[str],
    retrieval_coherence: float | None = None,
    retrieval_coherence_trimmed: bool = False,
    answer_depth_level: str = "standard",
    answer_depth_reason: str = "default",
) -> dict[str, Any]:
    """Attach to API response as ``turn_signals``; also used for telemetry."""
    msg_len = len((body_message or "").strip())
    vault_n = len(chunk_ids)
    raw_ans = out.get("answer")
    answer = raw_ans if isinstance(raw_ans, str) else ""

    regime = classify_task_regime(
        meta_connectivity=meta_connectivity,
        use_citation_audit=use_citation_audit,
        document_mode=document_mode,
        task_hint=task_hint,
        message_len=msg_len,
    )

    cov_score = min(1.0, vault_n / 5.0) if vault_n else 0.0
    cc = _citation_confidence(
        vault_chunk_count=vault_n,
        verification_ok=out.get("verification_ok"),
        verification_errors=list(out.get("verification_errors") or []),
        answer=answer,
    )

    hermes_r = run_hermes_checks(conn, out)
    hermes_d = hermes_report_to_dict(hermes_r)

    ds = out.get("draft_shipping") or {}
    soft_shipping = bool(ds.get("needs_confirmation")) if isinstance(ds, dict) else False
    dq = out.get("draft_quality") or {}
    low_draft = False
    if isinstance(dq, dict) and dq.get("score_percent") is not None:
        try:
            low_draft = float(dq["score_percent"]) < 80.0
        except (TypeError, ValueError):
            pass

    gates = {
        "hermes_passed": hermes_r.passed,
        "hermes_hard_errors": list(hermes_r.errors[:12]),
        "shipping_soft_warn": soft_shipping or low_draft,
    }

    depth: dict[str, Any] = {"queries_executed": len(queries_ran)}
    if retrieval_coherence is not None:
        depth["coherence_score"] = round(float(retrieval_coherence), 3)
    if retrieval_coherence_trimmed:
        depth["coherence_trimmed"] = True

    return {
        "task_regime": regime,
        "answer_depth": {"level": answer_depth_level, "reason": answer_depth_reason},
        "vault_coverage": {"chunk_count": vault_n, "score": round(cov_score, 3)},
        "retrieval_depth": depth,
        "verification_scope": _verification_scope(vault_n, use_citation_audit),
        "citation_confidence": round(cc, 3),
        "gates": gates,
        "user_visible_warning_count": _warning_line_count(
            answer, list(out.get("verification_errors") or [])
        ),
        "hermes": hermes_d,
    }


def response_fingerprint(out: dict[str, Any], *, model_id: str | None) -> dict[str, str]:
    """For regression logs when a golden fails — prompt/answer hashes."""
    ans = (out.get("answer") or "") if isinstance(out.get("answer"), str) else ""
    h_ans = hashlib.sha256(ans.encode("utf-8", errors="replace")).hexdigest()[:16]
    mid = (model_id or "").strip() or "unknown"
    return {"model_label": mid, "answer_sha256_16": h_ans}
