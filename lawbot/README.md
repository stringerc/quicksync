# Lawbot — grounded legal research assistant

This project implements a **retrieval-first** architecture: the model may only cite text that was **fetched and stored** in a citation vault, then verified. That is how you approach “no wrong citations” in software—not by trusting memorization.

## What this is / is not

- **Is:** A research and drafting assistant with structured memory, SMS access, and hooks for OpenClaw and AR companions.
- **Is not:** A lawyer, law firm, or substitute for licensed counsel. Outputs are for research and preparation; **verify everything** before court or filings.

## Quick start

```bash
cd /Users/Apple/lawbot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: NVIDIA_API_KEY (same as OpenClaw / NGC), COURTLISTENER_TOKEN, optional TWILIO_* for SMS
```

### Launch (recommended)

**One command** — runs automated gates (golden drafts + full unit tests + live API probes when a key is set), then starts the server:

```bash
bash scripts/launch.sh
```

Or with Make: `make launch`

- **Fast iteration** (skip preflight): `SKIP_PREFLIGHT=1 bash scripts/launch.sh` or `make serve`
- **Preflight only** (no server): `bash scripts/preflight_launch.sh` or `make preflight`
- **LAN / tunnel:** `LAWBOT_HOST=0.0.0.0 LAWBOT_PORT=8765 bash scripts/launch.sh`

**Manual uvicorn** (same defaults as `scripts/dev_server.sh`):

```bash
uvicorn lawbot.api.app:app --host 0.0.0.0 --port 8765 --reload
```

**Web UI:** open **`http://127.0.0.1:8765/`** in a browser while the server is running. The page streams **step-by-step progress** while it works (same idea as Perplexity-style status lines). Integrators can use **`POST /v1/chat`** (one JSON) or **`POST /v1/chat/stream`** (SSE); see **`docs/SIMPLE_UI_AND_TOOLS.md`**.

Health check: `GET http://127.0.0.1:8765/health`

**Verify external APIs (NVIDIA, CourtListener, DB):** with `.env` filled in, run:

```bash
python scripts/verify_apis.py
```

Exit code `0` means probes passed; it performs a **tiny** LLM completion and one **CourtListener** search (not full `/v1/chat`).

**Verify UI routes and DOM wiring** (static files, `/`, `/health`, `/docs`, `/v1/chat` smoke):

```bash
python -m unittest tests.test_ui_audit -v
```

**End-to-end with the server already running** (health, Hermes, `/v1/chat`, stream, mock E2E):

```bash
BASE_URL=http://127.0.0.1:8765 ./scripts/verify_user_flow.sh
```

Use the app only at **`http://127.0.0.1:8765/`** (or the same host/port as the server). Opening `index.html` as a **file** will break `fetch()` to `/health` and `/v1/chat`.

## Phone / messaging

**Preferred:** Use **OpenClaw** (Telegram/WhatsApp/Signal/BlueBubbles) from your syncscript setup and add an HTTP tool to `POST /v1/chat`—no SMS fees, same NVIDIA-backed models.

**Optional:** **Twilio SMS** — point the incoming webhook to `https://<your-domain>/webhooks/twilio/sms` (ngrok/Cloudflare Tunnel in dev).

## OpenClaw

OpenClaw runs as the **messaging and tool-calling shell**. Point a custom tool or skill at this API’s `/v1/chat` (see `docs/ARCHITECTURE.md`).

## Docs

- `docs/ARCHITECTURE.md` — full system design, citation integrity, Lexis/Justia, HUD options.
- `docs/NVIDIA_MAX_QUALITY.md` — **NVIDIA-only** setup: strongest models, auxiliary tier, what to ignore if you have no Anthropic key.
- `docs/DEVELOPER_WORKFLOW.md` — **Contributors:** Claude Code / IDE agents, lint + Bandit, optional pre-commit, PR checklist (no runtime overhead for users).

Project root **`CLAUDE.md`** gives agents short context for this repo (not loaded by the server).

**Cursor:** project rules live in **`.cursor/rules/`** (see `docs/DEVELOPER_WORKFLOW.md`). Optional **`.vscode/settings.json`** points Python at `.venv` when you create it.
