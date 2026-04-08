# Lawbot — Parity & Excellence Roadmap (Exhaustive Resource Map)

**Document type:** Canonical program roadmap (strategy + execution + measurement).  
**Audience:** Builders operating this repository and its deployments.  
**Status:** Living document — revise when capabilities, budgets, or APIs change.  
**Scope:** Match or exceed *interactive legal-research and drafting quality* available from leading consumer assistants (e.g. Claude-class UX) **without** relying on “trust the model’s memory” for citations — while honoring **retrieval-first** and **zero new UI toggles** (automatic routing, heuristics, server defaults only).

**Legal:** This software does not provide legal advice. Outputs require human counsel and verification before filing or court use.

---

## 1. Purpose and success definition

### 1.1 What “highest measurable IQ output” means here

“IQ” is **not** a literal psychometric score. In this program it means **operationalized quality** on a fixed rubric, reproducible across releases:

| Metric family | What we measure | How |
|---------------|-----------------|-----|
| **Citation integrity** | No invented or unverified quotes when vault is non-empty; Hermes blocks empty-vault leakage | `lawbot/hermes_verify.py`, `/v1/hermes/check`, automated tests |
| **Draft structure** | Headings, issue framing, completeness vs golden fixtures | `lawbot/draft_quality_gate.py`, `tests/test_golden_drafts.py`, `scripts/ci_quality.sh` |
| **Task adherence** | Follows explicit user instructions (e.g. strengthen filing, audit mode) | Golden fixtures + intent tests (`lawbot/intent.py`, `tests/test_intent.py`) |
| **Regression safety** | No silent degradation on fixed prompts | `docs/LAWBOT_QUALITY_BASELINE.md`, CI artifacts (`draft-quality-golden.jsonl`) |
| **Latency tier compliance** | Smoke/connectivity uses fast path; substantive work uses strongest model path | `lawbot/model_routing.py`, health JSON |
| **Reasoning depth (proxy)** | Multi-pass polish when substantive; optional future judge scores | `lawbot/auto_quality.py`, `lawbot/polish_pass.py`, `lawbot/draft_judge.py` |

**Definition of done (program level):** Every phase below has **acceptance criteria** that are testable or observable; “feel better” is never sufficient alone.

### 1.2 Non-negotiable product constraints

1. **No new user-facing toggles** for “quality mode” — quality is **default** + **server-side** routing (`polish_second_pass` may exist as API for integrators; web UI bias is automatic — see `lawbot/auto_quality.py`).
2. **Citation integrity is a systems property** — see `docs/ARCHITECTURE.md`.
3. **Multi-provider (implemented):** When **both** NVIDIA/OpenAI-compatible and Anthropic keys are set, Lawbot can **escalate** high-stakes turns to Anthropic per `LAWBOT_ANTHROPIC_ESCALATION` — see `lawbot/model_routing.decide_llm_route` and `docs/LAWBOT_PARITY_ROADMAP.md` §7. Health still reports **configured** backends; each chat response includes the **actual** `llm_backend` used for that turn.

---

## 2. Resource audit — everything we can exhaust

This section inventories **repository**, **runtime**, **external services**, **integrations**, **evaluation assets**, and **human/organizational** constraints. Each subsection ends with **exhaustion moves**: how to squeeze maximum value from that resource.

### 2.1 Repository (code + tests + scripts)

