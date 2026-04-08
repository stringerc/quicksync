"""
Run curated golden response fixtures through Hermes and optional structural checks.

Usage::
    python -m lawbot.eval.run_goldens
    python -m lawbot.eval.run_goldens --verbose

Golden files: ``eval/goldens/cases/*.json`` (repo root, next to ``lawbot/`` package).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from typing import Any

from lawbot.eval.golden_io import CASES_DIR, RUNS_DIR, load_golden_cases
from lawbot.hermes_verify import run_hermes_checks

_RUNS_DIR = RUNS_DIR
_TELEMETRY_CSV = _RUNS_DIR / "golden_telemetry.csv"
_FAILURE_JSON = _RUNS_DIR / "last_golden_failure.json"


def _fingerprint(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload.get("response", {}), sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def run_all(*, verbose: bool = False) -> int:
    """
    Run all goldens. Returns process exit code (0 = all pass).
    """
    cases = load_golden_cases()
    if not cases:
        print("No golden cases found under", CASES_DIR, file=sys.stderr)
        return 1

    _RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    failures: list[dict[str, Any]] = []
    row_base = {"run_at_utc": ts}

    for case in cases:
        cid = case.get("id", "?")
        resp = case.get("response")
        exp = case.get("expected") or {}
        exp_pass = bool(exp.get("hermes_passed", True))

        if not isinstance(resp, dict):
            failures.append({"id": cid, "error": "missing response object"})
            continue

        rpt = run_hermes_checks(None, resp)
        ok = rpt.passed == exp_pass
        fp = _fingerprint(case)

        if verbose or not ok:
            print(
                f"[golden] {cid} hermes_passed={rpt.passed} expected={exp_pass} "
                f"tags={case.get('tags', [])} fp={fp}"
            )
            if not ok:
                print("  errors:", rpt.errors)

        _append_telemetry_csv(
            {
                **row_base,
                "golden_id": cid,
                "hermes_passed": rpt.passed,
                "expected_hermes_passed": exp_pass,
                "match": ok,
                "fingerprint": fp,
                "holdout": bool(case.get("holdout")),
            }
        )

        if not ok:
            failures.append(
                {
                    "id": cid,
                    "hermes_passed": rpt.passed,
                    "expected_hermes_passed": exp_pass,
                    "errors": rpt.errors,
                    "warnings": rpt.warnings,
                    "fingerprint": fp,
                    "tags": case.get("tags", []),
                }
            )

    if failures:
        payload = {"run_at_utc": ts, "failures": failures}
        _FAILURE_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print("Wrote", _FAILURE_JSON, file=sys.stderr)
        return 1

    if _FAILURE_JSON.exists():
        _FAILURE_JSON.unlink()
    print(f"OK — {len(cases)} golden case(s) passed.")
    return 0


def _append_telemetry_csv(row: dict[str, Any]) -> None:
    _RUNS_DIR.mkdir(parents=True, exist_ok=True)
    new_file = not _TELEMETRY_CSV.exists()
    fieldnames = list(row.keys())
    with _TELEMETRY_CSV.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if new_file:
            w.writeheader()
        w.writerow(row)


def main() -> None:
    p = argparse.ArgumentParser(description="Run Lawbot Hermes golden fixtures.")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args()
    sys.exit(run_all(verbose=args.verbose))


if __name__ == "__main__":
    main()
