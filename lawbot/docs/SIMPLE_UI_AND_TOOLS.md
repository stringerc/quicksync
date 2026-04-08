# Simple UI + progress stream + optional tools

## What the web app does now

- **One big box** (“Your question”) and **Ask Lawbot** — enough for most people.
- **Optional checkbox**: “Look up public court opinions” (CourtListener).
- **“More options”** is folded under `<details>` so power users can override search words, place, or memo mode.
- While waiting, the UI shows a **numbered checklist** of steps (read question → search / skip → sources count → write answer). This mirrors patterns users know from **Perplexity** (“Searching…”, “Reading sources…”) and from **agent-style** UIs that surface activity instead of a blank wait.

## API

- **`POST /v1/chat`** — same JSON body as before; returns the final JSON in one shot (good for OpenClaw, scripts, tests).
- **`POST /v1/chat/stream`** — same body; **`text/event-stream`** (SSE). Events:
  - `{"event":"step","message":"…"}` — user-facing line to append to the checklist.
  - `{"event":"complete","result":{...}}` — same object shape as `/v1/chat`.
  - `{"event":"error","message":"…"}` — failure.

## OpenClaw / other assistants

- Point tools at **`POST /v1/chat`** for a single JSON response (see `docs/OPENCLAW_BRIDGE.md`).
- If a client can consume SSE, it can use **`/v1/chat/stream`** to show progress in Telegram/WhatsApp-style messages (emit each `step` as a status line, then send `result.answer`).

## MCP in Cursor (optional)

Lawbot does **not** ship an MCP server. To wire **Cursor** to Lawbot:

1. Use a **generic HTTP MCP** or a tiny custom MCP that `POST`s to `http://127.0.0.1:8765/v1/chat` with your session id, **or**
2. Keep using the **browser UI** for humans and **curl/scripts** for automation.

Hermes-style **verification** (second pass on quotes) remains a **separate** job: implement in code or an OpenClaw sub-agent; see `docs/ARCHITECTURE.md`.