| Asset | Location | Current role | Exhaustion moves |
|-------|----------|--------------|-------------------|
| Core chat pipeline | `lawbot/chat_service.py` | OpenAI-compatible + Anthropic backends, prompts, token limits, polish | Profile every branch; add provider-specific tuning; structured logging for A/B |
| Turn orchestration | `lawbot/chat_turn.py` | Retrieval, audit mode, document mode, task hints, polish resolution | Expand heuristics; add trace IDs for eval replay |
| Intent / tasks | `lawbot/intent.py` | Smoke detection, task hints | Richer classification without UI (length + pattern + profile) |
| Model routing | `lawbot/model_routing.py` | Fast vs strong NVIDIA models | Add **third tier** (e.g. “max quality” model id) via env only, still no UI |
| Auto polish | `lawbot/auto_quality.py` | When second pass runs | Tune thresholds using logged `reason` tags + metrics |
| Polish pass | `lawbot/polish_pass.py` | Second LLM pass | Swap model for polish-only; add judge-before-send optional path |
| Draft judge | `lawbot/draft_judge.py` | JSON scoring | OpenAI-compatible fast tier when available; else Anthropic; calibrate vs human scores |
| Draft quality gate | `lawbot/draft_quality_gate.py` | Deterministic checks | Add jurisdiction-specific rules (opt-in via profile keys, not new toggles) |
| Schemas | `lawbot/schemas.py` | Request/response contracts | Versioned API for integrators |
| Hermes | `lawbot/hermes_verify.py` | Post-generation verification | Expand rules for new failure modes discovered in eval |
| Citation vault | `lawbot/citation_vault.py` | Persist chunks | Better dedup, chunking strategy, embedding-backed retrieval later |
| CourtListener | `lawbot/providers/courtlistener.py` | Case law retrieval | Max out query patterns; cache responses; monitor rate limits |
| Citation extract / audit retrieval | `lawbot/citation_extract.py`, `lawbot/audit_retrieval.py` | Audit workflows | Broader citation patterns; parallel queries |
| Memory store | `lawbot/memory.py` | Sessions, messages, profile | Compaction policies; summarization model calls; export |
| DB schema | `lawbot/db.py` | SQLite tables | Migrations; optional Postgres for multi-tenant later |
| Gwinnett helpers | `lawbot/gwinnett_magistrate.py` | Local procedure templates | More courts via data-driven config files |
| Document review | `lawbot/document_review.py` | Section hints | Deeper structure analysis |
| Research orchestration | `lawbot/research.py` | CourtListener retrieval for queries | Query expansion, caching |
| Citation-audit gating | `lawbot/chat_mode.py` | When strict audit stack applies | Tune thresholds without UI |
| Vault footers / flags | `lawbot/vault_flags.py` | Empty-vault messaging | Consistency with Hermes |
| HUD broadcast | `lawbot/hud_broadcast.py` | Session summary to WebSocket | Align summary quality with chat |
| Usage limits / DB | `lawbot/usage_limits.py`, `lawbot/db.py` | Daily escalation counts | Cost caps |
| LLM observability | `lawbot/observability.py` | Structured JSON lines for each LLM call | Dashboards, A/B, audits |
| API surface | `lawbot/api/app.py` | REST, WS, static UI | Rate limits, auth, observability |
| Static UI | `lawbot/static/*` | Chat UX | Streaming UX, accessibility, print — **no new quality toggles** |
| OpenClaw skill | `openclaw-skills/lawbot-verify/SKILL.md` | External verification | Keep in sync with Hermes contract |
| Tests | `tests/**` | Regression | Expand golden sets; property tests for sanitization |
| CI | `.github/workflows/lawbot-ci.yml` | Quality gate + unittest | Add secrets for optional live-LLM nightly job (non-blocking) |
| Scripts | `scripts/*.py`, `scripts/*.sh` | API verify, baselines, smoke | Nightly benchmarks; cost reports |

### 2.2 Environment variables (configuration surface)

