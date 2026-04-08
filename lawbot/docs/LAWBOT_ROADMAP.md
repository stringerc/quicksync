# Lawbot roadmap — weaknesses → shipped outcomes

This document tracks **end-to-end** work (not only priority order): evaluation, trust UX, positioning, first-session experience, and UPRE-style telemetry. Status is descriptive; update as you ship.

**Scoped (not yet fully built):** live-LLM goldens, nightly matrix reporting, enterprise phases, shadow mode, walk-forward process — see [`LAWBOT_SCOPED_INITIATIVES.md`](./LAWBOT_SCOPED_INITIATIVES.md) for boundaries, phases, and exit criteria.

---

## 1. Evaluation / golden coverage

| Item | Target outcome | Status |
|------|----------------|--------|
| Curated golden sets | `eval/goldens/cases/*.json` — fixed responses + expected Hermes pass/fail | **Shipped** (initial set) |
| Runner | `python -m lawbot.eval.run_goldens` | **Shipped** |
| CI | `scripts/strict_test.sh` step 3 runs goldens | **Shipped** |
| Telemetry rows | `eval/runs/golden_telemetry.csv` (gitignored locally) | **Shipped** |
| Failure artifact | `eval/runs/last_golden_failure.json` on mismatch | **Shipped** |
| Jurisdiction / task matrix | Tag goldens; track coverage % in release notes | **Shipped** — `python -m lawbot.eval.matrix_report` + `matrix_taxonomy.json`; nightly job still [optional §2](./LAWBOT_SCOPED_INITIATIVES.md#2-nightly-full-golden-matrix) |
| Holdout splits | `holdout: true` in JSON; do not tune prompts only to pass holdouts | **Partial** (field exists) |
| Human spot-check | Rubric: `docs/HUMAN_REVIEW_RUBRIC.md` | **Shipped** |
| Regression diff | Fingerprints in CSV + failure JSON | **Shipped** |
| Live-LLM goldens | Optional nightly against `/v1/chat` with secrets | **Scoped** — [§1](./LAWBOT_SCOPED_INITIATIVES.md#1-live-llm-goldens-env-gated) P0→P2 |
| Walk-forward (legal) | Monthly new cases; require non-regression on holdout | **Scoped** — [§5](./LAWBOT_SCOPED_INITIATIVES.md#5-walk-forward--holdout-process--data) |

---

## 2. User misunderstanding (education)

| Item | Target outcome | Status |
|------|----------------|--------|
| Persistent disclosure strip | 4 bullets + link to trust page | **Shipped** (UI) |
| Badge copy | “Quotes match loaded text” + tooltips | **Shipped** (UI) |
| Long-paste confirm | Optional confirm before send; respect “don’t ask” | **Shipped** (UI) |
| Jurisdiction visibility | Pill when jurisdiction field set | **Shipped** (UI) |
| Static trust page | `/static/trust.html` | **Shipped** |

---

## 3. Competitive positioning

| Track | Scope | Status |
|-------|--------|--------|
| **Focused research/draft** (default) | Retrieval, verification, transparency, export | **Current positioning** — document in marketing |
| Narrow integrations | Export Markdown (exists); Word/PDF later | **Markdown shipped** |
| Enterprise / SSO / BAA | Multi-quarter | **Scoped** — [§3](./LAWBOT_SCOPED_INITIATIVES.md#3-enterprise-track-sso-audit-baa-posture-orgs) phases A→C |
| Docket / e-file | Partner-dependent | **Out of scope** until enterprise phase B/C + partner (see scoped doc) |
| Mobile | Responsive web first; native later | **Partial** (viewport meta exists) |

---

## 4. Single-session “wow”

| Item | Target outcome | Status |
|------|----------------|--------|
| Simple mode | Hide advanced toggles; default ON | **Shipped** (UI) |
| First-run suggestions | Starter prompts in empty state | **Shipped** (UI) |
| Fast first reply | Existing fast model + connectivity routing | **Already in backend** |

---

## 5. UPRE-style engineering (borrowed patterns)

| Pattern | Lawbot implementation | Status |
|---------|------------------------|--------|
| Structured envelope | `turn_signals` + `audit.task_regime`, `citation_confidence`, `hermes_passed` | **Shipped** |
| Gates | `turn_signals.gates` (Hermes hard, shipping soft) | **Shipped** |
| Decision telemetry | `turn_decision` JSON log line | **Shipped** |
| Isolation tests | Hermes goldens + existing unit tests | **Partial** — extend per-layer mocks |
| Shadow mode | Second pass without UX change | **Scoped** — [§4](./LAWBOT_SCOPED_INITIATIVES.md#4-shadow--paper-mode-second-checker) P0→P2 |

---

## 6. What “done” looks like

- Every PR: **lint + unit tests + Hermes goldens** green.
- Every release: **matrix coverage note** + spot-check sample from rubric.
- Monthly: **add or rotate holdout goldens**; review `turn_decision` aggregates if exported.
- See **suggested priority order** in [`LAWBOT_SCOPED_INITIATIVES.md` §6](./LAWBOT_SCOPED_INITIATIVES.md#6-consolidated-priority-order-suggested).
