"""
Select OpenAI-compatible chat model: strongest by default for legal research / strategy / drafting;
lighter model only for obvious smoke/connectivity turns (latency).

When both NVIDIA/OpenAI-compatible and Anthropic keys are set, ``decide_llm_route`` chooses
per turn (escalation to Anthropic for high-stakes work in ``auto`` mode).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from lawbot.config import settings
from lawbot.intent import (
    CHAT_TASK_STRENGTHEN_FILING,
    CHAT_TASK_VERIFY_CITATIONS,
    is_smoke_test_message,
)

# Long pastes without explicit document mode still qualify for escalation in ``auto``.
_MIN_CHARS_FOR_AUTO_ESCALATION = 1600


@dataclass(frozen=True)
class LLMRoute:
    """Resolved backend and model id for one turn."""

    backend: Literal["openai_compatible", "anthropic"]
    model_id: str
    #: True when Anthropic is used while an OpenAI-compatible key is also configured (for billing caps).
    escalation: bool


def decide_llm_route(
    *,
    user_message: str,
    meta_connectivity_hint: bool,
    document_mode: bool,
    audit_mode: bool,
    task_hint: str | None,
    polish_pass_only: bool,
    anthropic_budget_ok: bool,
) -> LLMRoute:
    """
    Choose OpenAI-compatible vs Anthropic.

    - Only OpenAI-compatible key → ``openai_compatible`` + tiered model id.
    - Only Anthropic key → ``anthropic`` + ``ANTHROPIC_MODEL`` (no escalation flag).
    - Both keys → ``LAWBOT_ANTHROPIC_ESCALATION`` (``never`` / ``auto`` / ``always``) + daily cap.
    """
    has_oc = bool(settings.openai_compatible_key())
    has_anth = settings.anthropic_configured()

    if not has_oc and not has_anth:
        raise ValueError("no LLM backend configured")

    if not has_oc and has_anth:
        return LLMRoute("anthropic", (settings.anthropic_model or "").strip() or "claude-sonnet-4-20250514", False)

    rm = (user_message or "")[:120_000]
    oc_model = select_chat_model(
        user_message=rm,
        meta_connectivity_hint=meta_connectivity_hint,
        document_mode=document_mode,
        audit_mode=audit_mode,
        task_hint=task_hint,
        polish_pass_only=polish_pass_only,
    )

    if has_oc and not has_anth:
        return LLMRoute("openai_compatible", oc_model, False)

    mode = (settings.anthropic_escalation_mode or "auto").strip().lower()
    if mode not in ("auto", "never", "always"):
        mode = "auto"

    esc_model = settings.resolved_anthropic_escalation_model()

    if mode == "never":
        return LLMRoute("openai_compatible", oc_model, False)

    if mode == "always":
        if not anthropic_budget_ok:
            return LLMRoute("openai_compatible", oc_model, False)
        return LLMRoute("anthropic", esc_model, True)

    # auto
    if meta_connectivity_hint:
        return LLMRoute("openai_compatible", oc_model, False)
    if polish_pass_only:
        return LLMRoute("openai_compatible", oc_model, False)

    msg = (user_message or "").strip()
    n = len(msg)
    want_escalate = (
        document_mode
        or audit_mode
        or task_hint == CHAT_TASK_STRENGTHEN_FILING
        or task_hint == CHAT_TASK_VERIFY_CITATIONS
        or n >= _MIN_CHARS_FOR_AUTO_ESCALATION
    )
    if not want_escalate or not anthropic_budget_ok:
        return LLMRoute("openai_compatible", oc_model, False)

    return LLMRoute("anthropic", esc_model, True)


def select_chat_model(
    *,
    user_message: str,
    meta_connectivity_hint: bool,
    document_mode: bool = False,
    audit_mode: bool = False,
    task_hint: str | None = None,
    polish_pass_only: bool = False,
) -> str:
    """
    Return the NVIDIA (or compatible) model id for this turn.

    - **Fast (`CHAT_MODEL_FAST`)** — connectivity checks and smoke messages (`ping`, `hi`, …).
    - **Max (`CHAT_MODEL_MAX`)** — when set and this turn is high-stakes (document mode,
      citation audit, verify/strengthen tasks, or long message), use max tier; otherwise
      **Primary (`CHAT_MODEL`)**. Polish-only second passes use primary, not max, to control cost.
    - If `CHAT_MODEL_FAST` is unset, fast tier falls back to primary.
    """
    high = (settings.chat_model or "").strip()
    fast = (settings.chat_model_fast or "").strip() or high
    max_m = (settings.chat_model_max or "").strip()
    if meta_connectivity_hint or is_smoke_test_message(user_message):
        return fast
    if polish_pass_only:
        return high
    if max_m and max_m != high:
        msg = (user_message or "").strip()
        n = len(msg)
        want_max = (
            document_mode
            or audit_mode
            or task_hint == CHAT_TASK_STRENGTHEN_FILING
            or task_hint == CHAT_TASK_VERIFY_CITATIONS
            or n >= _MIN_CHARS_FOR_AUTO_ESCALATION
        )
        if want_max:
            return max_m
    return high
