"""
User-visible “thinking steps” density for streaming UI.

When a turn is clearly low-stakes (ping, meta-check, short general question without cites/tasks),
we collapse Perplexity-style step lines into a single calm state — closer to ChatGPT / Claude loading UX.
"""

from __future__ import annotations

from lawbot.answer_depth import BRIEF_MESSAGE_CHAR_MAX
from lawbot.intent import (
    CHAT_TASK_STRENGTHEN_FILING,
    CHAT_TASK_VERIFY_CITATIONS,
    is_smoke_test_message,
)


def compact_thinking_eligible(
    *,
    msg_stripped: str,
    meta_connectivity: bool,
    task_hint: str | None,
    review_audit_label: str,
    extracted_count: int,
    response_mode: str,
    explicit_research_query: str | None,
    force_authority_retrieval: bool,
) -> bool:
    """
    True → client should show minimal thinking UI; server suppresses granular on_step lines.

    Conservative: any specialized task, auto-audit, extracted cites, explicit research scope,
    or authority forcing uses full steps.
    """
    if meta_connectivity:
        return True
    if is_smoke_test_message(msg_stripped):
        return True
    if task_hint in (CHAT_TASK_VERIFY_CITATIONS, CHAT_TASK_STRENGTHEN_FILING):
        return False
    if review_audit_label == "auto":
        return False
    if extracted_count >= 1:
        return False
    if explicit_research_query and str(explicit_research_query).strip():
        return False
    if force_authority_retrieval:
        return False
    # Long-form document drafting: keep full progress visibility
    if (response_mode or "").strip().lower() == "document" and len(msg_stripped) > 120:
        return False
    n = len(msg_stripped)
    if n <= BRIEF_MESSAGE_CHAR_MAX and task_hint is None:
        return True
    return False
