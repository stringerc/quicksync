"""
Report golden matrix coverage: (tag × task_regime) cells with ≥1 passing fixture.

Usage::

    python -m lawbot.eval.matrix_report
    python -m lawbot.eval.matrix_report --json
    python -m lawbot.eval.matrix_report --write eval/runs/matrix_report.json

Optional taxonomy: ``eval/goldens/matrix_taxonomy.json`` lists ``required_cells``;
coverage % = fraction of required cells that have at least one **passing** golden
(Hermes result matches ``expected.hermes_passed``).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lawbot.eval.golden_io import REPO_ROOT, TAXONOMY_PATH, load_golden_cases
from lawbot.hermes_verify import run_hermes_checks


def _extract_regime(response: dict[str, Any]) -> str:
    audit = response.get("audit") if isinstance(response.get("audit"), dict) else {}
    ts = response.get("turn_signals") if isinstance(response.get("turn_signals"), dict) else {}
    for key in ("task_regime",):
        v = audit.get(key) or ts.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return "unknown"


def _iter_cell_keys(case: dict[str, Any], regime: str) -> list[str]:
    explicit = case.get("matrix_cells")
    if isinstance(explicit, list) and explicit:
        return [str(x).strip() for x in explicit if str(x).strip()]
    single = case.get("matrix_cell")
    if isinstance(single, str) and single.strip():
        return [single.strip()]
    tags = case.get("tags")
    if not isinstance(tags, list) or not tags:
        return [f"_untagged|{regime}"]
    return [f"{str(t).strip()}|{regime}" for t in tags if str(t).strip()]


@dataclass
class CellStats:
    golden_ids: list[str] = field(default_factory=list)
    passing_ids: list[str] = field(default_factory=list)


def _load_taxonomy() -> list[str]:
    if not TAXONOMY_PATH.is_file():
        return []
    try:
        raw = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    cells = raw.get("required_cells")
    if not isinstance(cells, list):
        return []
    return [str(c).strip() for c in cells if str(c).strip()]


def build_report() -> dict[str, Any]:
    cases = load_golden_cases()
    cells: dict[str, CellStats] = {}
    per_case: list[dict[str, Any]] = []

    for case in cases:
        cid = str(case.get("id", "?"))
        resp = case.get("response")
        exp = case.get("expected") or {}
        exp_pass = bool(exp.get("hermes_passed", True))
        if not isinstance(resp, dict):
            per_case.append({"id": cid, "error": "missing response object", "match": False})
            continue

        regime = _extract_regime(resp)
        rpt = run_hermes_checks(None, resp)
        match = rpt.passed == exp_pass
        keys = _iter_cell_keys(case, regime)
        row = {
            "id": cid,
            "regime": regime,
            "hermes_passed": rpt.passed,
            "expected_hermes_passed": exp_pass,
            "match": match,
            "matrix_cells": keys,
            "holdout": bool(case.get("holdout")),
        }
        per_case.append(row)

        for ck in keys:
            st = cells.setdefault(ck, CellStats())
            st.golden_ids.append(cid)
            if match:
                st.passing_ids.append(cid)

    required = _load_taxonomy()
    observed = sorted(cells.keys())
    covered_required = [c for c in required if c in cells and cells[c].passing_ids]
    missing_required = [c for c in required if c not in cells or not cells[c].passing_ids]

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "golden_count": len(cases),
        "taxonomy_path": str(TAXONOMY_PATH.relative_to(REPO_ROOT)) if TAXONOMY_PATH.is_file() else None,
        "required_cell_count": len(required),
        "required_cells_covered": len(covered_required),
        "required_coverage_ratio": (len(covered_required) / len(required)) if required else None,
        "missing_required_cells": missing_required,
        "observed_cell_count": len(observed),
        "cells": {
            k: {
                "golden_count": len(v.golden_ids),
                "passing_golden_count": len(v.passing_ids),
                "golden_ids": v.golden_ids,
                "passing_golden_ids": v.passing_ids,
            }
            for k, v in sorted(cells.items())
        },
        "per_golden": per_case,
    }
    return payload


def main() -> None:
    p = argparse.ArgumentParser(description="Lawbot golden matrix coverage report.")
    p.add_argument("--json", action="store_true", help="Print JSON to stdout")
    p.add_argument(
        "--write",
        type=str,
        default="",
        help="Write JSON report to this path (under repo if relative)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 if any required taxonomy cell has no passing golden",
    )
    args = p.parse_args()
    report = build_report()

    out_path: Path | None = None
    if args.write:
        out_path = Path(args.write)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        req = report.get("required_cell_count") or 0
        cov = report.get("required_cells_covered") or 0
        ratio = report.get("required_coverage_ratio")
        print(f"Goldens: {report['golden_count']}  Observed cells: {report['observed_cell_count']}")
        if req:
            pct = f"{100.0 * ratio:.1f}%" if ratio is not None else "n/a"
            print(f"Required taxonomy: {cov}/{req} cells with ≥1 passing golden ({pct})")
            miss = report.get("missing_required_cells") or []
            if miss:
                print("Missing required cells:", ", ".join(miss[:12]) + (" …" if len(miss) > 12 else ""))
        else:
            print(f"(Add {TAXONOMY_PATH.name} with required_cells for coverage vs a fixed matrix.)")
        print("Cells:")
        for ck, info in (report.get("cells") or {}).items():
            print(f"  {ck}  pass={info['passing_golden_count']}/{info['golden_count']}")
        if out_path:
            print(f"Wrote {out_path}", file=sys.stderr)

    missing = report.get("missing_required_cells") or []
    if args.strict and _load_taxonomy() and missing:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
