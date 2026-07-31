#!/usr/bin/env python3
"""
HireFlow visible RPA demo (Playwright).

Opens a REAL browser window so you can watch:
  login → CVs page → upload CV → Match jobs

Usage:
  pip install playwright
  playwright install chromium

  export HF_EMAIL='you@example.com'
  export HF_PASSWORD='your-password'
  export HF_CV='/path/to/resume.pdf'   # optional
  export HF_BASE_URL='http://localhost:3000'

  python scripts/rpa_hireflow_demo.py

Tips:
  - Frontend (:3000) + backend (:8000) must be running
  - HEADLESS=1 to hide browser (default is visible)
  - SLOW_MO=600  (ms delay between actions — higher = easier to watch)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright missing. Run:")
        print("  pip install playwright && playwright install chromium")
        return 1

    email = env("HF_EMAIL")
    password = env("HF_PASSWORD")
    base_url = env("HF_BASE_URL", "http://localhost:3000") or "http://localhost:3000"
    cv_path = env("HF_CV")
    headless = env("HEADLESS", "0") == "1"
    slow_mo = int(env("SLOW_MO", "550") or "550")

    if not email or not password:
        print("Set HF_EMAIL and HF_PASSWORD first.")
        print("Example:")
        print("  export HF_EMAIL='admin@example.com'")
        print("  export HF_PASSWORD='secret'")
        return 1

    if cv_path:
        cv_file = Path(cv_path).expanduser().resolve()
        if not cv_file.is_file():
            print(f"CV not found: {cv_file}")
            return 1
    else:
        # pick newest pdf under uploads/resumes if present
        uploads = Path(__file__).resolve().parents[1] / "uploads" / "resumes"
        pdfs = sorted(uploads.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
        cv_file = pdfs[0] if pdfs else None

    print("Starting visible browser…")
    print(f"  URL: {base_url}")
    print(f"  Email: {email}")
    print(f"  Slow-mo: {slow_mo}ms  headless={headless}")
    if cv_file:
        print(f"  CV: {cv_file}")
    else:
        print("  CV: (none — will only login + open CVs page)")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=["--start-maximized"],
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        # 1) Login — typing is visible because of slow_mo
        page.goto(f"{base_url}/login", wait_until="domcontentloaded")
        page.wait_for_selector('input[type="email"]')

        page.click('input[type="email"]')
        page.type('input[type="email"]', email, delay=80)

        page.click('input[type="password"]')
        # password field shows dots, but each keystroke is visibly delayed
        page.type('input[type="password"]', password, delay=90)

        page.get_by_role("button", name="Enter console").click()
        page.wait_for_url("**/dashboard**", timeout=30000)
        print("Logged in → dashboard")

        # 2) Go to CVs
        page.goto(f"{base_url}/resumes", wait_until="domcontentloaded")
        page.wait_for_timeout(1200)
        print("Opened CVs page")

        # 3) Upload CV if available
        if cv_file:
            with page.expect_file_chooser() as fc_info:
                page.get_by_text("Upload CV", exact=False).first.click()
            chooser = fc_info.value
            chooser.set_files(str(cv_file))
            print("Uploading / analyzing CV (watch the loader)…")
            # wait for overlay to appear then disappear (best effort)
            page.wait_for_timeout(2000)
            try:
                page.wait_for_selector("text=Processing CV", timeout=5000)
                page.wait_for_selector("text=Processing CV", state="detached", timeout=180000)
            except Exception:
                page.wait_for_timeout(8000)
            print("Upload finished (or timed out waiting for loader)")

            # 4) Match first CV row if button exists
            match_btn = page.get_by_role("button", name="Match jobs").first
            if match_btn.count() > 0:
                match_btn.click()
                print("Matching jobs (watch the loader)…")
                try:
                    page.wait_for_selector("text=Matching jobs", timeout=5000)
                    page.wait_for_selector("text=Matching jobs", state="detached", timeout=300000)
                except Exception:
                    page.wait_for_timeout(10000)
                print("Match finished")

        print("Demo complete — browser stays open 12s so you can look around")
        time.sleep(12)
        browser.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
