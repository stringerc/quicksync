# Scoped initiatives — live eval, matrix, enterprise, shadow

This document **scopes** work that is intentionally not fully implemented in-tree yet: clear boundaries, phases, dependencies, and exit criteria. Update when priorities shift.

---

## 1. Live-LLM goldens (env-gated)

**Goal:** Run the same structural expectations as offline goldens, but against a **real** chat turn so regressions catch prompt/model/stack issues Hermes-only fixtures miss.

| Dimension | Scope |
|-----------|--------|
| **In scope** | Script or job that POSTs to `/v1/chat` (or calls `execute_chat_turn` in-process) with fixture `message` + session/profile from JSON; asserts HTTP 200, `audit.hermes_passed`, and optional `turn_signals` fields; records model id, latency, and hashes in `eval/runs/` (append-only, gitignored). |
| **Out of scope (v1)** | Flaky LLM assertions on exact wording; parallel load testing; comparing answers across providers in CI. |
| **Gates** | `LAWBOT_EVAL_LIVE=1` and presence of `NVIDIA_API_KEY` / `OPENAI_COMPATIBLE_*` (or explicit eval key) — **no secrets in repo**; default CI stays offline-only. |
| **Phases** | **P0:** One “smoke live” case (short ping) — proves wiring. **P1:** 3–5 cases mirroring offline matrix tags. **P2:** Nightly-only expansion (see §2). |
| **Dependencies** | Network, billable API, stable test session DB or ephemeral DB path. |
| **Exit criteria** | Documented command (`python -m lawbot.eval.run_goldens --live` or sibling module), single failure artifact path, README section in `eval/goldens/README.md`. |
| **Risk** | Cost + flake; mitigate with retries=1, timeout caps, and **never** blocking PR CI on live by default. |

---

## 2. Nightly full golden matrix

**Goal:** Increase **breadth** of Hermes coverage without slowing every PR; publish a **coverage snapshot** (matrix cells with ≥1 passing golden).

| Dimension | Scope |
|-----------|--------|
| **In scope** | Cron/GitHub Actions **schedule** (e.g. 06:00 UTC) running: `strict_test.sh` **or** goldens-only + optional `--live` subset; artifact upload of CSV + summary JSON; optional Slack/email on failure only. |
| **Out of scope (v1)** | Blocking deploys on nightly alone; auto-rollback from golden failures (needs separate release process). |
| **Matrix definition** | Axes documented in `eval/goldens/README.md` (e.g. jurisdiction × task regime × source mode). **Coverage metric** = % of cells with ≥1 golden tagged `matrix_cell: "ga_civil|filing_draft"` passing. |
| **Phases** | **P0:** Nightly = current offline goldens + strict_test. **P1:** Matrix report **shipped** (`python -m lawbot.eval.matrix_report`, `matrix_taxonomy.json`). **P2:** Attach live subset weekly or nightly with budget cap. |
| **Dependencies** | CI minutes, artifact retention policy, optional secret store for live job. |
| **Exit criteria** | Green scheduled workflow; one downloadable artifact per run; matrix % in release notes template. |

---

## 3. Enterprise track (SSO, audit, BAA posture, orgs)

**Goal:** Sequence **multi-quarter** capabilities so “legal OS” claims match engineering reality — **no** big-bang integration list.

| Dimension | Scope |
|-----------|--------|
| **Positioning (chosen default)** | **Focused research/draft surface** until revenue justifies enterprise depth — see roadmap §3. Enterprise items below are **explicitly sequenced**, not parallel mandates. |
| **In scope — phase A (foundation)** | API stability (versioned `/v1` contracts, deprecation policy); **org-scoped** API keys or projects (design + minimal schema); export of **audit-relevant** fields already in logs (`turn_decision`, session id) as CSV/JSON bundle for a session or date range. |
| **In scope — phase B (trust)** | SSO (SAML/OIDC) behind feature flag; **admin** role for org; configurable **retention** window for chat storage; documented **subprocessor** list + DPA template (legal review outside eng). |
| **In scope — phase C (regulated)** | BAA or BAA-equivalent **process** for US healthcare-adjacent use (if product direction requires); field-level encryption at rest (if required by contract); **SOC2-style** evidence pack from existing logs (not certification itself). |
| **Out of scope (unless contracted)** | Native mobile apps; universal docket API; e-file partner integrations; on-prem first release. |
| **Dependencies** | Identity provider, billing (org seats), legal/compliance review, SLA definitions. |
| **Exit criteria per phase** | Written go/no-go + one pilot customer or internal dogfood org before the next phase starts. |

---

## 4. Shadow / paper mode (second checker)

**Goal:** Run a **stricter or duplicate** check on a **sample** of turns, log agreement rate, **without** changing user-visible output until metrics justify it.

| Dimension | Scope |
|-----------|--------|
| **In scope** | Feature flag `LAWBOT_SHADOW_CHECKER=1`; sample rate `LAWBOT_SHADOW_SAMPLE_RATE` (e.g. 0.02); async or post-reply path that re-runs Hermes with stricter config **or** second model with judge prompt; log `shadow_agreement`, `shadow_hermes_passed`, `session_id` to same sink as `turn_decision`. |
| **Out of scope (v1)** | User-visible “second opinion” UI; blocking on shadow failure; training data collection from shadow outputs. |
| **Phases** | **P0:** Log-only duplicate Hermes pass on 2% of traffic. **P1:** Dashboard CSV export weekly. **P2:** Opt-in stricter mode for paid tier (product decision). |
| **Dependencies** | Extra LLM cost at sample rate; storage for shadow rows; privacy review if prompts contain PII. |
| **Exit criteria** | Documented disagreement rate SLO (e.g. investigate if >5% divergence week-over-week); kill-switch via env. |

---

## 5. Walk-forward / holdout (process + data)

**Goal:** Prevent **overfitting** prompts to the golden library.

| Dimension | Scope |
|-----------|--------|
| **In scope** | Monthly calendar reminder (issue template or `memory/` checklist): add 1+ new golden from real redacted turns; tag `holdout: true`; **do not** tune prompts to pass holdouts only — use for release gating and manual review. |
| **Engineering** | JSON field `holdout` already supported; optional `eval/run_holdout_only.py` that **excludes** holdouts from dev iteration runs (local script). |
| **Out of scope** | Automated scraping of new law; automatic holdout generation from production without human review. |

---

## 6. Consolidated priority order (suggested)

1. **Nightly offline matrix report** — cheap, improves visibility.  
2. **Live-LLM smoke (P0)** — env-gated, one case.  
3. **Shadow P0** — sample logging only.  
4. **Enterprise phase A** — when commercial pull exists.  
5. **Live expansion + shadow P1** — as budget and SLOs allow.

---

## Related docs

- `docs/LAWBOT_ROADMAP.md` — shipped vs planned summary table  
- `eval/goldens/README.md` — golden file format and tags  
- `docs/HUMAN_REVIEW_RUBRIC.md` — human spot-checks alongside automation  