| Variable | Purpose | Exhaustion moves |
|----------|---------|------------------|
| `NVIDIA_API_KEY` / `OPENAI_COMPATIBLE_API_KEY` | Primary LLM | Rate-limit awareness; model list refresh via `GET /v1/models`; cost telemetry |
| `OPENAI_BASE_URL` | Host (default NVIDIA NIM) | Try alternate compliant hosts if needed for redundancy |
| `CHAT_MODEL` | Strong instruct model | Periodic catalog review; A/B on staging |
| `CHAT_MODEL_FAST` | Smoke/low-latency | Keep minimal — only connectivity |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | Anthropic path; with both keys, escalation — see §7 | **Escalation model** via `ANTHROPIC_ESCALATION_MODEL` (optional); `LAWBOT_ANTHROPIC_ESCALATION`, `LAWBOT_MAX_ANTHROPIC_ESCALATIONS_PER_DAY` |
| `COURTLISTENER_TOKEN` | Opinion retrieval | Exhaust pagination patterns; store more raw text in vault |
| `LAWBOT_DB_PATH` | SQLite | Backup job; WAL mode; integrity checks |
| `TWILIO_*`, `PUBLIC_BASE_URL` | SMS | Same chat pipeline — ensure parity with web |
| `HUD_TOKEN` | WebSocket HUD | Session summaries pushed to AR — keep summary quality aligned with chat |

### 2.3 External APIs (third parties)

| API | Used when | Limits / notes | Exhaustion moves |
|-----|-----------|----------------|------------------|
| NVIDIA NIM (OpenAI-compatible) | Default | Quotas, model catalog changes | Script: `scripts/verify_apis.py`; automated model list diff in CI (read-only) |
| Anthropic | No compatible key | Billing | Use for **quality reference** runs + optional routing for high-stakes turns |
| CourtListener | Research path | Token | Batch retrieval for known docket lists; cache aggressively |
| Twilio | SMS webhook | Per-message cost | Prefer OpenClaw channels for volume |

### 2.4 Integrations

| Integration | Role | Exhaustion moves |
|-------------|------|------------------|
| **OpenClaw** | Multi-channel gateway to `/v1/chat` | Document tool contract; retries; session stickiness |
| **Cursor MCP servers** (GitHub, Vercel, Supabase, etc.) | Dev velocity, deployment | Not runtime for Lawbot — use for **shipping** this roadmap faster |
| **Hermes / OpenClaw skill** | External verification | Single source of truth in `hermes_verify`; skill mirrors |

### 2.5 Evaluation and data assets

| Asset | Location | Exhaustion moves |
|-------|----------|------------------|
| Quality baseline narrative | `docs/LAWBOT_QUALITY_BASELINE.md` | Anchor all “did we regress” debates |
| Golden JSONL output | CI artifact `draft-quality-golden.jsonl` | Trend lines over time |
| Golden fixtures | `tests/fixtures/golden/` | Add more jurisdictions and tasks |
| Baseline reply samples | `docs/LAST_LAWBOT_BASELINE_REPLY*.json` | Refresh after major model changes |
| Taste matrix | `scripts/taste_prompts.json`, `scripts/run_taste_matrix.py` | Periodic human rating sessions |

### 2.6 Human and organizational resources

| Resource | Implication for roadmap |
|----------|-------------------------|
| **Solo operator + mission-mode execution** | Roadmap must be **chunkable** into clear missions with acceptance tests |
| **Budget sensitivity** (historically tight per `USER.md`) | **Cost governance** (§11) is a first-class workstream; “exhaust resources” may mean **time and attention**, not unbounded APIspend — **explicit budget ceiling** should be set per deployment |
| **Custody / legal context** | Highest-stakes threads must get **maximum verification**, not maximum verbosity |

---

## 3. Current capability matrix (honest snapshot)

| Dimension | Strong today | Gap vs “best class” |
|-----------|--------------|---------------------|
| **Citation integrity mechanics** | Vault + Hermes + audit modes | Scale of retrieved corpus; licensed secondary sources |
| **Model strength (default)** | Large instruct via NVIDIA (`405b` class) | No “extended thinking” API in this stack unless Anthropic (or other) is wired for those turns |
| **Multi-pass** | Auto polish for substantive turns | Polish model same family — may need **stronger second-pass model** |
| **Backend selection** | OpenAI-compatible **or** Anthropic, not both | **Resolved (v2):** `decide_llm_route` — NVIDIA default + Anthropic escalation for high-stakes turns when both keys set |
| **Evaluation** | Deterministic gates + golden tests | Sparse **live** LLM eval in CI (by design) — add **scheduled** jobs |
| **Memory** | SQLite sessions + profile; session embedding RAG for prior chat; compaction summary | Vector RAG for **uploaded long documents** in-repo remains optional future scope |

