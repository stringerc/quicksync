"""
Automatic answer-depth routing (no extra UI).

**Goal:** Match response shape to task stakes — short, direct answers for simple questions;
full memos, multi-step reasoning, and vault-grounded analysis when the turn is clearly
substantive (filings, audits, long pastes, loaded sources, explicit research scope).

**Principles (conservative, quality-first):**
- Prefer **false negatives** (treat as standard/deep) over false positives (brief when user needed depth).
- **Deep** when any high-stakes signal fires — never cap tokens or ask for brevity.
- **Brief** only for short, general chat with **no** loaded vault chunks, **no** citation audit,
  **no** specialized task (strengthen/verify), and **no** obvious legal-substance hooks.
- **Meta-connectivity** messages keep their existing dedicated instructions; depth stays ``standard``.

This mirrors common product patterns: intent classification + resource-aware generation,
without exposing toggles to end users (see also ``model_routing``, ``retrieval_coherence``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING, CHAT_TASK_VERIFY_CITATIONS, message_suggests_substantive_legal_topic

AnswerDepthLevel = Literal["brief", "standard", "deep"]


@dataclass(frozen=True)
class AnswerDepth:
    level: AnswerDepthLevel
    reason: str


# Tunable thresholds — err on the side of deeper answers.
BRIEF_MESSAGE_CHAR_MAX = 520
_MAX_CHARS_FOR_BRIEF = BRIEF_MESSAGE_CHAR_MAX
_MIN_CHARS_FORCE_DEEP = 1400
_MIN_VAULT_CHUNKS_FORCE_DEEP = 2


def classify_answer_depth(
    *,
    message: str,
    meta_connectivity: bool,
    document_mode: bool,
    use_citation_audit: bool,
    task_hint: str | None,
    chunk_ids: list[str],
    explicit_research_query: str | None,
    force_authority_retrieval: bool,
) -> AnswerDepth:
    """
    Return depth level and a short machine reason for telemetry and audits.
    """
    msg = (message or "").strip()
    n = len(msg)
    vault_n = len(chunk_ids)

    if meta_connectivity:
        return AnswerDepth("standard", "meta_connectivity")

    if document_mode:
        return AnswerDepth("deep", "document_mode")

    if use_citation_audit:
        return AnswerDepth("deep", "citation_audit")

    if task_hint == CHAT_TASK_STRENGTHEN_FILING:
        return AnswerDepth("deep", "task_strengthen_filing")

    if task_hint == CHAT_TASK_VERIFY_CITATIONS:
        return AnswerDepth("deep", "task_verify_citations")

    if force_authority_retrieval:
        return AnswerDepth("deep", "force_authority_retrieval")

    if explicit_research_query and str(explicit_research_query).strip():
        return AnswerDepth("deep", "explicit_research_query")

    if n >= _MIN_CHARS_FORCE_DEEP:
        return AnswerDepth("deep", "long_message")

    if vault_n >= _MIN_VAULT_CHUNKS_FORCE_DEEP:
        return AnswerDepth("deep", "multiple_vault_chunks")

    if message_suggests_substantive_legal_topic(msg):
        return AnswerDepth("standard", "legal_substance_hint")

    if vault_n >= 1:
        return AnswerDepth("standard", "has_vault_chunks")

    # Eligible for brief: short, no task, no vault, no legal hook above
    if n <= BRIEF_MESSAGE_CHAR_MAX and task_hint is None:
        return AnswerDepth("brief", "short_general_no_vault")

    return AnswerDepth("standard", "default")


BRIEF_ANSWER_INSTRUCTION = (
    "ANSWER DEPTH — SHORT QUESTION: The user asked a compact question in plain language. "
    "Give a **direct, accurate** answer first (what a careful reader needs to know right away), "
    "then only as much context as helps — about **3–10 sentences**, or a **short bullet list** if clearer. "
    "Do **not** write a legal memorandum, long essay, or exhaustive survey unless the question "
    "clearly requires comparing multiple rules or jurisdictions. "
    "If important caveats exist (e.g. facts matter, local rules vary), state them in **one or two** sentences."
)
