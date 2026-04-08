"""
Hermes-style verification: deterministic checks on Lawbot chat responses.

Use after /v1/chat (or via POST /v1/hermes/check) — narrow scope, no LLM reasoning.
Keep leakage patterns aligned with lawbot.chat_service empty-vault guardrails.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import sqlite3

from lawbot.citation_vault import CitationVault, verify_quotes_in_vault

# When vault_empty, user-facing answer must not contain these (model memory / meta leaks).
_EMPTY_VAULT_LEAKAGE = re.compile(
    r"O\.C\.G\.A\.|"
    r"verified cases and laws|"
    r"top\s*0\.01|"
    r"elite\s+attorney|"
    r"top\s+appellate\s+attorney|"
    r"SOURCE\s+CHUNKS|"
    r"without relying on the allowed chunk|"
    r"allowed\s+chunk\s+ids?",
    re.IGNORECASE,
)

_QUOTE_TAG = re.compile(r"<quote\s+chunk=", re.IGNORECASE)

# Obvious placeholder chunk ids (must not reach users when vault is in play).
_CHUNK_PLACEHOLDER = re.compile(
    r"chk_[Xx?]{3,}|chk_TBD|chunk\s+id\s+TBD|chk_XXXXX",
    re.IGNORECASE,
)


@dataclass
class HermesReport:
    """Result of run_hermes_checks."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    checks: dict[str, Any] = field(default_factory=dict)


def _schema_issues(d: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). session_id optional (warn if missing — partial payloads)."""
    issues: list[str] = []
    warns: list[str] = []
    if not isinstance(d, dict):
        return (["payload must be a JSON object"], [])
    if "error" in d and d["error"]:
        return ([], [])
    for key in ("answer", "verification_ok"):
        if key not in d:
            issues.append(f"missing key: {key}")
    if "answer" in d and d["answer"] is not None and not isinstance(d["answer"], str):
        issues.append("answer must be a string when present")
    if "verification_errors" not in d:
        issues.append("missing key: verification_errors")
    if "session_id" not in d:
        warns.append("session_id missing (ok for partial replay checks)")
    ve = d.get("verification_errors")
    if ve is not None and not isinstance(ve, list):
        issues.append("verification_errors must be a list when present")
    vo = d.get("verification_ok")
    if vo is not None and not isinstance(vo, bool):
        issues.append("verification_ok must be boolean when present")
    return (issues, warns)


def _vault_empty_flag(d: dict[str, Any]) -> bool:
    if "vault_empty" in d and d["vault_empty"] is not None:
        return bool(d["vault_empty"])
    audit = d.get("audit") or {}
    ids = audit.get("vault_chunk_ids")
    if isinstance(ids, list):
        return len(ids) == 0
    return True


def _chunk_ids(d: dict[str, Any]) -> list[str]:
    audit = d.get("audit") or {}
    raw = audit.get("vault_chunk_ids")
    if isinstance(raw, list):
        return [str(x) for x in raw]
    raw = d.get("vault_chunk_ids")
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return []


def verify_empty_vault_leakage(answer: str, vault_empty: bool) -> list[str]:
    if not vault_empty or not (answer or "").strip():
        return []
    errs: list[str] = []
    if _QUOTE_TAG.search(answer):
        errs.append("empty vault: answer contains <quote> tags (quotes require vault chunks)")
    if _EMPTY_VAULT_LEAKAGE.search(answer):
        errs.append("empty vault: answer contains banned citation/meta pattern (O.C.G.A., SOURCE CHUNKS, top 0.01%, etc.)")
    return errs


def verify_placeholder_chunk_syntax(answer: str) -> list[str]:
    if not (answer or "").strip():
        return []
    if _CHUNK_PLACEHOLDER.search(answer):
        return ["answer contains placeholder chunk id pattern (chk_XXXX / TBD)"]
    return []


def verify_verification_consistency(verification_ok: bool, verification_errors: list[str] | None) -> list[str]:
    errs = list(verification_errors or [])
    if errs and verification_ok:
        return ["verification_ok is True but verification_errors is non-empty"]
    return []


def run_hermes_checks(conn: sqlite3.Connection | None, response: dict[str, Any]) -> HermesReport:
    """
    Run all deterministic Hermes checks on a chat response dict (same shape as /v1/chat).

    conn: required for quote-vs-vault checks when vault_chunk_ids non-empty; may be None to skip DB checks.
    """
    errors: list[str] = []
    warnings: list[str] = []
    checks: dict[str, Any] = {}

    schema_errs, schema_warns = _schema_issues(response)
    checks["schema_ok"] = len(schema_errs) == 0
    errors.extend(schema_errs)
    warnings.extend(schema_warns)

    if response.get("error"):
        return HermesReport(passed=len(errors) == 0, errors=errors, warnings=warnings, checks=checks)

    raw_ans = response.get("answer")
    answer = raw_ans if isinstance(raw_ans, str) else ""
    vault_empty = _vault_empty_flag(response)
    chunk_ids = _chunk_ids(response)
    checks["vault_empty"] = vault_empty
    checks["vault_chunk_ids_count"] = len(chunk_ids)

    vo = bool(response.get("verification_ok", False))
    verrs = list(response.get("verification_errors") or [])
    cons = verify_verification_consistency(vo, verrs)
    checks["verification_consistency_ok"] = len(cons) == 0
    errors.extend(cons)

    leak = verify_empty_vault_leakage(answer, vault_empty)
    checks["empty_vault_leakage_ok"] = len(leak) == 0
    errors.extend(leak)

    ph = verify_placeholder_chunk_syntax(answer)
    checks["no_placeholder_chunk_ids"] = len(ph) == 0
    errors.extend(ph)

    if conn is not None and chunk_ids:
        vault = CitationVault(conn)
        q_ok, q_errs = verify_quotes_in_vault(answer, vault, chunk_ids)
        checks["quote_substrings_match_vault"] = q_ok
        if not q_ok:
            errors.extend([f"quote check: {e}" for e in q_errs])
        elif not vo:
            warnings.append("verification_ok is False but quote substrings matched vault (check server logic)")
    elif chunk_ids and conn is None:
        warnings.append("vault_chunk_ids present but no DB connection — skipped quote-vs-vault check")

    passed = len(errors) == 0
    return HermesReport(passed=passed, errors=errors, warnings=warnings, checks=checks)


def hermes_report_to_dict(r: HermesReport) -> dict[str, Any]:
    return {
        "hermes_passed": r.passed,
        "errors": r.errors,
        "warnings": r.warnings,
        "checks": r.checks,
    }