---

## 4. Architectural principles (strict)

1. **Retrieval-first** for any claim that looks like a citation or quote.
2. **Automatic quality** over manual modes — `lawbot/auto_quality.py` is the pattern.
3. **Observable** — every auto decision should log a **machine-readable reason** (polish already does this).
4. **Testable** — new behavior ships with tests or golden updates.
5. **Security** — tokens in env only; no client-side secret storage; privilege warnings in docs.

---

## 5. Master roadmap — phased delivery

Each phase lists **deliverables**, **acceptance criteria**, and **dependencies**. Phases can overlap in engineering time but **order** respects technical dependencies.

### Phase 0 — Baseline lock (continuous)

- **Deliverables:** CI green; `scripts/ci_quality.sh` passes; `docs/LAWBOT_QUALITY_BASELINE.md` current.
- **Acceptance:** No merge without draft gate + golden tests; `unittest` discover passes.
- **Dependencies:** None.

### Phase 1 — Observability and measurement **(implemented)**

- **Deliverables:** Structured **JSON** log lines (`lawbot/observability.py`) for **phase** (primary/polish), **backend**, **model id**, **latency**, **token usage** when the provider returns it.
- **Acceptance:** Can answer “what model answered this turn?” from logs alone.
- **Dependencies:** Phase 0.

### Phase 2 — Multi-provider orchestration **(implemented)**

- **Deliverables:** `decide_llm_route()` — with **both** keys: default **NVIDIA**; **escalate** to Anthropic on high-stakes signals (`document_mode`, `audit_mode`, strengthen/verify tasks, long messages); **polish** second pass stays on OpenAI-compatible by default (cost); daily cap via SQLite + `LAWBOT_MAX_ANTHROPIC_ESCALATIONS_PER_DAY` (`-1` = unlimited).
- **Acceptance:** Unit tests for routing + usage limits; `.env.example` documents all flags.
- **Dependencies:** Phase 1; `lawbot/config.py`, `lawbot/model_routing.py`, `lawbot/chat_service.py`, `lawbot/usage_limits.py`, `lawbot/db.py`.

### Phase 3 — Reasoning depth **(implemented)**

- **Deliverables:** `lawbot/reasoning_depth.py` — internal JSON **reasoning scaffold** (fast OpenAI-compatible call) before main `run_chat` when `LAWBOT_REASONING_PASS=auto`; streaming step `reasoning` / “Structuring issues and facts…”. **Anthropic extended thinking** (`thinking` + `budget_tokens`) on high-stakes Anthropic turns when `LAWBOT_ANTHROPIC_THINKING=auto`, with API fallback if unsupported.
- **Acceptance:** Response includes `reasoning_pass_used`; logs include `anthropic_thinking_fallback` when needed.
- **Dependencies:** Phase 2.

### Phase 4 — Context and memory at scale **(implemented)**

- **Deliverables:** `lawbot/session_compaction.py` — LLM compaction into `sessions.summary`. **`lawbot/session_rag.py`** — embedding retrieval over prior messages in-session (`LAWBOT_EMBEDDING_MODEL`, NVIDIA `input_type` handled in `lawbot/embedding_client.py`). **Upload / PDF vault RAG** remains optional future (out of scope unless product adds upload pipeline).
- **Acceptance:** `MemoryStore.count_messages`; compaction logged as `session_compaction`; session RAG covered by integration with `retrieve_session_context` / `ingest_turn` in `chat_turn.py`.
- **Dependencies:** Phase 1.

### Phase 5 — Retrieval maximization **(implemented — baseline)**

