---
name: lawbot-verify
description: Run deterministic Lawbot checks (HTTP, Hermes, mock-LLM sanitize tests) against a live server.
---

# Lawbot verification (Hermes + OpenClaw)

Use this skill when the user wants to **verify Lawbot is healthy** after deploys or config changes — same checks as Cursor CI, runnable from **OpenClaw** (Telegram/WhatsApp/etc.) via a shell or HTTP tool.

## What gets verified

1. **`GET /health`** — API up, LLM backend reported.
2. **`GET /v1/health/deep`** — SQLite + **Hermes self-test** (no LLM): proves empty-vault leakage detection works.
3. **`POST /v1/hermes/check`** — Hermes endpoint accepts a JSON payload (typical `/v1/chat` shape) and returns `hermes_passed`.
4. **UI static assets** — `GET /`, `GET /static/app.js`.
5. **`POST /v1/chat`** — one live completion (`search_case_law: false`).
6. **`POST /v1/chat/stream`** — SSE `step` + `complete`.
7. **`tests.test_e2e_mock_llm_sanitize`** — proves toxic model output is stripped (no live model).

## Install (OpenClaw)

Copy this folder to your OpenClaw skills directory:

```bash
mkdir -p ~/.openclaw/skills
cp -R /path/to/lawbot/openclaw-skills/lawbot-verify ~/.openclaw/skills/lawbot-verify
```

Restart or reload OpenClaw so it picks up the skill.

## Run (from the machine where Lawbot runs)

Server must be listening (default `http://127.0.0.1:8765`):

```bash
cd /path/to/lawbot
./scripts/openclaw_lawbot_verify.sh
```

Or the underlying script with optional base URL:

```bash
BASE_URL=http://127.0.0.1:8765 ./scripts/verify_user_flow.sh
```

Exit code **0** = all checks passed. Non-zero = failure (see stderr).

## Optional: HTTP tool instead of shell

Register a tool that:

- `GET {BASE_URL}/v1/health/deep` — assert `hermes_self_test.clean_answer_passes` and `ocga_leak_fails_as_expected`.
- `POST {BASE_URL}/v1/hermes/check` with body from a saved `/v1/chat` response — assert `hermes_passed`.

Do **not** ask the LLM to “verify citations”; use these **deterministic** endpoints.

## Hermes vs Lawbot internals

- **Python** (`lawbot.hermes_verify`): schema, empty-vault leakage, quote-vs-vault checks.
- **API** (`POST /v1/hermes/check`): same logic for external agents (OpenClaw, CI, n8n).

See `docs/OPENCLAW_BRIDGE.md` and `docs/ARCHITECTURE.md`.
