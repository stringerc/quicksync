#!/usr/bin/env python3
"""
Capture Lawbot UI screenshots with Playwright (Chromium).
Requires: pip install playwright && playwright install chromium
Server: uvicorn on http://127.0.0.1:8765

  cd /Users/Apple/lawbot && source .venv/bin/activate && python scripts/capture_ui_screenshots.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "audit-screenshots"
BASE = "http://127.0.0.1:8765/"


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install: pip install playwright && playwright install chromium", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        page.goto(BASE, wait_until="networkidle", timeout=60000)
        page.screenshot(path=str(OUT / "02-loaded.png"), full_page=True)

        # Fast path: turn off case search for a quicker reply
        page.locator("#caseSearchToggle").uncheck()

        page.locator("#message").fill("Say hello in one short sentence.")
        page.screenshot(path=str(OUT / "03-filled.png"), full_page=True)

        page.locator("#sendBtn").click()

        page.wait_for_selector("#lawbotThinking", timeout=10000)
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "04-thinking-steps.png"), full_page=True)

        page.wait_for_selector("#lawbotThinking", state="detached", timeout=180000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "05-reply-with-copy.png"), full_page=True)

        browser.close()

    print(f"Wrote screenshots under {OUT}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