- **Deliverables:** `lawbot/retrieval_query.py` — jurisdiction-aware `augment_courtlistener_query` + `dedupe_chunks`; **`lawbot/research.py`** CourtListener path; **`lawbot/cl_cache.py`** query-key cache; **`lawbot/model_routing.py`** — optional **`CHAT_MODEL_MAX`** third tier for high-stakes **NVIDIA-only** turns (same signals as Anthropic escalation, without leaving NVIDIA). Lexis/docket-specific pre-fetch workflows remain product-specific increments.
- **Acceptance:** `tests/test_retrieval_query.py`, `tests/test_cl_cache.py`, routing tests for `CHAT_MODEL_MAX`.
- **Dependencies:** Phase 0.

### Phase 6 — Verification hardening **(implemented)**

- **Deliverables:** Hermes `verify_placeholder_chunk_syntax` — placeholder chunk ids (`chk_XXXXX`, TBD).
- **Acceptance:** `tests/test_hermes_verify.py` placeholder case.
- **Dependencies:** Phase 0.

### Phase 7 — Product polish **(implemented — baseline)**

- **Deliverables:** Mobile overflow CSS for `pre`/`code`; static UI served from `lawbot/static/`; streaming steps for chat. Further UX (themes, a11y audits) is ongoing product work, not blocking “core complete.”
- **Acceptance:** `tests/test_ui_audit.py` green.
- **Dependencies:** Phase 0.

### Phase 8 — Operational excellence **(implemented — baseline)**

- **Deliverables:** `lawbot/rate_limit.py` + middleware on `/v1/chat` and `/v1/chat/stream` (`LAWBOT_RATE_LIMIT_PER_MINUTE`, `0` = off). **`docs/OPERATIONS.md`** — backups, rate limit, env matrix, restore snippet, incident checklist.
- **Acceptance:** `tests/test_rate_limit.py`.
- **Dependencies:** Deployment target chosen.

**v1 program closure (this repo):** Phases **0–8** baseline deliverables are **implemented and test-covered** (see Appendix D). What remains **outside** core v1 scope is **optional product expansion**: e.g. per-upload PDF embedding pipeline, automatic docket prefetch, richer jurisdiction packs, scheduled live-LLM CI, and infra niceties (request correlation IDs). Those are **continuous improvement**, not “missing core build” — schedule them as separate initiatives when budget and product priority allow.

---

## 6. Workstream deep dives

### 6.1 Model routing (automatic)

**Goal:** Strongest appropriate model per turn without user intervention.

**Implemented:**

- **`CHAT_MODEL_MAX`** — optional third NVIDIA tier in `select_chat_model()` for high-stakes OpenAI-compatible turns (document mode, audit mode, verify/strengthen tasks, long messages). Polish-only second pass stays on `CHAT_MODEL` (cost control). See `lawbot/model_routing.py`.
- **`decide_llm_route()`** — when Anthropic is also configured, escalation uses `ANTHROPIC_ESCALATION_MODEL` / caps; otherwise NVIDIA tiers apply.

**Acceptance:** Unit tests in `tests/test_llm_route.py`, `tests/test_model_routing.py`.

### 6.2 Polish and judge

**Goal:** Second pass when `auto_quality` says so; optional judge scores stored for analysis.

**Acceptance:** Distribution of `reason` tags stable or improved after tuning; draft_judge available on **all** backends if we add Anthropic support there.

### 6.3 Evaluation discipline

**Goal:** No “we think it’s smarter” — only **measured** movement.

**Artifacts:**

- Nightly or weekly: run `scripts/run_taste_matrix.py` (if keys available) → archive JSON.
- Human rubric: 1–5 on clarity, structure, citation safety, instruction following.

---

## 7. Multi-provider strategy (technical detail)

**Configured backends:** `settings.llm_backend()` still describes **which API credentials exist** (for `/health`). **Per-turn** routing uses `decide_llm_route()`.

**Behavior when only one backend is configured:** Same as before (NVIDIA-only or Anthropic-only).

**When both are configured:**

