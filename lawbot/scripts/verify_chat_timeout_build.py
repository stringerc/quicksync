#!/usr/bin/env python3
"""
Verify chat timeout formula and optional mega-file stats (no LLM required).

  python scripts/verify_chat_timeout_build.py
  python scripts/verify_chat_timeout_build.py path/to/your_paste.txt
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.test_chat_timeout_formula import chat_timeout_ms  # noqa: E402


def main() -> int:
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        if not p.is_file():
            print(f"Not a file: {p}", file=sys.stderr)
            return 1
        n = len(p.read_text(encoding="utf-8"))
    else:
        n = 65_000
        print("(no file arg — using 65,000 chars as example mega-paste size)\n")
    ms = chat_timeout_ms(n, search_case_law=True, two_phase_filing=True)
    print(f"characters: {n}")
    print(f"browser wait (chatTimeoutMs, search + two-phase when paste ≥8k): {ms} ms ({ms / 60_000:.2f} minutes)")
    print("\nTo live-test: start Lawbot, paste the same text in the UI, and watch the browser console for timeoutMin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
