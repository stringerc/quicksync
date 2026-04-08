# Lawbot — project memory

Longer personal context lives in **`/Users/Apple/MEMORY.md`** (§ Lawbot). **This file** tracks **how to get back to a known-good setup** after changes.

---

## Working states (update after meaningful changes)

When something is verified end-to-end, **append a new dated block** below with: what you tested, exit codes, and any env notes (never paste secrets).

### Baseline — 2026-04-06 (verified)

**Run**

```bash
cd /Users/Apple/lawbot
source .venv/bin/activate
uvicorn lawbot.api.app:app --host 127.0.0.1 --port 8765
```

**Recovery if UI is 404 but `/health` works:** restart `uvicorn` (stale process may lack `/` and `/static/*`).

**Verify APIs**

```bash
python scripts/verify_apis.py
# expect exit 0 when NVIDIA + CourtListener + DB OK
```

**Verify UI + routes (no browser required)**

```bash
python -m unittest tests.test_ui_audit -v
# expect 7 tests OK
```

**Quick HTTP checks**

- `GET http://127.0.0.1:8765/` → 200 HTML (contains `sendBtn`)
- `GET http://127.0.0.1:8765/static/app.js` → 200
- `GET http://127.0.0.1:8765/health` → JSON `status: ok`
- `POST http://127.0.0.1:8765/v1/chat` with `{"message":"ping","session_id":null}` → JSON with `answer` or `error`

**Env (local only, gitignored)**

- `lawbot/.env`: `NVIDIA_API_KEY`, `COURTLISTENER_TOKEN`, optional Twilio/HUD
- NVIDIA key can match `~/.config/nvidia.env` pattern (OpenClaw stack)

**Repo note:** `lawbot/` is **not** its own git repo yet. To enable rollback-by-commit: `cd lawbot && git init`, commit after each verified baseline.

**Last messaging E2E (automated):** `verify_apis.py` exit 0; two `POST /v1/chat` turns on same `session_id` (follow-up recalled prior user text); `GET /` + `/static/app.js` 200; `tests.test_ui_audit` 7/7 OK.

**2026-04-06 — Retrieval gating:** Words like “testing” were used as the CourtListener search query and pulled unrelated cases (e.g. company names with “Testing”). Now `infer_research_query()` skips auto case search for smoke words / very short messages unless the optional **case-law search** field is filled. Response JSON includes `retrieval_skipped: true` when no search ran. **Restart uvicorn after backend changes** or the browser still hits old behavior.

**2026-04-06 — UI controls:** Checkbox **Search case law (CourtListener)** (`search_case_law`, default true; persisted in `localStorage`). Uncheck to force no CourtListener call. Optional **Jurisdiction** field saved to profile key `jurisdiction` and sent with each chat. Assistant meta can show **no case search** when `retrieval_skipped`.

**2026-04-06 — Empty vault anti-hallucination:** If CourtListener ran but returned **no chunks**, the app used to set `retrieval_skipped=false`, so the model wasn’t forced into “no sources” mode and the footer wrongly said “add a CourtListener token.” Models then invented case cites (e.g. Kellos) and “top attorney” briefs. Fixed: `empty_vault` + `EMPTY VAULT` user block, stricter system prompt, accurate footer (`query_executed` in research response), API field `vault_empty`.

**2026-04-06 — Intent (prestige openings):** `classify_simple_task` now treats **elite / top .01% appellate** lead-ins like **rewrite** when the message is long or filing-like (`lawbot/intent.py` + `test_prestige_opening_beats_buried_verify_in_appendix`). Verbatim benchmark ask: `docs/LAWBOT_QUALITY_BASELINE.md`. **Session verify:** `uvicorn` restarted on `127.0.0.1:8765` (`--reload`), `GET /health` 200, `python -m unittest discover` 88 OK, `scripts/verify_apis.py` exit 0.

