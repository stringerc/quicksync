#!/usr/bin/env python3
"""
Heuristic gate for docs/LAST_LAWBOT_BASELINE_REPLY.json after scripts/post_baseline_message.py.
Exit 0 = passes baseline "must not" / routing checks; exit 1 = fail with reasons.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
JSON_PATH = REPO / "docs" / "LAST_LAWBOT_BASELINE_REPLY.json"

# Must-not substrings (baseline drafting ask — not verification-as-primary).
FORBIDDEN = (
    "this is a citation verification task",
    "vault vs not",
    "source chunk chk_",
    "matches what we loaded",
    "not verified in vault this session",
    "general tips",
)

# Should be present for strengthen path.
WANT_TASK = "strengthen_filing"


def main() -> int:
    if not JSON_PATH.is_file():
        print(f"Missing {JSON_PATH} — run scripts/post_baseline_message.py first.", file=sys.stderr)
        return 1
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    ans = (data.get("answer") or "").lower()
    audit = data.get("audit") or {}
    fails: list[str] = []

    if audit.get("task_hint") != WANT_TASK:
        fails.append(f"task_hint want {WANT_TASK!r}, got {audit.get('task_hint')!r}")
    if audit.get("enabled") is not False:
        fails.append(f"audit.enabled should be False for drafting-first, got {audit.get('enabled')!r}")

    for phrase in FORBIDDEN:
        if phrase in ans:
            fails.append(f"forbidden phrase in answer: {phrase!r}")

    if re.search(r"\bohio\b.*\b(state v\.|district)\b", ans):
        fails.append("answer mentions Ohio / unrelated state noise")

    if fails:
        print("BASELINE CHECK FAILED:")
        for f in fails:
            print(f"  - {f}")
        return 1

    n = len(data.get("answer") or "")
    print(f"BASELINE CHECK OK (answer_chars={n}, task_hint={WANT_TASK}, audit_enabled=False)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
