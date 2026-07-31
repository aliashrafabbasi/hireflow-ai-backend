"""Visible browser RPA for resume email demos (Playwright headed)."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from app.core.config import settings


_WINDOW_W = 1280
_WINDOW_H = 800


def _cdp_raise(page_obj) -> None:
    """Raise a normal-sized window (not fullscreen) so the demo stays visible."""
    try:
        page_obj.bring_to_front()
        cdp = page_obj.context.new_cdp_session(page_obj)
        info = cdp.send("Browser.getWindowForTarget")
        window_id = info.get("windowId")
        if window_id is None:
            return
        cdp.send(
            "Browser.setWindowBounds",
            {
                "windowId": window_id,
                "bounds": {
                    "windowState": "normal",
                    "left": 80,
                    "top": 60,
                    "width": _WINDOW_W,
                    "height": _WINDOW_H,
                },
            },
        )
    except Exception:
        try:
            page_obj.bring_to_front()
        except Exception:
            pass


def _type_visible(page_obj, selector: str, text: str, *, delay_ms: int = 55) -> None:
    """Click field then type at a normal RPA pace (visible, not sluggish)."""
    field = page_obj.locator(selector).first
    field.click()
    page_obj.wait_for_timeout(200)
    field.fill("")
    field.type(text, delay=delay_ms)
    page_obj.wait_for_timeout(250)


def _os_raise_window(*, pin_on_top: bool = True) -> None:
    """Force Chromium above whatever app the user is currently using."""
    if shutil.which("wmctrl"):
        try:
            subprocess.run(
                ["wmctrl", "-a", "Chromium"],
                check=False,
                timeout=2,
                capture_output=True,
            )
            subprocess.run(
                ["wmctrl", "-a", "Chrome"],
                check=False,
                timeout=2,
                capture_output=True,
            )
            if pin_on_top:
                subprocess.run(
                    ["wmctrl", "-r", ":ACTIVE:", "-b", "add,above"],
                    check=False,
                    timeout=2,
                    capture_output=True,
                )
        except Exception:
            pass

    if shutil.which("xdotool"):
        try:
            script = (
                "ids=$(xdotool search --class chromium || true); "
                "ids=\"$ids $(xdotool search --class Chromium || true)\"; "
                "for id in $ids; do "
                "  xdotool windowactivate --sync \"$id\" 2>/dev/null; "
                "  xdotool windowraise \"$id\" 2>/dev/null; "
                "done"
            )
            subprocess.run(
                ["bash", "-lc", script],
                check=False,
                timeout=3,
                capture_output=True,
            )
        except Exception:
            pass


def _unpin_window() -> None:
    if not shutil.which("wmctrl"):
        return
    try:
        subprocess.run(
            ["wmctrl", "-r", ":ACTIVE:", "-b", "remove,above"],
            check=False,
            timeout=2,
            capture_output=True,
        )
    except Exception:
        pass


def _launch_browser(p, *, headless: bool, slow_mo: int):
    launch_env = os.environ.copy()
    launch_env.setdefault("GDK_BACKEND", "x11")
    browser = p.chromium.launch(
        headless=headless,
        slow_mo=slow_mo,
        env=launch_env,
        args=[
            f"--window-size={_WINDOW_W},{_WINDOW_H}",
            "--window-position=80,60",
            "--disable-features=CalculateNativeWinOcclusion",
        ],
    )
    context = browser.new_context(
        viewport={"width": _WINDOW_W - 16, "height": _WINDOW_H - 88},
    )
    page = context.new_page()
    return browser, page


def _focus(page_obj, pause_ms: int = 600) -> None:
    _cdp_raise(page_obj)
    _os_raise_window(pin_on_top=True)
    page_obj.wait_for_timeout(pause_ms)


def show_slack_channel(*, hold_ms: int = 12000) -> dict[str, Any]:
    """Open Slack in a visible browser AFTER n8n posts, so the new message is on screen."""
    import time

    from playwright.sync_api import sync_playwright

    slack_url = settings.SLACK_CHANNEL_URL
    if not slack_url:
        raise RuntimeError("Set SLACK_CHANNEL_URL in .env")

    headless = settings.RPA_HEADLESS
    slow_mo = min(max(settings.RPA_SLOW_MO_MS, 80), 200)

    # Give Slack API a moment to deliver the message n8n just posted.
    time.sleep(2)

    with sync_playwright() as p:
        browser, page = _launch_browser(p, headless=headless, slow_mo=slow_mo)
        try:
            _focus(page, 400)
            page.goto(slack_url, wait_until="domcontentloaded")
            _focus(page, 1500)
            # Refresh so the newest channel message is visible.
            page.reload(wait_until="domcontentloaded")
            _focus(page, hold_ms)
        finally:
            _unpin_window()
            browser.close()

    return {"ok": True, "message": "Slack channel shown in browser"}


def run_visible_flow(
    cv_path: str | Path,
    *,
    email_from: str = "",
    email_subject: str = "",
) -> dict[str, Any]:
    from playwright.sync_api import sync_playwright

    if not settings.RPA_ENABLED:
        raise RuntimeError("RPA is disabled. Set RPA_ENABLED=true in .env")

    email = settings.RPA_UI_EMAIL or settings.HF_EMAIL
    password = settings.RPA_UI_PASSWORD or settings.HF_PASSWORD
    base_url = settings.HF_BASE_URL
    # Standard RPA pace (visible typing, not ultra-slow).
    slow_mo = min(max(settings.RPA_SLOW_MO_MS, 80), 200)
    headless = settings.RPA_HEADLESS

    cv_file = Path(cv_path).expanduser().resolve()
    if not cv_file.is_file():
        raise FileNotFoundError(f"CV not found: {cv_file}")
    if not email or not password:
        raise RuntimeError(
            "Set HF_EMAIL and HF_PASSWORD (or RPA_UI_EMAIL / RPA_UI_PASSWORD) in .env"
        )

    result: dict[str, Any] = {
        "ok": False,
        "candidate_name": None,
        "resume_filename": cv_file.name,
        "email_from": email_from,
        "email_subject": email_subject,
        "best_job_title": None,
        "best_score": None,
        "company": None,
        "message": "",
    }

    with sync_playwright() as p:
        browser, page = _launch_browser(p, headless=headless, slow_mo=slow_mo)
        try:
            _focus(page, 400)

            page.goto(f"{base_url}/login", wait_until="domcontentloaded")
            _focus(page, 700)
            page.wait_for_selector('input[type="email"]')
            _type_visible(page, 'input[type="email"]', email, delay_ms=55)
            _type_visible(page, 'input[type="password"]', password, delay_ms=60)
            page.get_by_role("button", name="Enter console").click()
            page.wait_for_url("**/dashboard**", timeout=45000)
            _focus(page, 800)

            page.goto(f"{base_url}/resumes", wait_until="domcontentloaded")
            _focus(page, 600)

            upload_name = cv_file.name

            with page.expect_file_chooser() as fc_info:
                page.get_by_text("Upload CV", exact=False).first.click()
            fc_info.value.set_files(str(cv_file))
            _focus(page, 500)

            try:
                page.wait_for_selector("text=Processing CV", timeout=8000)
                page.wait_for_selector(
                    "text=Processing CV", state="detached", timeout=180000
                )
            except Exception:
                page.wait_for_timeout(5000)

            # Upload failed (e.g. hard error) → STOP. Never Match an older CV.
            err = page.locator('[data-testid="page-error"]')
            if err.count():
                msg = (err.first.inner_text() or "").strip() or "Upload failed"
                raise RuntimeError(f"Upload failed — stopping RPA: {msg}")

            # Target ONLY the CV we just uploaded (newest list is desc by uploaded_at).
            row = page.locator(
                f'[data-testid="resume-row"][data-resume-filename="{upload_name}"]'
            ).first
            if row.count() == 0:
                # Filename may be normalized / UUID-stored; fall back carefully.
                stem = cv_file.stem.replace("-", " ").replace("_", " ").lower()
                rows = page.locator('[data-testid="resume-row"]')
                matched_row = None
                # Prefer the newest row (index 0) after a successful upload.
                if rows.count() > 0:
                    matched_row = rows.first
                for i in range(min(rows.count(), 10)):
                    r = rows.nth(i)
                    label = (
                        r.locator('[data-testid="resume-name"]').inner_text() or ""
                    ).lower()
                    fname = (r.get_attribute("data-resume-filename") or "").lower()
                    if (
                        stem in label
                        or stem in fname
                        or upload_name.lower() in fname
                    ):
                        matched_row = r
                        break
                if matched_row is None:
                    raise RuntimeError(
                        f"Uploaded CV “{upload_name}” not found in list — "
                        "refusing to Match an older resume."
                    )
                row = matched_row

            # Prefer HireFlow-extracted name from the list (not the PDF filename).
            try:
                listed = row.locator('[data-testid="resume-name"]').first
                if listed.count():
                    listed_name = listed.inner_text().strip()
                    # Skip UUID / tempfile labels that mirror the attachment name.
                    compact = listed_name.replace(" ", "").replace("-", "")
                    bad = (
                        not listed_name
                        or (len(compact) >= 32 and compact.isalnum()
                            and all(c in "0123456789abcdefABCDEF" for c in compact))
                        or listed_name.lower().startswith("tmp")
                    )
                    if listed_name and not bad:
                        result["candidate_name"] = listed_name
            except Exception:
                pass

            match_btn = row.locator('[data-testid="match-jobs-btn"]')
            if match_btn.count() == 0:
                match_btn = row.get_by_role("button", name="Match jobs")
            if match_btn.count() == 0:
                raise RuntimeError(
                    f"No Match jobs button for uploaded CV “{upload_name}”"
                )
            match_btn.click()
            _focus(page, 500)
            try:
                page.wait_for_selector("text=Matching jobs", timeout=8000)
                page.wait_for_selector(
                    "text=Matching jobs", state="detached", timeout=300000
                )
            except Exception:
                page.wait_for_timeout(12000)

            # Match UI error → STOP (don't scrape stale panel).
            err = page.locator('[data-testid="page-error"]')
            if err.count():
                msg = (err.first.inner_text() or "").strip() or "Match failed"
                raise RuntimeError(f"Match failed — stopping RPA: {msg}")

            page.wait_for_selector('[data-testid="best-match-card"]', timeout=15000)

            try:
                candidate = page.locator('[data-testid="match-candidate"]').first
                if candidate.count():
                    scraped = candidate.inner_text().strip()
                    compact = scraped.replace(" ", "").replace("-", "")
                    bad = (
                        not scraped
                        or (len(compact) >= 32 and compact.isalnum()
                            and all(c in "0123456789abcdefABCDEF" for c in compact))
                        or scraped.lower().startswith("tmp")
                    )
                    if scraped and not bad:
                        result["candidate_name"] = scraped
            except Exception:
                pass
            try:
                best_title = page.locator('[data-testid="best-match-title"]').first
                if best_title.count():
                    result["best_job_title"] = best_title.inner_text().strip()
                company = page.locator('[data-testid="best-match-company"]').first
                if company.count():
                    result["company"] = company.inner_text().strip()
                score = page.locator(
                    '[data-testid="best-match-card"] [data-testid="score-pill"]'
                ).first
                if score.count():
                    result["best_score"] = (
                        score.get_attribute("data-score")
                        or score.inner_text().strip()
                    )
                    if result["best_score"] and not str(
                        result["best_score"]
                    ).endswith("%"):
                        result["best_score"] = f"{result['best_score']}%"
            except Exception:
                pass

            _focus(page, 3500)

            if not result.get("best_job_title") or not result.get("best_score"):
                raise RuntimeError(
                    "Match finished but best-match score was not shown for the "
                    f"uploaded CV “{upload_name}”."
                )

            result["ok"] = True
            result["message"] = "HireFlow UI flow completed"
        finally:
            _unpin_window()
            browser.close()

    return result
