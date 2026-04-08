#!/usr/bin/env python3
"""POST the verbatim baseline ask from docs/LAWBOT_QUALITY_BASELINE.md to /v1/chat."""
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BASELINE_MD = REPO / "docs" / "LAWBOT_QUALITY_BASELINE.md"
OUT_JSON = REPO / "docs" / "LAST_LAWBOT_BASELINE_REPLY.json"
OUT_TXT = REPO / "docs" / "LAST_LAWBOT_BASELINE_REPLY.txt"
CHAT_URL = "http://127.0.0.1:8765/v1/chat"
TIMEOUT_SEC = 600


def extract_baseline_message(md: str) -> str:
    m = re.search(
        r"## Baseline ask \(verbatim\).*?```\n(.*?)```\n\n---\n\n## Intent",
        md,
        re.DOTALL,
    )
    if not m:
        raise ValueError("Could not extract fenced baseline message from LAWBOT_QUALITY_BASELINE.md")
    return m.group(1)


def main() -> int:
    md = BASELINE_MD.read_text(encoding="utf-8")
    msg = extract_baseline_message(md)
    payload = {
        "message": msg,
        "session_id": None,
        "search_case_law": True,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        CHAT_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        sys.stderr.write(f"HTTP {e.code}: {err}\n")
        return 1
    except urllib.error.URLError as e:
        sys.stderr.write(f"Request failed: {e}\n")
        return 1

    data = json.loads(raw)
    OUT_JSON.write_text(json.dumps(data, indent=2), encoding="utf-8")
    answer = data.get("answer") or ""
    audit = data.get("audit") or {}
    header = (
        f"task_hint: {audit.get('task_hint')}\n"
        f"citation_audit_enabled: {audit.get('enabled')}\n"
        f"answer_chars: {len(answer)}\n"
        f"---\n\n"
    )
    OUT_TXT.write_text(header + answer, encoding="utf-8")
    print(f"Wrote {OUT_JSON.name} and {OUT_TXT.name}")
    print(f"task_hint={audit.get('task_hint')} audit_enabled={audit.get('enabled')} answer_len={len(answer)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
