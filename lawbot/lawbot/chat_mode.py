"""
Decide when to use full citation-audit prompts vs plain conversational replies (Claude-like).

Default: conversational — short, direct answers without vault boilerplate.
Escalate to citation audit when the user clearly brought citations, pasted a long filing, chose an API section,
or asked verify/strengthen. Retrieved chunks alone do **not** force audit (vague queries can return noisy hits).
"""

from __future__ import annotations

from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING, CHAT_TASK_VERIFY_CITATIONS
from lawbot.schemas import ChatIn

# Short messages without cite-like extractions stay conversational even if CourtListener returned chunks.
MIN_CHARS_FOR_CHUNK_TRIGGERED_AUDIT = 500


def should_use_citation_audit(
    body: ChatIn,
    extracted_count: int,
    task_hint: str | None,
    review_audit_label: str,
    vault_chunk_count: int,
) -> bool:
    """
    Return True for the full audit stack (strict empty-vault copy, EXTRACTED CITATIONS block, AUDIT_SYSTEM_APPEND).
    Return False for everyday chat: meta questions, greetings, simple how-tos without legal cites in text.

    **Strengthen / rewrite filings:** use conversational prompts + task directive only — not the audit stack.
    That avoids "Vault vs not" matrices and irrelevant retrieved opinions hijacking drafting feedback.
    Callers can still force section review via ``review_pass`` (appendix, part1, …).
    """
    rp = (body.review_pass or "").strip().lower()
    if rp and rp not in ("", "full", "none"):
        return True
    if task_hint == CHAT_TASK_STRENGTHEN_FILING:
        return False
    if task_hint == CHAT_TASK_VERIFY_CITATIONS:
        return True
    if review_audit_label == "auto":
        return True
    if extracted_count >= 1:
        return True
    msg = (body.message or "").strip()
    if vault_chunk_count > 0 and len(msg) >= MIN_CHARS_FOR_CHUNK_TRIGGERED_AUDIT:
        return True
    return False
