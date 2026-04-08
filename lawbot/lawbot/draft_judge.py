"""
Optional second rubric: small LLM call that scores clarity/structure on a 1–5 scale.

Separate from draft_quality (deterministic). Higher cost/latency — opt-in via ``draft_judge`` on chat.

Uses ``settings.auxiliary_chat_model_id()`` when OpenAI-compatible / NVIDIA is configured (see ``LAWBOT_AUXILIARY_MODEL_TIER``); otherwise Anthropic Messages API if that is the only backend.
"""

from __future__ import annotations

import json
import re

from lawbot.anthropic_client import get_anthropic_async_client
from lawbot.config import settings
from lawbot.openai_client import get_openai_compatible_client
from lawbot.openai_retry import chat_completions_create_with_retry

_JUDGE_SYSTEM = (
    "You score assistant drafts for writing quality only — not legal correctness. "
    "Reply with a single JSON object and no other text."
)

_JUDGE_USER_TEMPLATE = """Rate this assistant draft.

Output exactly one JSON object with integer fields clarity and structure (each 1-5), and string one_line (max 120 chars).
Example shape: {"clarity": 4, "structure": 3, "one_line": "Clear but dense in section II."}

Criteria:
- clarity: readable sentences, minimal jargon bloat, coherent flow
- structure: headings, lists, paragraphing where appropriate for length

Draft:
---
{DRAFT}
---
"""


_JSON_OBJ = re.compile(r"\{[^{}]*\}")


async def run_draft_judge_rubric(answer: str) -> dict[str, object]:
    """
    Returns ``{"clarity": int, "structure": int, "one_line": str, "parse_ok": bool}``
    or ``{"error": str}`` on failure.
    """
    text = (answer or "").strip()
    if not text:
        return {"error": "empty_answer", "parse_ok": False}

    draft = text[:14_000]

    if settings.openai_compatible_key():
        return await _judge_openai_compatible(draft)
    if settings.anthropic_configured():
        return await _judge_anthropic(draft)
    return {"error": "no_llm_backend", "parse_ok": False}


async def _judge_openai_compatible(draft: str) -> dict[str, object]:
    client = get_openai_compatible_client()
    model = settings.auxiliary_chat_model_id()
    user_msg = _JUDGE_USER_TEMPLATE.replace("{DRAFT}", draft)
    msg = await chat_completions_create_with_retry(
        client,
        model=model,
        max_tokens=220,
        temperature=0.2,
        messages=[
            {"role": "system", "content": _JUDGE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )
    raw = (msg.choices[0].message.content or "").strip()
    return _finish_judge_parse(raw, judge_model=model)


async def _judge_anthropic(draft: str) -> dict[str, object]:
    client = get_anthropic_async_client()
    model = (settings.anthropic_model or "").strip() or "claude-sonnet-4-20250514"
    user_msg = _JUDGE_USER_TEMPLATE.replace("{DRAFT}", draft)
    msg = await client.messages.create(
        model=model,
        max_tokens=220,
        temperature=0.2,
        system=_JUDGE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw_parts: list[str] = []
    for block in msg.content:
        if block.type == "text":
            raw_parts.append(block.text)
    raw = "".join(raw_parts).strip()
    return _finish_judge_parse(raw, judge_model=model)


def _finish_judge_parse(raw: str, *, judge_model: str) -> dict[str, object]:
    parsed = _parse_judge_json(raw)
    if parsed:
        parsed["parse_ok"] = True
        parsed["judge_model"] = judge_model
        return parsed
    return {"error": "json_parse_failed", "raw_excerpt": raw[:400], "parse_ok": False}


def _parse_judge_json(raw: str) -> dict[str, object] | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    m = _JSON_OBJ.search(raw)
    if not m:
        return None
    try:
        o = json.loads(m.group(0))
        if isinstance(o, dict) and "clarity" in o and "structure" in o:
            return {
                "clarity": int(o["clarity"]),
                "structure": int(o["structure"]),
                "one_line": str(o.get("one_line", ""))[:200],
            }
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return None
