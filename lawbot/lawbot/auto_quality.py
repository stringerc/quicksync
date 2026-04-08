"""
When to run an extra polish pass without requiring UI toggles or API flags.

Default bias: **quality over cost** — err toward running polish whenever the turn is
substantive (long paste, filing help, cite verification, or full citation-audit mode).
Only trivial / connectivity-style turns stay single-pass.
"""

from __future__ import annotations

from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING, CHAT_TASK_VERIFY_CITATIONS

# Below this length, polish rarely helps (single line / ping) — avoids double LLM on noise.
_MIN_SUBSTANTIVE_USER_CHARS = 80

# Pastes or drafts at or above this length get polish without needing a special task.
# Kept below chat_turn’s long-drafting skip (2800) so more “real work” messages get a second pass.
_MIN_CHARS_LONG_PASTE = 1600


def resolve_polish_second_pass(
    *,
    requested: bool,
    message: str,
    task_hint: str | None,
    use_citation_audit: bool,
    meta_connectivity: bool,
    retrieval_skipped: bool = False,
) -> tuple[bool, str | None]:
    """
    Return (run_polish, reason).

    ``reason`` is ``"user"`` when the client set ``polish_second_pass``; otherwise an ``auto_*`` tag, or ``None``.
    """
    if meta_connectivity:
        return (False, None)
    if requested:
        return (True, "user")

    msg = (message or "").strip()
    n = len(msg)

    if task_hint == CHAT_TASK_STRENGTHEN_FILING:
        return (True, "auto_strengthen_filing")
    if task_hint == CHAT_TASK_VERIFY_CITATIONS:
        return (True, "auto_verify_citations")
    # Short question with "case lookup" off: one LLM pass is enough (saves latency).
    if retrieval_skipped and not use_citation_audit and n < 500:
        return (False, "auto_skip_quick_no_case_lookup")
    if n >= _MIN_CHARS_LONG_PASTE:
        return (True, "auto_long_message")
    # Full citation-audit stack: second pass tightens redundancy and headings.
    if use_citation_audit and n >= _MIN_SUBSTANTIVE_USER_CHARS:
        return (True, "auto_citation_audit")

    return (False, None)
