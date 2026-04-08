# Developer workflow (no production impact)

Everything here runs **on your machine or in CI**. None of it is imported by the Lawbot server at runtime, so it does **not** add latency to `/v1/chat` or user-facing paths.

## Cursor (IDE) — rules + context

This repo includes **Cursor project rules** under **`.cursor/rules/`**:

| File | Role |
|------|------|
| `lawbot-core.mdc` | Always on: retrieval-first product, architecture pointer, secrets, minimal diffs. |
| `lawbot-python.mdc` | When editing `**/*.py`: tests, `security_scan.sh`, citation-path caution. |
| `lawbot-static.mdc` | When editing `lawbot/static/**`: Markdown + DOMPurify, `innerHTML`, timeout tests. |

**How to use well**

1. Open the **Lawbot folder** as the workspace root (so rules apply).
2. For long sessions, **`@`-mention** `CLAUDE.md` or `docs/ARCHITECTURE.md` once when work touches citations, vault, or chat pipeline.
3. Enable a **Python interpreter** from `.venv` after `python3 -m venv .venv` (optional helper: `.vscode/settings.json`).
4. **Composer / Agent:** Same rules apply; prefer attaching test files or `lawbot/` paths so changes stay scoped.
5. **Cursor settings:** Ensure **Project Rules** are enabled (Cursor **Settings → Rules**). If project rules never apply, check that **Global** rules are not overriding and that the workspace root is the Lawbot repo.

Rules are **not** a substitute for reading `docs/ARCHITECTURE.md` before large refactors.

## Claude Code (optional terminal agent)

[Claude Code](https://github.com/anthropics/claude-code) is Anthropic’s **terminal/IDE** coding agent (`claude` CLI). Use it for refactors, tests, git hygiene, and exploration inside this repo.

1. Install (pick one): see [official setup](https://code.claude.com/docs/en/setup) — e.g. `brew install --cask claude-code` on macOS, or the install script from the docs.
2. From the repo root: run `claude`.
3. Read **`CLAUDE.md`** in this repo for project context (also useful for Cursor and other agents).

**Do not** add Claude Code as a Python or Node dependency of Lawbot’s runtime; the CLI is a **developer tool**, not an application library.

## Security-oriented checks (CI + local)

We mirror the *idea* of “security guidance” hooks: **static analysis** on `lawbot/`, not a second LLM in the request path.

| What | Where |
|------|--------|
| **Ruff** lint | `ruff check lawbot tests scripts` |
| **Bandit** (medium+ only on `lawbot/`) | `bandit -r lawbot -ll -q` |
| **One command** | `bash scripts/security_scan.sh` |

CI runs the same checks in `.github/workflows/lawbot-ci.yml` (and the repo-wide workflow in `ci.yml` runs Ruff + tests on main).

Optional **pre-commit** (see repo root `.pre-commit-config.yaml`): `pip install pre-commit && pip install -r requirements-dev.txt && pre-commit install` — runs **`scripts/pre_commit_security.sh`**, which delegates to **`scripts/security_scan.sh`** (Ruff + Bandit, same as CI). Uses **`always_run: true`** so hooks run even with an empty index. **Pin bumps:** update `requirements-dev.txt`, **`pip install` lines in `.github/workflows/`**, and keep dev installs aligned (no separate pre-commit package pin—hooks use your env’s Ruff/Bandit from `requirements-dev.txt`).

**Monorepo vs Lawbot-as-root:** If `.git` is **above** the `lawbot/` folder, the default hook entry is `bash lawbot/scripts/pre_commit_security.sh`. If Lawbot **is** the git root, change the entry in `.pre-commit-config.yaml` to `bash scripts/pre_commit_security.sh`.

## Structured feature workflow (human process)

Adapted from a phased “feature dev” style — **process only**, not code inside `lawbot/`:

1. **Scope** — One sentence outcome; what is explicitly out of scope.
2. **Read** — `docs/ARCHITECTURE.md` + files you will touch; note citation/verification boundaries.
3. **Test-first or test-next** — Add or update `tests/` for behavior you care about.
4. **Implement** — Smallest change that satisfies tests and architecture.
5. **Security scan + ruff** — `bash scripts/security_scan.sh`.
6. **Manual smoke** — `bash scripts/launch.sh` or targeted script; never commit secrets.
7. **PR** — Use the checklist below.

## PR checklist (GitHub)

Use this for human review (similar in spirit to PR-review toolkits, but **no extra agents** in Lawbot):

- [ ] **Behavior** — Matches issue or agreed scope; no unrelated refactors.
- [ ] **Tests** — New logic covered or explained why not (e.g. pure config).
- [ ] **Security** — No `eval` / `exec` on user input; HTML/JS output escaped where user content is echoed; env secrets not logged.
- [ ] **Lint + bandit** — `bash scripts/security_scan.sh` passes locally.
- [ ] **Docs** — User-facing behavior change reflected in `README.md` or `docs/` if needed.

## Anthropic Agent SDK (future note)

If you ever build a **separate** internal service or batch tool using [Claude Agent SDK](https://docs.anthropic.com/), that is an **architecture decision** (new deployable, credentials, SLOs). It is **not** a lightweight drop-in for the existing FastAPI chat pipeline—and it should stay out of the hot path unless explicitly designed for it.

## OpenClaw and Hermes (coding vs legal stack)

**Hermes (in this repo)** is **`lawbot.hermes_verify`** + **`POST /v1/hermes/check`**: a **deterministic second pass** on Lawbot **chat JSON** (empty-vault leakage, quote-vs-vault, etc.). It is for **verification of legal answers**, not for writing or editing code. You do **not** “implement a coding agent” inside Hermes; routing coding tasks through Hermes would be the wrong layer.

**OpenClaw** is your **messaging + tool-calling gateway** (Telegram, WhatsApp, etc.). It already fits Lawbot as an HTTP client to **`POST /v1/chat`** and optional shell scripts (see `docs/OPENCLAW_BRIDGE.md` and `openclaw-skills/lawbot-verify/`).

What you *can* add on the OpenClaw side (configuration under `~/.openclaw/`, not inside Lawbot’s Python runtime):

| Goal | Reasonable approach |
|------|---------------------|
| **Trigger dev checks from a channel** | A tool or skill that runs `bash scripts/security_scan.sh` or `./scripts/openclaw_lawbot_verify.sh` on the **same machine** that holds the repo — narrow scope, explicit path. |
| **Replace Cursor / Claude Code for coding** | Not a good fit for OpenClaw alone: general-purpose coding needs an **IDE** or a **dedicated CLI** (Cursor, Aider, etc.). Wiring OpenClaw to arbitrary `git`/`aider` on your dev box from Telegram is possible but **high risk** (broad shell access from chat). Prefer **Cursor** (or similar) for coding, OpenClaw for **mobility + Lawbot legal chat + smoke checks**. |
| **Free / no Claude Code** | Use **Cursor** (or local **Ollama + Aider**) on the machine where you edit code; OpenClaw does not make third-party tools free — it only **invokes** whatever you configure. |

**Summary:** Implement **legal** workflows through OpenClaw → Lawbot HTTP. **Hermes** verifies those responses. **Coding** workflows stay in the IDE or a CLI you trust; optionally mirror **dev-only** commands (lint, verify script) as restricted OpenClaw tools if you need them from your phone.
