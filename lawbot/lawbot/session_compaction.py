"""
Phase 4 — Session memory: periodic LLM compression of older turns into ``sessions.summary``.

Non-destructive: messages stay in SQLite; the summary augments what the model sees for long threads.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any

from lawbot.config import settings
from lawbot.openai_client import get_openai_compatible_client
from lawbot.openai_retry import chat_completions_create_with_retry
from lawbot.memory import MemoryStore
from lawbot.observability import log_llm_event

_COMPACT_SYSTEM = """You compress prior chat for legal-work continuity (not legal advice).
Output ONLY valid JSON with keys:
- "durable_facts": string[] (up to 12 bullets: parties, case names/numbers if stated, key dates, amounts, relief sought, deadlines the user mentioned)
- "open_loops": string[] (up to 6 unfinished questions or tasks the user raised)
- "jurisdiction_notes": string (one sentence: state/court if known, else "unspecified")

Do not invent facts. If the transcript is empty or noise, return empty arrays and a short jurisdiction_notes."""

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.I)


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


async def maybe_compact_session(conn, mem: MemoryStore, session_id: str) -> bool:
    """
    If message count crosses threshold, summarize older messages into sessions.summary.
    Returns True if compaction ran successfully.
    """
    if (settings.lawbot_session_compaction or "auto").strip().lower() != "auto":
        return False
    if not settings.openai_compatible_key():
        return False

    n = mem.count_messages(session_id)
    th = settings.compaction_message_threshold
    every = max(1, settings.compaction_every_n_messages)
    if n < th:
        return False
    # Fire after threshold, then every `every` messages (e.g. 48, 72, 96…)
    if (n - th) % every != 0:
        return False

    msgs = mem.recent_messages(session_id, limit=400)
    if len(msgs) < 30:
        return False

    # Oldest portion: all but last 24 messages in chronological order
    chronological = list(reversed(msgs))
    if len(chronological) <= 24:
        return False
    old = chronological[:-24]
    lines: list[str] = []
    for m in old[-120:]:
        role = m.get("role", "?")
        content = (m.get("content") or "")[:3500]
        lines.append(f"{role}: {content}")
    blob = "\n\n".join(lines)
    if len(blob) < 200:
        return False

    model = settings.auxiliary_chat_model_id()
    t0 = time.perf_counter()
    client = get_openai_compatible_client()
    try:
        msg = await chat_completions_create_with_retry(
            client,
            model=model,
            max_tokens=900,
            temperature=0.1,
            messages=[
                {"role": "system", "content": _COMPACT_SYSTEM},
                {"role": "user", "content": "PRIOR TRANSCRIPT (oldest portion, truncated):\n\n" + blob[:100_000]},
            ],
        )
    except Exception as e:
        log_llm_event(
            {
                "event": "session_compaction_failed",
                "session_id": session_id,
                "error": str(e)[:300],
            }
        )
        return False

    raw = (msg.choices[0].message.content or "").strip()
    parsed = _extract_json(raw)
    if not parsed:
        return False
    try:
        block = json.dumps(parsed, ensure_ascii=False, indent=2)[:10_000]
    except (TypeError, ValueError):
        return False

    prev = (mem.get_session_summary(session_id) or "").strip()
    merged = (prev + "\n\n---\n" + block).strip() if prev else block
    merged = merged[:24_000]
    mem.set_session_summary(session_id, merged)
    dt = (time.perf_counter() - t0) * 1000
    log_llm_event(
        {
            "event": "session_compaction",
            "session_id": session_id,
            "message_count": n,
            "duration_ms": round(dt, 2),
            "model": model,
        }
    )
    return True
