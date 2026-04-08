# Lawbot — context for Claude Code / Cursor / other agents

This file gives coding agents quick orientation. **It is not loaded by the production app** (zero runtime cost).

## Cursor (IDE)

- **Project rules:** `.cursor/rules/*.mdc` — loaded automatically by Cursor (`lawbot-core`, `lawbot-python`, `lawbot-static` for `lawbot/static/`).
- **Deep context on demand:** In chat, attach **`@CLAUDE.md`**, **`@docs/ARCHITECTURE.md`**, or **`@docs/DEVELOPER_WORKFLOW.md`** so the model sees the full file without duplicating it in rules.
- **Interpreter:** Prefer the repo venv (`.vscode/settings.json` points at `.venv` if present).

## What Lawbot is

- **Retrieval-first** legal assistant: citations must come from **fetched, stored** text in the citation vault and verification flow—not model memory.
- **Stack:** Python 3.12+, FastAPI (`lawbot.api`), static UI under `lawbot/static/`, tests in `tests/`.
- **Not:** Licensed legal advice; outputs are for research and preparation.

## Commands

```bash
# Install
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # ruff, bandit, optional playwright

# Lint + security scan (same idea as CI)
bash scripts/security_scan.sh

# Tests
python -m unittest discover -s tests -p 'test_*.py' -q

# Launch (preflight + server)
bash scripts/launch.sh
```

## Where to look

| Topic | Location |
|-------|----------|
| System design, citation integrity | `docs/ARCHITECTURE.md` |
| API / UI integration | `docs/SIMPLE_UI_AND_TOOLS.md` |
| Open-access research | `docs/OPEN_ACCESS_RESEARCH.md` |
| Developer workflow, PR checklist | `docs/DEVELOPER_WORKFLOW.md` |

## Rules for changes

- Match existing style; **minimal diffs**—only what the task needs.
- Do not add production dependencies for **developer-only** tools (Claude Code, pre-commit, bandit run in CI—not shipped to users).
- **Secrets:** never commit `.env`; use `.env.example` for documented keys only.