| `LAWBOT_ANTHROPIC_ESCALATION` | Behavior |
|-------------------------------|----------|
| `never` | Anthropic key ignored; all turns NVIDIA/OpenAI-compatible. |
| `always` | All turns use Anthropic (including polish) — highest cost. |
| `auto` (default) | NVIDIA/OpenAI-compatible unless the turn matches **escalation signals** and daily cap allows — then Anthropic (`ANTHROPIC_ESCALATION_MODEL` if set, else `ANTHROPIC_MODEL`). |

**Auto escalation signals:** `document_mode` **or** citation-audit stack (`audit_mode`) **or** task strengthen/verify **or** user message length ≥ 1600 chars — and **not** connectivity/smoke (`meta_connectivity_hint`). **Polish-only** turns (`polish_pass_only`) stay on OpenAI-compatible in `auto` to avoid doubling Anthropic cost.

**Risk:** Cost — use `LAWBOT_MAX_ANTHROPIC_ESCALATIONS_PER_DAY` (0 = no escalations when both keys; `-1` = unlimited).

---

## 8. Dependency graph (simplified)

```
Phase 0 (CI baseline)
   → Phase 1 (observability)
        → Phase 2 (multi-provider)
              → Phase 3 (reasoning depth)
        → Phase 4 (memory/RAG)
   → Phase 5 (retrieval)
   → Phase 6 (verification)
   → Phase 7 (UX)
   → Phase 8 (ops)
```

---

## 9. Risk register

| Risk | Mitigation |
|------|------------|
| API cost overrun | Hard caps, escalation budgets, logging |
| Model catalog change | `GET /v1/models` monitoring; pin model ids in env |
| Over-trust in polish | Hermes + draft gate remain authoritative |
| Legal liability | Disclaimers; human counsel; no “automated filing” |

---

## 10. Appendix A — API surface (quick reference)

- `GET /health` — backend, `chat_model` / `chat_model_fast` / optional `chat_model_max`  
- `GET /v1/health/deep` — DB + Hermes self-test  
- `POST /v1/chat`, `POST /v1/chat/stream` — main chat  
- `POST /v1/hermes/check` — verification  
- `GET /ws/hud` — HUD feed (token required)  
- Webhooks: Twilio SMS  

---

## 11. Appendix B — Cost governance

1. **Establish monthly ceiling** per environment (dev/staging/prod).  
2. **Tag** every LLM call with **phase** (primary, polish, judge, summarize).  
3. **Review** weekly: spend by phase vs user value (sessions that used vault, long documents).  
4. **Prefer** NVIDIA for volume; **reserve** Anthropic (or equivalent) for **escalation** only if budget constrained.

---

## 12. Appendix C — “Exhaustion checklist” (operational)

Use this as a recurring audit:

- [ ] All env vars documented and **set** in prod (no silent fallbacks).  
- [ ] `python scripts/verify_apis.py` passes.  
- [ ] Golden CI artifact reviewed for drift.  
- [ ] `docs/LAWBOT_QUALITY_BASELINE.md` still matches product intent.  
- [ ] CourtListener token valid; sample query works.  
- [ ] OpenClaw tool path smoke-tested.  
- [ ] Hermes rules updated for last month’s failures.  
- [ ] Model catalog diff reviewed (NVIDIA).  

---

**End of roadmap v1.** Update this file when Phases complete or when the resource inventory changes.

---

## 13. Appendix D — Test inventory (exhaust every regression hook)

