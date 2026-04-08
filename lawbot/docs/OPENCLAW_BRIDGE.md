# OpenClaw bridge

OpenClaw should call this service over HTTP instead of inventing citations itself.

For how this relates to **coding agents**, **Hermes**, and what not to put in OpenClaw, see **`docs/DEVELOPER_WORKFLOW.md`** (section “OpenClaw and Hermes”).

## Tool definition (conceptual)

Register an HTTP tool or skill whose handler:

1. `POST /v1/chat` with JSON:
   - `message`: user text from the channel
   - `session_id`: stable id per chat (Telegram chat id, Signal peer, etc.)
   - `research_query`: optional shorter search string
   - `extra_chunk_ids`: optional list after user pastes Lexis excerpts via `/v1/citations/lexis-paste`

2. Display `answer` to the user. If `verification_ok` is false, prepend a warning.

## Hermes API (implemented)

Deterministic checks (Python module `lawbot.hermes_verify`) are exposed for agents and CI:

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/health/deep` | SQLite touch + Hermes self-test (no LLM). |
| `POST /v1/hermes/check` | Body = JSON object (typically a full `/v1/chat` response). Returns `hermes_passed`, `errors`, `warnings`, `checks`. |

**OpenClaw:** run `./scripts/openclaw_lawbot_verify.sh` (wraps `verify_user_flow.sh`) or copy `openclaw-skills/lawbot-verify/` to `~/.openclaw/skills/`.

## Base URL

Use your deployed URL (HTTPS) or `http://host.docker.internal:8765` if OpenClaw runs on the same machine.

For a **second pass** beyond the server’s inline quote checks, `POST /v1/hermes/check` with the `/v1/chat` JSON — or call `run_hermes_checks` from Python — instead of asking an LLM to “verify cites.”

## Channels from your phone

OpenClaw does **not** rely on carrier SMS for “text from anywhere”—use **Telegram** or **WhatsApp** (your syncscript setup) and route messages through this API. That matches the same **NVIDIA-backed** models configured in OpenClaw.

Use **Twilio** `/webhooks/twilio/sms` only when you need true SMS; this repo implements that webhook separately.
