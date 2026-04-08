# Architecture — Lawbot

## North star (technically honest)

1. **Top attorneys** combine judgment, ethics, courtroom skill, and verified research. Software can excel at **organization, recall, retrieval, and consistency**—not at replacing bar-licensed representation.
2. **“Never a wrong citation”** is a **systems property**, not a model property. Achieve it by:
   - **Retrieve** authoritative text (API, licensed database, or user-uploaded excerpt).
   - **Store** verbatim chunks in a **citation vault** with stable IDs and source URLs.
   - **Constrain** generation so the model may only quote from the vault (or explicitly label anything else as *proposed language, verify*).
   - **Verify** after generation: quoted strings must **match** vault text (with normalization); otherwise block or flag.

Large language models **will** hallucinate citations if not constrained. This design assumes that.

## Stack roles

| Layer | Role |
|--------|------|
| **OpenClaw** | Gateway: Telegram, WhatsApp, Signal, BlueBubbles (iMessage), Discord, WebChat, etc. Multi-channel access from your phone without building each client. |
| **Hermes (your usage)** | Implemented as **`lawbot.hermes_verify`** + **`POST /v1/hermes/check`**: deterministic second pass (schema, empty-vault leakage, quote-vs-vault). Optional OpenClaw skill `openclaw-skills/lawbot-verify/`. **Not** a separate magic legal brain. |
| **Python service (this repo)** | Citation vault, memory, research orchestration, webhooks (Twilio), AR/HUD WebSocket feed. |
| **NVIDIA NIM (OpenAI-compatible)** | Default: `https://integrate.api.nvidia.com/v1` + tiered models: `CHAT_MODEL` (strongest default, `meta/llama-3.1-405b-instruct`) for substantive turns; `CHAT_MODEL_FAST` for smoke/connectivity only — see `lawbot/model_routing.py`. List models with `GET /v1/models`. Same class of setup as OpenClaw in syncscript (`NVIDIA_API_KEY`). Reasoning **only** over retrieved vault chunks + your stored facts. |
| **Anthropic API** | If **only** Anthropic is configured, all turns use it. If **both** NVIDIA/OpenAI-compatible and Anthropic keys are set, see **`docs/LAWBOT_PARITY_ROADMAP.md` §7** — per-turn escalation (`LAWBOT_ANTHROPIC_ESCALATION`) instead of ignoring Anthropic. |

This repo calls the **OpenAI Python SDK** against an OpenAI-compatible base URL (NVIDIA by default). Anthropic remains available as an alternate backend.

## Citation sources: LexisNexis vs Justia vs others

| Source | Verbatim in automation? | Notes |
|--------|---------------------------|--------|
| **LexisNexis** | Only with **your** enterprise/API access and license terms. | Typical path: API or export → ingest into vault with Lexis document IDs. No public scraper; contract-bound. |
| **Justia** | Partially: many opinions are public domain; **mirror into your vault** via permitted means. | Prefer **CourtListener** (API) for many U.S. opinions—often the same underlying text with stable citations. |
| **CourtListener** | Strong default for **U.S. case law** retrieval in this stack. | Free API token; good for machine-readable opinions. |

**Rule:** For any filing, **re-check** citations in the authoritative system your counsel uses (often Lexis/Westlaw). The vault is only as good as its pipeline.

### LexisNexis (including Lexis+ AI) vs this stack

Lexis bundles **proprietary collections**, **editorial content**, and **their** assistant on **their** data. You cannot replicate their full catalog without licenses—but you can aim to be **stronger on dimensions that matter for trust**:

| Dimension | Lexis+ AI (typical) | This design |
|-----------|---------------------|-------------|
| **Citation integrity** | Vendor-controlled | **Vault + mandatory quotes + automated string check** on what *you* retrieved |
| **Transparency** | Closed corpus + black-box answers | **Open retrieval pipeline** (e.g. CourtListener URLs) you can audit |
| **Cost** | Subscription | **NVIDIA free-tier style keys** + open APIs where possible |
| **Customization** | Product UX | **Your** memory, timelines, OpenClaw channels, HUD feed |

“Better than Lexis” in practice means **better for your workflow on verified primary text**, not claiming every secondary source Lexis sells.

## Memory (precise, no repetition)

Three layers (all implemented in this repo’s SQLite schema):

1. **Profile** — durable user/case preferences, jurisdictions, parties, docket IDs.
2. **Timeline** — dated events with provenance (*what you said*, *document uploaded*, *retrieval*).
3. **Working set** — last N turns + compaction summaries **you control** (no silent amnesia).

Optional later: embedding index (e.g. Chroma/pgvector) for **document** search—not for “remembering law” without retrieval.

## Phone access “from anywhere”

**Option A (recommended):** OpenClaw + **Telegram** (fastest) or **WhatsApp** (QR pairing) so the same brain answers on your phone.

**Option B:** **Twilio SMS** → this API’s `/webhooks/twilio/sms` (implemented). Reliable globally; costs per message.

**Option C:** **BlueBubbles** on Mac + OpenClaw for **iMessage**-like UX (see OpenClaw docs).

## HUD / glasses

There is no single “best” universal HUD for legal work today; choices are **device-specific**:

| Approach | Best for |
|----------|----------|
| **Phone + earpiece + OpenClaw voice** | Lowest friction; use voice notes and short summaries. |
| **AR glasses with browser or companion app** (e.g. some Android-based AR) | Show **bullet summary + next question** from a WebSocket (`/ws/hud`) fed by this service. |
| **Smart glasses with phone as compute** | Same: phone runs HTTPS + WebSocket to your backend; glasses display read-only cards. |

**Implementation here:** `GET /ws/hud` WebSocket pushes the latest **session summary + open risks + next actions** for a paired device. Pairing via `HUD_TOKEN` in env.

## Security and ethics

- Encrypt **data at rest** (disk) and **in transit** (TLS).
- Separate **test** and **prod** vaults; never mix client matters.
- Log **access**; support **delete/export** for your data.
- **Privilege:** This README does not create attorney–client privilege. That is a **relationship and context** matter—consult a human attorney.

## End-to-end build phases (nothing left as “TODO architecture”)

1. **Core API** — health, chat, memory CRUD *(done in scaffold)*.
2. **Citation vault + CourtListener** *(scaffold + token)*.
3. **Twilio webhook** *(scaffold)*.
4. **HUD WebSocket** *(scaffold)*.
5. **OpenClaw bridge** — HTTP tool calling `/v1/chat` *(documented + contract)*.
6. **Production** — TLS, secrets manager, backups, Lexis pipeline *(your license)*.

Phases 1–5 are in-repo; phase 6 is deployment and licensed data feeds.
