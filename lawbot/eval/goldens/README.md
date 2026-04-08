# Golden Hermes fixtures

Each `cases/*.json` file is a **recorded-shaped** `/v1/chat` response (no live LLM). The runner (`python -m lawbot.eval.run_goldens`) passes the `response` object through `run_hermes_checks` and compares `hermes_passed` to `expected.hermes_passed`.

## Fields

| Field | Meaning |
|--------|---------|
| `id` | Stable id for logs and failures |
| `tags` | Jurisdiction / task labels (e.g. `GA`, `federal`, `connectivity`, `no-sources`) |
| `holdout` | If `true`, treat as out-of-sample in coverage reports (manual for now) |
| `expected.hermes_passed` | Whether Hermes should pass |
| `response` | Full JSON object as returned by the API |

## Matrix coverage

- **Automated report:** `python -m lawbot.eval.matrix_report` (human summary) or `--json` / `--write eval/runs/matrix_report.json`.
- **Taxonomy:** `matrix_taxonomy.json` lists `required_cells` as `tag|task_regime` (see `audit.task_regime` on each golden `response`). Coverage % = required cells with ≥1 **passing** golden (Hermes result matches `expected.hermes_passed`).
- Optional per-case overrides: `matrix_cell` (one cell) or `matrix_cells` (list) instead of expanding `tags` × regime.
- `holdout: true` cases should not be tuned against directly; add monthly.

## Telemetry

Successful runs append a row to `eval/runs/golden_telemetry.csv`. Failures write `eval/runs/last_golden_failure.json` with fingerprints for drift tracking.

## CI

`scripts/strict_test.sh` runs the golden runner after unit tests. Full nightly can add more cases or live-LLM smoke (optional, off by default).