**2026-04-06 — Strengthen = drafting-first (no audit stack):** `should_use_citation_audit` returns **False** for `strengthen_filing` so replies use conversational prompts + strengthen directive (not “Vault vs not” matrices). Long strengthen messages skip CourtListener unless `research_query` is set. `scripts/post_baseline_message.py` + `scripts/check_baseline_reply.py` for regression. `chat_service`: prestige note says keep **formal** court tone (not conversational); conversational sanitizer allows 16 paragraphs so lists are not cut off.

**2026-04-07 — Default `CHAT_MODEL` (NVIDIA):** **`meta/llama-3.1-405b-instruct`** for substantive research/strategy/drafting; **`CHAT_MODEL_FAST`** = `meta/llama-3.3-70b-instruct` for smoke/connectivity only (`lawbot/model_routing.py`). API model list: `GET /v1/models`. Response JSON includes `audit.chat_model_id` for the resolved tier.

---

## Quick reference

| Item | Value |
|------|--------|
| UI | `http://127.0.0.1:8765/` (not `file://`) |
| API docs | `/docs` |
| DB | `./data/lawbot.db` (from `LAWBOT_DB_PATH`) |
| **Quality baseline (initial ask → rubric)** | `docs/LAWBOT_QUALITY_BASELINE.md` + Cursor skill `lawbot-baseline-quality` (`.cursor/skills/lawbot-baseline-quality/SKILL.md`) |

---

## Baseline-ask quality loop

Freeze the **verbatim** first user message and success criteria in `docs/LAWBOT_QUALITY_BASELINE.md`. Use that file + the skill above to judge whether a reply matches the contract; extend `tests/test_intent.py` / `test_chat_task_integration.py` when you lock expected `task_hint` behavior. This is **alignment to your ask**, not a universal “IQ” score.

---

## OpenClaw, Hermes, and Cursor — who can do what

**OpenClaw** (your gateway, e.g. `127.0.0.1:18789` per `~/MEMORY.md`) is a **separate** runtime: Telegram/WhatsApp/Signal, tool profiles, and **your** skill packs under `~/.openclaw/skills/`. It is **not** automatically wired into **Cursor IDE** chats unless you add an MCP bridge or custom integration.

**Hermes (in this repo)** is **not** a Cursor skill file. In `docs/ARCHITECTURE.md` / `docs/OPENCLAW_BRIDGE.md` it means a **verification pattern**: a second pass that checks quotes against `allowed_chunk_ids` and response shape — deterministic, narrow scope. Implement that as code or an OpenClaw sub-agent if you want it automated.

**Cursor / Codex agents editing `lawbot/`** typically have: shell, file tools, and whatever **MCP servers** you enabled in Cursor (GitHub, Vercel, etc.). They do **not** inherit OpenClaw’s channel tools or browser automation unless you explicitly connect them.

**“Visual” UI checks from an assistant without a browser:**

- Automated: `python -m unittest tests.test_ui_audit -v`, `curl`/`GET` on `/`, `/static/*`, `POST /v1/chat`, `scripts/verify_apis.py`.
- Real browser (pixels, Copy button, layout): **you** open `http://127.0.0.1:8765/`, or configure an **OpenClaw** agent/tool that has **browser** capabilities (if your OpenClaw install exposes that) to hit the same URL — that flow is outside this repo unless you document your gateway tool name.

**Skills location (OpenClaw, not Cursor):** `~/.openclaw/skills/*/SKILL.md`. Example: `honesty-protocol` explicitly says not to claim browser control unless it is actually available — apply the same honesty in Cursor.

---

## For assistants / future sessions

After code changes that might break runtime:

1. Run `verify_apis.py` and `tests/test_ui_audit.py`.
2. Restart `uvicorn` and confirm `GET /` is 200.
3. **Append a new “Working state — YYYY-MM-DD”** subsection above with what passed.
4. For **true** visual confirmation of the web UI, use a human browser pass or an OpenClaw tool that can drive a browser — do not assume the Cursor agent has that unless MCP says so.
