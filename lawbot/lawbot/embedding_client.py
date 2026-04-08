"""OpenAI-compatible embedding calls (NVIDIA NIM, etc.)."""

from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from typing import Literal

from lawbot.config import settings
from lawbot.openai_client import get_openai_compatible_client
from lawbot.openai_retry import embeddings_create_with_retry

log = logging.getLogger(__name__)

# In-process LRU + TTL for embed_query (session RAG hot paths).
_embed_query_cache: OrderedDict[str, tuple[float, list[float]]] = OrderedDict()


def _nv_embed_extra(role: Literal["query", "passage"]) -> dict[str, str] | None:
    """NVIDIA nv-embedqa on integrate.api.nvidia.com requires ``input_type`` (not separate model ids)."""
    m = (settings.lawbot_embedding_model or "").strip()
    if "nv-embedqa" in m.lower():
        return {"input_type": role}
    return None


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Returns one embedding vector per input string (same order). Skips empty strings in API
    but pads with empty list for those indices — callers should filter empties before calling.
    """
    key = settings.openai_compatible_key()
    model = (settings.lawbot_embedding_model or "").strip()
    if not key or not model:
        raise RuntimeError("embedding model or API key not configured")
    non_empty: list[tuple[int, str]] = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
    if not non_empty:
        return [[] for _ in texts]
    client = get_openai_compatible_client()
    inputs = [t for _, t in non_empty]
    xb = _nv_embed_extra("passage")
    kwargs: dict = {"model": model, "input": inputs}
    if xb:
        kwargs["extra_body"] = xb
    resp = await embeddings_create_with_retry(client, **kwargs)
    by_idx: dict[int, list[float]] = {}
    for j, item in enumerate(resp.data or []):
        if j >= len(non_empty):
            break
        orig_i, _ = non_empty[j]
        vec = list(item.embedding) if item.embedding is not None else []
        by_idx[orig_i] = vec
    out: list[list[float]] = []
    for i in range(len(texts)):
        out.append(by_idx.get(i, []))
    return out


def _truncate_for_embed(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""
    max_c = max(256, int(getattr(settings, "session_rag_embed_max_chars", 1800) or 1800))
    if len(t) <= max_c:
        return t
    return t[:max_c]


def _embed_cache_get(cache_key: str) -> list[float] | None:
    ttl = float(getattr(settings, "session_rag_embed_cache_ttl_seconds", 300.0) or 0.0)
    if ttl <= 0:
        return None
    now = time.monotonic()
    stale_keys = [k for k, (exp, _) in _embed_query_cache.items() if exp < now]
    for k in stale_keys:
        _embed_query_cache.pop(k, None)
    ent = _embed_query_cache.get(cache_key)
    if not ent:
        return None
    exp, vec = ent
    if exp < now:
        _embed_query_cache.pop(cache_key, None)
        return None
    _embed_query_cache.move_to_end(cache_key)
    return vec


def _embed_cache_set(cache_key: str, vec: list[float]) -> None:
    ttl = float(getattr(settings, "session_rag_embed_cache_ttl_seconds", 300.0) or 0.0)
    max_entries = max(8, int(getattr(settings, "session_rag_embed_cache_max_entries", 256) or 256))
    if ttl <= 0:
        return
    now = time.monotonic()
    _embed_query_cache[cache_key] = (now + ttl, vec)
    _embed_query_cache.move_to_end(cache_key)
    while len(_embed_query_cache) > max_entries:
        _embed_query_cache.popitem(last=False)


async def embed_query(
    text: str,
    *,
    embed_ms_accum: dict[str, float] | None = None,
) -> list[float]:
    """
    Query embedding for session RAG. Optional ``embed_ms_accum`` (same dict across a turn) accumulates
    wall time in milliseconds for uncached API calls only (cache hits add 0).
    """
    t = _truncate_for_embed(text)
    if not t:
        return []
    key = settings.openai_compatible_key()
    model = (settings.lawbot_embedding_model or "").strip()
    if not key or not model:
        return []
    cache_key = hashlib.sha256(f"{model}\0{t}".encode()).hexdigest()
    hit = _embed_cache_get(cache_key)
    if hit is not None:
        return hit
    t_api = time.perf_counter()
    client = get_openai_compatible_client()
    xb = _nv_embed_extra("query")
    kwargs: dict = {"model": model, "input": [t]}
    if xb:
        kwargs["extra_body"] = xb
    resp = await embeddings_create_with_retry(client, **kwargs)
    if embed_ms_accum is not None:
        embed_ms_accum["embed_ms"] = float(embed_ms_accum.get("embed_ms", 0.0)) + (
            time.perf_counter() - t_api
        ) * 1000
    if not resp.data:
        return []
    item = resp.data[0]
    vec = list(item.embedding) if item.embedding is not None else []
    _embed_cache_set(cache_key, vec)
    return vec
