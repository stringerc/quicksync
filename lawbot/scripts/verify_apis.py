#!/usr/bin/env python3
"""
Verify Lawbot external APIs: NVIDIA (OpenAI-compatible), CourtListener, optional Anthropic.

Run from repo root:
  cd /Users/Apple/lawbot && source .venv/bin/activate && python scripts/verify_apis.py

Exit codes: 0 = all probes that apply passed, 1 = failure or misconfiguration.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Repo root = parent of scripts/
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.chdir(ROOT)


def _mask(s: str, keep: int = 4) -> str:
    if not s:
        return "(empty)"
    if len(s) <= keep * 2:
        return "***"
    return s[:keep] + "…" + s[-keep:]


async def probe_nvidia() -> tuple[bool, str]:
    from lawbot.config import settings

    key = settings.openai_compatible_key()
    if not key:
        return False, "skip (no NVIDIA_API_KEY / OPENAI_COMPATIBLE_API_KEY)"
    try:
        from lawbot.llm_client_cleanup import aclose_if_real
        from openai import AsyncOpenAI

        client = AsyncOpenAI(base_url=settings.openai_base_url, api_key=key)
        try:
            r = await client.chat.completions.create(
                model=settings.chat_model,
                max_tokens=16,
                messages=[{"role": "user", "content": 'Reply with exactly: OK'}],
            )
            text = (r.choices[0].message.content or "").strip()
            if not text:
                return False, "empty completion"
            return True, f"ok ({settings.chat_model}) preview={text[:40]!r}"
        finally:
            await aclose_if_real(client)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


async def probe_embeddings() -> tuple[bool, str]:
    """Session RAG uses OpenAI-compatible embeddings.create on the same base URL."""
    from lawbot.config import settings

    if not settings.openai_compatible_key():
        return False, "skip (no NVIDIA_API_KEY / OPENAI_COMPATIBLE_API_KEY)"
    model = (settings.lawbot_embedding_model or "").strip()
    if not model:
        return False, "skip (LAWBOT_EMBEDDING_MODEL unset — session RAG off)"
    try:
        from lawbot.embedding_client import embed_texts

        vecs = await embed_texts(["lawbot embedding probe"])
        if not vecs or not vecs[0]:
            return False, "empty embedding vector"
        return True, f"ok ({model}, dim={len(vecs[0])})"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


async def probe_courtlistener() -> tuple[bool, str]:
    from lawbot.config import settings

    token = settings.courtlistener_token
    if not token:
        return False, "skip (no COURTLISTENER_TOKEN)"
    try:
        import httpx

        headers = {
            "Authorization": f"Token {token}",
            "User-Agent": "Lawbot-verify_apis/1.0 (courtlistener API)",
            "Accept": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            r = await client.get(
                "https://www.courtlistener.com/api/rest/v4/search/",
                params={"q": "miranda", "type": "o", "order_by": "score desc"},
                headers=headers,
            )
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
        data = r.json()
        n = len(data.get("results") or [])
        return True, f"ok (sample search returned {n} opinion hit(s))"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


async def probe_anthropic() -> tuple[bool, str]:
    from lawbot.config import settings

    if not settings.anthropic_api_key:
        return False, "skip (no ANTHROPIC_API_KEY)"
    try:
        import anthropic

        from lawbot.llm_client_cleanup import aclose_if_real

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        try:
            msg = await client.messages.create(
                model=settings.anthropic_model,
                max_tokens=16,
                messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            )
            text = ""
            for block in msg.content:
                if block.type == "text":
                    text += block.text
            text = text.strip()
            return True, f"ok preview={text[:40]!r}"
        finally:
            await aclose_if_real(client)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def probe_sqlite() -> tuple[bool, str]:
    from lawbot.config import settings
    from lawbot.db import connect

    try:
        conn = connect(settings.lawbot_db_path)
        conn.execute("SELECT 1")
        conn.close()
        return True, f"ok ({settings.lawbot_db_path})"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


async def main() -> int:
    # Load .env via pydantic when importing settings
    from lawbot.config import settings

    print("Lawbot API verification")
    print(f"  Repo: {ROOT}")
    print(f"  LLM backend: {settings.llm_backend() or '(none — set NVIDIA_API_KEY)'}")
    if settings.openai_compatible_key():
        print(f"  NVIDIA / OpenAI key: {_mask(settings.openai_compatible_key())}")
        print(f"  OPENAI_BASE_URL: {settings.openai_base_url}")
        print(f"  CHAT_MODEL: {settings.chat_model}")
        print(f"  CHAT_MODEL_FAST: {settings.chat_model_fast}")
        if (settings.chat_model_max or "").strip():
            print(f"  CHAT_MODEL_MAX (high-stakes NVIDIA tier): {settings.chat_model_max}")
        print(f"  Auxiliary tier (reasoning/compaction/judge): {settings.lawbot_auxiliary_model_tier} → {settings.auxiliary_chat_model_id()}")
        emb = (settings.lawbot_embedding_model or "").strip()
        if emb:
            print(f"  LAWBOT_EMBEDDING_MODEL (session RAG): {emb}")
            if "nv-embedqa" in emb.lower():
                print("    (NVIDIA nv-embedqa: uses input_type=query|passage on embeddings API)")
    print(f"  CourtListener search cache: enabled={settings.cl_search_cache_enabled} ttl_s={settings.cl_search_cache_ttl_seconds}")
    if settings.anthropic_api_key:
        print(f"  Anthropic key: {_mask(settings.anthropic_api_key)}")
        print(f"  ANTHROPIC_MODEL: {settings.anthropic_model}")
        if settings.both_llm_backends_configured():
            print(
                f"  Dual-backend: escalation={settings.anthropic_escalation_mode!r} "
                f"model={settings.resolved_anthropic_escalation_model()}"
            )
    if settings.courtlistener_token:
        print(f"  CourtListener token: {_mask(settings.courtlistener_token)}")
    print()

    results: list[tuple[str, bool, str]] = []

    ok, msg = probe_sqlite()
    results.append(("SQLite (local DB)", ok, msg))
    ok, msg = await probe_nvidia()
    results.append(("NVIDIA / OpenAI-compatible chat", ok, msg))
    ok, msg = await probe_embeddings()
    results.append(("Embeddings (session RAG)", ok, msg))
    ok, msg = await probe_courtlistener()
    results.append(("CourtListener search API", ok, msg))
    ok, msg = await probe_anthropic()
    results.append(("Anthropic (fallback)", ok, msg))

    hard_fail = False
    for name, passed, detail in results:
        if passed:
            status = "PASS"
        elif "skip" in detail.lower():
            status = "SKIP"
        else:
            status = "FAIL"
            hard_fail = True
        print(f"  [{status}] {name}: {detail}")

    if settings.llm_backend() is None:
        print("\n  ERROR: No LLM key configured — set NVIDIA_API_KEY in .env")
        hard_fail = True

    print()
    if hard_fail:
        print("Result: FAILED (see above)")
        return 1
    print("Result: OK — configured APIs respond as expected")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
