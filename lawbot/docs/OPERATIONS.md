# Lawbot — operations (Phase 8)

## Environment

- **Secrets:** Only in `.env` or a host secret manager — never commit keys.
- **Database:** `LAWBOT_DB_PATH` (default `./data/lawbot.db`). Back up this file for session history, vault chunks, and (if used) daily API usage counters.
- **NVIDIA-only deployments:** See **`docs/NVIDIA_MAX_QUALITY.md`**. Set `LAWBOT_AUXILIARY_MODEL_TIER=primary` so reasoning, compaction, and draft judge use your strongest `CHAT_MODEL`.

## Rate limiting

- `LAWBOT_RATE_LIMIT_PER_MINUTE` — requests per client IP per minute to `POST /v1/chat` and `POST /v1/chat/stream`. **`0` = disabled** (default).

## Quality features (Phases 3–6)

| Variable | Meaning |
|----------|---------|
| `LAWBOT_REASONING_PASS` | `auto` (default) or `never` — internal JSON scaffold before main reply (OpenAI-compatible fast tier). |
| `LAWBOT_SESSION_COMPACTION` | `auto` or `never` — periodic compression of older messages into `sessions.summary`. |
| `LAWBOT_COMPACTION_MESSAGE_THRESHOLD` | First compaction when message count reaches this (default `48`). |
| `LAWBOT_COMPACTION_EVERY_N_MESSAGES` | Repeat compaction every N messages after threshold (default `24`). |
| `LAWBOT_ANTHROPIC_THINKING` | `auto` or `never` — extended thinking on high-stakes Anthropic turns when the API accepts it. |
| `LAWBOT_ANTHROPIC_THINKING_BUDGET_TOKENS` | Thinking budget (default `8000`). |
| `LAWBOT_SESSION_RAG` | `auto` or `never` — embedding retrieval over prior messages in the same session (requires `LAWBOT_EMBEDDING_MODEL`). |
| `LAWBOT_EMBEDDING_MODEL` | OpenAI-compatible embedding model id (same `OPENAI_BASE_URL` as chat); empty disables session RAG. |
| `LAWBOT_SESSION_RAG_TOP_K` | Max prior-chat excerpts to inject (default `4`). |
| `LAWBOT_CL_SEARCH_CACHE` | `true`/`false` — cache CourtListener retrieval by query key (default on). |
| `LAWBOT_CL_SEARCH_CACHE_TTL_SECONDS` | Cache TTL in seconds (default `3600`). |
| `CHAT_MODEL_MAX` | Optional stronger NVIDIA model id for high-stakes turns (document/audit/long/verify tasks); empty = use `CHAT_MODEL` only. |
| `LAWBOT_LLM_HTTP_RETRIES` | Backoff retries for transient OpenAI-compatible **chat + embeddings** errors (default `4`; `1` = single attempt only). |

## TLS and deployment

- Terminate TLS at your reverse proxy (nginx, Caddy, Cloudflare) or platform (Railway, Fly, etc.).
- Set `PUBLIC_BASE_URL` for Twilio webhooks.

## Incident checklist

1. Check `/health` and `/v1/health/deep`.
2. Review `lawbot.llm` JSON logs for `llm_complete` / failures.
3. Verify `.env` keys and quotas (NVIDIA, Anthropic, CourtListener).
4. Restore DB from backup if corruption suspected.

## Restore test

```bash
cp /backup/lawbot.db ./data/lawbot.db
python -c "from lawbot.db import connect; from lawbot.config import settings; c=connect(settings.lawbot_db_path); c.execute('SELECT 1'); c.close(); print('ok')"
```
