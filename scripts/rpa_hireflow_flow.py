#!/usr/bin/env python3
"""
Visible HireFlow RPA used when a resume email arrives.

Launches a real Chromium window (slowMo) so you can watch:
  login → upload CV → match jobs → (optional) open Slack tab
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    value = value.strip()
    return value or default


def run_visible_flow(
    cv_path: str | Path,
    *,
    email_from: str = "",
    email_subject: str = "",
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    email = _env("HF_EMAIL")
    password = _env("HF_PASSWORD")
    base_url = _env("HF_BASE_URL", "http://localhost:3000") or "http://localhost:3000"
    slack_url = _env("SLACK_CHANNEL_URL")  # optional, e.g. https://app.slack.com/client/...
    slow_mo = int(_env("SLOW_MO", "500") or "500")
    headless = _env("HEADLESS", "0") == "1"

    cv_file = Path(cv_path).expanduser().resolve()
    if not cv_file.is_file():
        raise FileNotFoundError(f"CV not found: {cv_file}")
    if not email or not password:
        raise RuntimeError("Set HF_EMAIL and HF_PASSWORD in the environment")

    result: dict[str, Any] = {
        "ok": False,
        "candidate_name": cv_file.stem,
        "resume_filename": cv_file.name,
        "email_from": email_from,
        "email_subject": email_subject,
        "best_job_title": None,
        "best_score": None,
        "company": None,
        "message": "",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            slow_mo=slow_mo,
            args=["--start-maximized"],
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        # Login
        page.goto(f"{base_url}/login", wait_until="domcontentloaded")
        page.wait_for_selector('input[type="email"]')
        page.click('input[type="email"]')
        page.type('input[type="email"]', email, delay=70)
        page.click('input[type="password"]')
        page.type('input[type="password"]', password, delay=80)
        page.get_by_role("button", name="Enter console").click()
        page.wait_for_url("**/dashboard**", timeout=45000)

        # CVs
        page.goto(f"{base_url}/resumes", wait_until="domcontentloaded")
        page.wait_for_timeout(800)

        with page.expect_file_chooser() as fc_info:
            page.get_by_text("Upload CV", exact=False).first.click()
        fc_info.value.set_files(str(cv_file))

        # Wait for upload overlay
        try:
            page.wait_for_selector("text=Processing CV", timeout=8000)
            page.wait_for_selector("text=Processing CV", state="detached", timeout=180000)
        except Exception:
            page.wait_for_timeout(10000)

        # Match first row
        match_btn = page.get_by_role("button", name="Match jobs").first
        if match_btn.count() == 0:
            raise RuntimeError("No Match jobs button found after upload")
        match_btn.click()
        try:
            page.wait_for_selector("text=Matching jobs", timeout=8000)
            page.wait_for_selector("text=Matching jobs", state="detached", timeout=300000)
        except Exception:
            page.wait_for_timeout(15000)

        # Scrape best match panel (best-effort)
        try:
            candidate = page.locator("text=Candidate").locator("xpath=following::p[1]").first
            if candidate.count():
                result["candidate_name"] = candidate.inner_text().strip()
        except Exception:
            pass
        try:
            best_title = page.locator("text=Best match").locator("xpath=following::p[1]").first
            if best_title.count():
                result["best_job_title"] = best_title.inner_text().strip()
            company = page.locator("text=Best match").locator("xpath=following::p[2]").first
            if company.count():
                result["company"] = company.inner_text().strip()
            score = page.locator("text=Best match").locator("xpath=ancestor::div[1]").locator("span").filter(has_text="%").first
            if score.count():
                result["best_score"] = score.inner_text().strip()
        except Exception:
            pass

        result["ok"] = True
        result["message"] = "HireFlow UI flow completed"

        # Optional: open Slack so user sees the channel while n8n posts
        if slack_url:
            slack_page = context.new_page()
            slack_page.goto(slack_url, wait_until="domcontentloaded")
            slack_page.wait_for_timeout(4000)

        # Keep window open briefly so user can see the result
        page.bring_to_front()
        page.wait_for_timeout(8000)
        browser.close()

    return result
