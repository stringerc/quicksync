#!/usr/bin/env python3
"""
Emit one JSON line per golden fixture (for CI logs / artifacts) and aggregate stats.

Usage (from repo root):
  python scripts/draft_quality_golden_metrics.py
  python scripts/draft_quality_golden_metrics.py --jsonl-out /tmp/draft-quality-golden.jsonl
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lawbot.draft_quality_gate import analyze_draft_quality, draft_quality_to_json_line  # noqa: E402

FIXTURE_DIR = ROOT / "tests" / "fixtures" / "golden"
MARKER = "DRAFT_QUALITY_GOLDEN"


def main() -> int:
    p = argparse.ArgumentParser(description="Golden draft quality metrics for CI")
    p.add_argument(
        "--jsonl-out",
        type=Path,
        default=None,
        help="Optional path to append/write one JSON object per line (case id + metrics)",
    )
    args = p.parse_args()
    manifest = json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))
    scores: list[int] = []
    lines_out: list[str] = []

    for case in manifest["cases"]:
        cid = case["id"]
        ans = (FIXTURE_DIR / case["answer_file"]).read_text(encoding="utf-8")
        usr = (FIXTURE_DIR / case["user_file"]).read_text(encoding="utf-8")
        r = analyze_draft_quality(
            ans,
            user_message=usr,
            document_mode=True,
            citation_audit=case.get("citation_audit", False),
            vault_chunk_ids=case.get("vault_chunk_ids"),
        )
        scores.append(int(r["score_percent"]))
        payload = json.loads(draft_quality_to_json_line(r))
        row = {"case_id": cid, **payload}
        line = json.dumps(row, separators=(",", ":"))
        # Stable prefix for `grep DRAFT_QUALITY_GOLDEN` in Actions logs
        print(f"{MARKER} {line}", flush=True)
        lines_out.append(line)

    if args.jsonl_out is not None:
        args.jsonl_out.write_text("\n".join(lines_out) + "\n", encoding="utf-8")

    mean = statistics.mean(scores) if scores else 0.0
    print(
        f"{MARKER}_SUMMARY "
        + json.dumps(
            {
                "cases": len(scores),
                "score_percent_mean": round(mean, 2),
                "score_percent_min": min(scores) if scores else None,
                "score_percent_max": max(scores) if scores else None,
            },
            separators=(",", ":"),
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
