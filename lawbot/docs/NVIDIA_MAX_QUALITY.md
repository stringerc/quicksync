# Lawbot — maximum quality on **NVIDIA only** (no Anthropic)

If your **only** LLM API is NVIDIA NIM (`OPENAI_BASE_URL` + `NVIDIA_API_KEY`), Lawbot is already built for that path. Nothing here requires Claude or another vendor.

## What actually raises “IQ” on your stack

1. **`CHAT_MODEL`** — Your **strongest** instruct model on the [NVIDIA catalog](https://build.nvidia.com/) (or `GET https://integrate.api.nvidia.com/v1/models` with your key). This is the default brain for substantive turns (`lawbot/model_routing.py`).

2. **`CHAT_MODEL_FAST`** — Only for **ping / connectivity / smoke** style messages. Keep it smaller/faster so trivial checks don’t queue behind huge models.

3. **`CHAT_MODEL_MAX`** (optional) — Third NVIDIA tier for **high-stakes** turns when you stay on NVIDIA only: document mode, citation audit, verify/strengthen tasks, or long messages (same thresholds as Anthropic escalation signals). Empty uses `CHAT_MODEL` only. Polish second pass intentionally stays on `CHAT_MODEL` for cost control.

4. **`LAWBOT_AUXILIARY_MODEL_TIER`** — `primary` (default) or `fast`.
   - **`primary`**: Reasoning scaffold, session compaction, and optional **draft judge** all use **`CHAT_MODEL`** — **highest quality**, more tokens/latency/cost.
   - **`fast`**: Those *extra* calls use **`CHAT_MODEL_FAST`** — cheaper; main answers still use `CHAT_MODEL` when the turn is substantive.

5. **Built-in pipelines (all NVIDIA)**  
   - Internal **reasoning JSON scaffold** before the main reply (`LAWBOT_REASONING_PASS=auto`).  
   - **Session memory** compaction into `sessions.summary` for long threads (`LAWBOT_SESSION_COMPACTION=auto`).  
   - Optional **polish second pass** (`lawbot/auto_quality.py`).  
   - **CourtListener** + citation vault for grounded quotes (`LAWBOT_QUALITY_BASELINE.md`).

6. **Session embedding RAG** (`LAWBOT_EMBEDDING_MODEL` + `LAWBOT_SESSION_RAG=auto`)  
   - After each turn, user + assistant text is chunked, embedded via the same OpenAI-compatible API as chat, and stored per session.  
   - On later turns, the current message is embedded and matched (cosine similarity) to prior chunks so the model sees **relevant earlier chat** alongside case-law chunks.  
   - **NVIDIA `nv-embedqa` models** require asymmetric `input_type` (`query` vs `passage`); Lawbot sends this automatically — do not use separate `-query`/`-passage` model suffixes on the API.  
   - If `LAWBOT_EMBEDDING_MODEL` is unset, session RAG stays off.

7. **CourtListener search cache** (`LAWBOT_CL_SEARCH_CACHE`, `LAWBOT_CL_SEARCH_CACHE_TTL_SECONDS`)  
   - Caches retrieval payloads by normalized query key to avoid duplicate searches within the TTL.

8. **Anthropic-related env vars** — **Ignore them** if you have no Anthropic key. They do nothing unless `ANTHROPIC_API_KEY` is set.

## Minimal `.env` for NVIDIA-only max IQ

```env
NVIDIA_API_KEY=your_key
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
CHAT_MODEL=meta/llama-3.1-405b-instruct
CHAT_MODEL_FAST=meta/llama-3.3-70b-instruct
LAWBOT_AUXILIARY_MODEL_TIER=primary
LAWBOT_REASONING_PASS=auto
LAWBOT_SESSION_COMPACTION=auto
# Optional: highest continuity — default in .env.example; verify embeddings with scripts/verify_apis.py.
# LAWBOT_EMBEDDING_MODEL=nvidia/nv-embedqa-e5-v5
```

Swap `CHAT_MODEL` when you confirm a **newer or stronger** model id from the catalog.

## Verify

```bash
python scripts/verify_apis.py
```

Exit 0 means NVIDIA + DB (and CourtListener if token set) respond.
