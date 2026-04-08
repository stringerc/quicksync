"""
Phase 3 — Internal reasoning scaffold (no UI toggle): JSON outline before the main reply.

Uses ``settings.auxiliary_chat_model_id()`` (default: **primary** = ``CHAT_MODEL`` on NVIDIA for max IQ).
Set ``LAWBOT_AUXILIARY_MODEL_TIER=fast`` to use ``CHAT_MODEL_FAST`` for these passes only.
Skipped for polish-only turns and connectivity checks.
"""

from __future__ import annotations

import json
import re
from typing import Any

from lawbot.config import settings
from lawbot.openai_client import get_openai_compatible_client
from lawbot.openai_retry import chat_completions_create_with_retry
from lawbot.intent import CHAT_TASK_STRENGTHEN_FILING, CHAT_TASK_VERIFY_CITATIONS

_MIN_SUBSTANTIVE = 1200

_REASONING_SYSTEM = """You are a drafting assistant (not a lawyer). Output ONLY a single JSON object (no markdown fences) with keys:
- "issues": string[] (1–6 short issue or question statements implied by the user text)
- "facts_to_confirm": string[] (dates, amounts, party names, docket numbers that may need verification)
- "structure_suggestion": string[] (1–5 bullet labels for how to organize the reply, e.g. "Jurisdiction", "Facts", "Relief")
- "caution": string (one sentence: uncertainty, missing facts, or need for licensed counsel)

Do not include legal citations or case names. Do not output any text outside the JSON object."""

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.I)


def should_run_reasoning_pass(
    *,
    user_message: str,
    document_mode: bool,
    audit_mode: bool,
    task_hint: str | None,
    meta_connectivity_hint: bool,
    polish_pass_only: bool,
    answer_depth: str = "standard",
) -> bool:
    if (settings.lawbot_reasoning_pass or "auto").strip().lower() != "auto":
        return False
    if answer_depth == "brief":
        return False
    if meta_connectivity_hint or polish_pass_only:
        return False
    msg = (user_message or "").strip()
    if document_mode or audit_mode:
        return True
    if len(msg) < 80:
        return False
    if task_hint in (CHAT_TASK_STRENGTHEN_FILING, CHAT_TASK_VERIFY_CITATIONS):
        return True
    if len(msg) >= _MIN_SUBSTANTIVE:
        return True
    return False


def _extract_json(raw: str) -> dict[str, Any] | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        o = json.loads(raw)
        return o if isinstance(o, dict) else None
    except json.JSONDecodeError:
        pass
    m = _JSON_FENCE.search(raw)
    if m:
        try:
            o = json.loads(m.group(1).strip())
            return o if isinstance(o, dict) else None
        except json.JSONDecodeError:
            pass
    return None


async def build_reasoning_scaffold(
    *,
    user_message: str,
    profile: dict[str, str],
) -> str | None:
    """Return a user-block fragment for the main model, or None on failure/skip."""
    if not settings.openai_compatible_key():
        return None
    client = get_openai_compatible_client()
    model = settings.auxiliary_chat_model_id()
    prof = "\n".join(f"{k}: {v}" for k, v in list(profile.items())[:12])
    body = (user_message or "")[:24_000]
    user_txt = f"USER PROFILE (if any):\n{prof}\n\nUSER MESSAGE:\n{body}"
    try:
        msg = await chat_completions_create_with_retry(
            client,
            model=model,
            max_tokens=700,
            temperature=0.15,
            messages=[
                {"role": "system", "content": _REASONING_SYSTEM},
                {"role": "user", "content": user_txt},
            ],
        )
    except Exception:
        return None
    raw = (msg.choices[0].message.content or "").strip()
    parsed = _extract_json(raw)
    if not parsed:
        return None
    try:
        compact = json.dumps(parsed, ensure_ascii=False, indent=2)[:6000]
    except (TypeError, ValueError):
        return None
    return (
        "INTERNAL REASONING SCAFFOLD (JSON — use to structure your reply; do not paste this block verbatim "
        "to the user and do not call it 'scaffold' or 'internal'):\n"
        f"{compact}"
    )
