#!/usr/bin/env python3
"""
Browser-style smoke test against a running Lawbot server (not file://).

Requires: pip install playwright && playwright install chromium
Run server first: uvicorn lawbot.api.app:app --host 127.0.0.1 --port 8765

Usage:
  BASE_URL=http://127.0.0.1:8765 python scripts/browser_smoke.py
  FULL=1 python scripts/browser_smoke.py   # also sends one chat and waits for reply
"""

from __future__ import annotations

import os
import sys

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8765").rstrip("/")


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install playwright: pip install playwright && playwright install chromium", file=sys.stderr)
        return 1

    full = os.environ.get("FULL", "").strip() in ("1", "true", "yes")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{BASE}/", wait_until="domcontentloaded", timeout=30_000)

        for sel in ("#sendBtn", "#message", "#statusPill"):
            if not page.locator(sel).is_visible():
                print(f"FAIL: not visible {sel}", file=sys.stderr)
                return 1

        page.wait_for_timeout(1500)
        pill = page.locator("#statusPill").inner_text()
        if "checking" in pill.lower() and "disconnected" not in pill.lower():
            pass  # still warming
        print(f"OK: page loaded, status pill: {pill[:60]!r}…")

        if full:
            page.fill("#message", "Reply with exactly one word: browserok")
            page.click("#sendBtn")
            page.wait_for_selector(".msg.assistant:not(.thinking)", timeout=180_000)
            bodies = page.locator(".msg.assistant:not(.thinking) .msg-body")
            last = bodies.nth(bodies.count() - 1).inner_text()
            print(f"OK: assistant message ({len(last)} chars): {last[:240]!r}…")

        browser.close()

    print("browser_smoke: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