| Test module | Primary coverage |
|-------------|------------------|
| `tests/test_polish_pass.py` | Second-pass polish behavior |
| `tests/test_empty_vault_sanitize.py` | Empty-vault / leakage sanitization |
| `tests/test_intent.py` | Smoke vs substantive, task hints |
| `tests/test_chat_timeout_formula.py` | Timeout math for long operations |
| `tests/test_auto_quality.py` | When polish auto-fires (`auto_*` reasons) |
| `tests/test_audit_chat_turn.py` | Citation-audit turn wiring |
| `tests/test_draft_quality_gate.py` | Deterministic draft structure gate |
| `tests/test_golden_drafts.py` | Golden fixtures vs gate |
| `tests/test_chat_tokens.py` | Token budget / scaling behavior |
| `tests/test_chat_controls.py` | API flags and controls |
| `tests/test_gwinnett_magistrate.py` | Gwinnett template injection |
| `tests/test_model_routing.py` | `CHAT_MODEL` / `CHAT_MODEL_FAST` / optional `CHAT_MODEL_MAX` |
| `tests/test_chat_task_integration.py` | Task + chat integration |
| `tests/test_chat_mode.py` | Chat mode behavior |
| `tests/test_taste_matrix_script.py` | Taste matrix script |
| `tests/test_hermes_verify.py` | Hermes verification rules |
| `tests/test_e2e_mock_llm_sanitize.py` | E2E with mock LLM |
| `tests/test_ui_audit.py` | Static routes, DOM, health |
| `tests/test_document_review.py` | Document review helpers |
| `tests/test_audit_retrieval.py` | Audit retrieval merge + queries |
| `tests/test_citation_extract.py` | Citation extraction |

**Exhaustion discipline:** Any new feature touching chat, vault, or verification should extend **at least one** of: unit test, golden fixture, or Hermes case.

---

## 14. Appendix E — Scripts inventory

| Script | Role |
|--------|------|
| `scripts/verify_apis.py` | Live probes: NVIDIA + CourtListener + DB |
| `scripts/preflight_launch.sh` | CI quality + full unittest + `verify_apis` (if API key set) |
| `scripts/launch.sh` | Preflight then `uvicorn` (or `SKIP_PREFLIGHT=1` for dev) |
| `scripts/ci_quality.sh` | Draft gate + golden + metrics JSONL |
| `scripts/draft_quality_golden_metrics.py` | Emit `draft-quality-golden.jsonl` for CI artifact |
| `scripts/check_baseline_reply.py` | Compare replies to stored baselines |
| `scripts/post_baseline_message.py` | Post baseline prompts (ops) |
| `scripts/run_taste_matrix.py` | Multi-prompt quality sweep |
| `scripts/taste_prompts.json` | Prompt set for taste matrix |
| `scripts/verify_user_flow.sh` | User-flow verification |
| `scripts/verify_chat_timeout_build.py` | Timeout build check |
| `scripts/browser_smoke.py` | Browser smoke |
| `scripts/capture_ui_screenshots.py` | UI capture for review |
| `scripts/dev_server.sh` | Local dev server helper |
| `scripts/openclaw_lawbot_verify.sh` | OpenClaw + Hermes verify bridge |

---

## 15. Appendix F — MCP / dev tooling (Cursor)

Enabled MCP servers (from workspace configuration) include **GitHub**, **Vercel**, **Supabase**, **Stripe**, **Figma**, **n8n**, **Zapier**, **Make**, etc. These do **not** execute inside the Lawbot Python process; they **accelerate** shipping (PRs, deploys, design, automation). **Exhaustion move:** use them for **release hygiene** (CI, deployments, issue tracking) so runtime work in §2–§7 stays funded and merged.

---

## 16. Adversarial review (what could still beat this roadmap)

| Gap | Mitigation (future / optional) |
|-----|------------------------------|
| **No automated retry** on transient 5xx from providers | **Done:** `lawbot/openai_retry.py` — exponential backoff on chat completions (main, reasoning, compaction, draft judge); `LAWBOT_LLM_HTTP_RETRIES`. |
| **No request correlation id** in API responses | Add optional `X-Request-ID` middleware; echo in `log_llm_event`. |
| **draft_judge** on Anthropic-only installs | **Done:** `draft_judge.py` uses Anthropic Messages when no OpenAI-compatible key. |
| **Phase 3 extended thinking** | Wire provider-native reasoning flags when API exposes them; keep behind same escalation policy. |
| **SQLite WAL / backups** | Enable WAL; document backup of `LAWBOT_DB_PATH` for escalation counts + sessions. |

These are **incremental** improvements; they do not invalidate Phases 1–2 implementation.
