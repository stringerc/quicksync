#!/usr/bin/env python3
"""
Run a fixed battery of prompts against POST /v1/chat; save full JSON for diffing after prompt/sanitize changes.

Usage (server must be up):
  BASE_URL=http://127.0.0.1:8765 python scripts/run_taste_matrix.py run
  BASE_URL=http://127.0.0.1:8765 python scripts/run_taste_matrix.py run --json
  python scripts/run_taste_matrix.py compare taste_runs/run_A.json taste_runs/run_B.json
  python scripts/run_taste_matrix.py score taste_runs/run_latest.json

Outputs: taste_runs/run_<UTC>_<shortid>.json under repo root (gitignored).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS_FILE = ROOT / "scripts" / "taste_prompts.json"
OUT_DIR = ROOT / "taste_runs"

_REDFLAGS = [
    (r"SOURCE\s+CHUNKS", "echoes internal label SOURCE CHUNKS"),
    (r"O\.C\.G\.A\.", "mentions O.C.G.A. (often bad when vault empty)"),
    (r"top\s*0\.01|elite\s+attorney|top\s+appellate\s+attorney", "elite / prestige attorney echo"),
    (r"justia\.com|findlaw\.com|leagle\.com", "website dump"),
    (r"verify the accuracy of (the )?cases", "overclaims verification"),
]


def _body_after_audit_header(text: str) -> str:
    """Skip required **Sources** / **Verified citations** block so O.C.G.A. in boilerplate is not a false redflag."""
    t = text or ""
    if "**Sources in vault:**" in t[:1200]:
        segs = t.split("\n\n", 2)
        if len(segs) >= 3:
            return segs[2]
    return t


def _score_answer(text: str, vault_empty: bool | None) -> tuple[int, list[str]]:
    flags: list[str] = []
    if not (text or "").strip():
        return (1, ["empty answer"])
    scored = _body_after_audit_header(text)
    for rx, msg in _REDFLAGS:
        if re.search(rx, scored, re.I):
            flags.append(msg)
    if vault_empty is True and re.search(r"Kellos|Cox-Ott|\d+\s+Ga\.", scored, re.I):
        flags.append("possible invented reporter cite with empty vault")
    return (len(flags), flags)


def cmd_run(base_url: str, as_json: bool) -> int:
    if not PROMPTS_FILE.is_file():
        print("Missing scripts/taste_prompts.json", file=sys.stderr)
        return 1

    cases = json.loads(PROMPTS_FILE.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"_{int(time.time()) % 10000:04d}"
    out_path = OUT_DIR / f"run_{run_id}.json"

    results: list[dict] = []
    for c in cases:
        cid = c["id"]
        payload = {
            "message": c["message"],
            "session_id": None,
            "search_case_law": c.get("search_case_law", False),
        }
        url = f"{base_url}/v1/chat"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = {"error": str(e), "http": e.code, "body": e.read().decode(errors="replace")[:2000]}
        except Exception as e:
            body = {"error": str(e)}
        dt_ms = int((time.perf_counter() - t0) * 1000)
        ans = (body.get("answer") or "") if isinstance(body, dict) else ""
        ve = body.get("vault_empty") if isinstance(body, dict) else None
        nflags, flist = _score_answer(ans, ve)
        results.append(
            {
                "id": cid,
                "note": c.get("note", ""),
                "message": c["message"],
                "search_case_law": payload["search_case_law"],
                "ms": dt_ms,
                "vault_empty": ve,
                "audit_mode_guess": body.get("audit", {}).get("enabled") if isinstance(body, dict) else None,
                "answer": ans,
                "error": body.get("error") if isinstance(body, dict) else None,
                "heuristic_redflags": nflags,
                "heuristic_flag_detail": flist,
            }
        )

    bundle = {
        "base_url": base_url,
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "total_heuristic_redflags": sum(r.get("heuristic_redflags") or 0 for r in results),
    }
    out_path.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if as_json:
        print(json.dumps(bundle, indent=2, ensure_ascii=False))
        return 0

    print(f"Wrote {out_path}\n")
    print(f"Total heuristic redflags (lower better): {bundle['total_heuristic_redflags']}\n")
    for r in results:
        preview = (r["answer"] or "")[:320].replace("\n", " ")
        flag = "ERR " if r.get("error") else ""
        hf = r.get("heuristic_redflags", 0)
        print(f"--- {flag}{r['id']} ({r['ms']} ms) redflags={hf} vault_empty={r['vault_empty']} ---")
        print(f"    Q: {r['message'][:100]!r}")
        if r.get("heuristic_flag_detail"):
            print(f"    ! {', '.join(r['heuristic_flag_detail'])}")
        print(f"    A: {preview}{'…' if len(r.get('answer') or '') > 320 else ''}\n")

    print("Compare runs: python scripts/run_taste_matrix.py compare OLD NEW")
    return 0


def _load_run(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_compare(path_a: str, path_b: str) -> int:
    pa, pb = Path(path_a), Path(path_b)
    a, b = _load_run(pa), _load_run(pb)
    ra = {r["id"]: r for r in a.get("results", [])}
    rb = {r["id"]: r for r in b.get("results", [])}
    ids = sorted(set(ra) | set(rb))
    print(f"Compare:\n  A: {pa} (run_id={a.get('run_id')})\n  B: {pb} (run_id={b.get('run_id')})\n")
    sum_a = a.get("total_heuristic_redflags")
    sum_b = b.get("total_heuristic_redflags")
    if sum_a is not None and sum_b is not None:
        print(f"Heuristic redflags total: A={sum_a}  B={sum_b}  (delta B-A: {sum_b - sum_a})\n")

    for i in ids:
        if i not in ra:
            print(f"[{i}] only in B\n")
            continue
        if i not in rb:
            print(f"[{i}] only in A\n")
            continue
        xa, xb = ra[i], rb[i]
        la, lb = len(xa.get("answer") or ""), len(xb.get("answer") or "")
        fa, fb = xa.get("heuristic_redflags"), xb.get("heuristic_redflags")
        print(f"=== {i} === len {la} -> {lb}  redflags {fa} -> {fb}")
        if (xa.get("answer") or "") == (xb.get("answer") or ""):
            print("  (identical answers)\n")
            continue

        def peek(t: str, n: int = 12) -> str:
            lines = (t or "").splitlines()[:n]
            return "\n".join(f"  {ln}" for ln in lines)

        print("  --- A ---")
        print(peek(xa.get("answer")))
        print("  --- B ---")
        print(peek(xb.get("answer")))
        print()
    return 0


def cmd_score(path: str) -> int:
    p = Path(path)
    data = _load_run(p)
    print(f"Score: {p}  run_id={data.get('run_id')}\n")
    tot = 0
    for r in data.get("results", []):
        n = r.get("heuristic_redflags", 0)
        tot += n
        print(f"{r['id']}: redflags={n}  {r.get('heuristic_flag_detail') or []}")
    print(f"\nTotal redflags: {tot} (lower is better)\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Lawbot taste matrix: run, compare, score")
    ap.add_argument("--base-url", default=os.environ.get("BASE_URL", "http://127.0.0.1:8765").rstrip("/"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("run", help="POST all prompts and write taste_runs/run_*.json")
    pr.add_argument("--json", action="store_true", dest="as_json")

    pc = sub.add_parser("compare", help="Diff two run JSON files by prompt id")
    pc.add_argument("path_a")
    pc.add_argument("path_b")

    ps = sub.add_parser("score", help="Print heuristic scores from a run JSON")
    ps.add_argument("path")

    args = ap.parse_args()

    if args.cmd == "run":
        return cmd_run(args.base_url, getattr(args, "as_json", False))
    if args.cmd == "compare":
        return cmd_compare(args.path_a, args.path_b)
    if args.cmd == "score":
        return cmd_score(args.path)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
