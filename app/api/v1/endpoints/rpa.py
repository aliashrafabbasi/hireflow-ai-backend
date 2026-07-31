"""Trigger visible browser RPA when n8n receives a resume email."""

from __future__ import annotations

import asyncio
import re
import tempfile
import traceback
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.config import settings
from app.dependencies.auth import get_current_staff
from app.services.rpa_browser import run_visible_flow, show_slack_channel

router = APIRouter(prefix="/rpa", tags=["RPA"])


class ShowSlackBody(BaseModel):
    hold_ms: int = Field(default=12000, ge=3000, le=60000)


_UUID_NAME_RE = re.compile(
    r"^[0-9a-f]{8}[- ]?[0-9a-f]{4}[- ]?[0-9a-f]{4}[- ]?[0-9a-f]{4}[- ]?[0-9a-f]{12}$",
    re.I,
)


def _is_bad_candidate_name(name: str | None) -> bool:
    """True for empty / UUID / tempfile stems that should not go to Slack."""
    n = (name or "").strip()
    if not n:
        return True
    if _UUID_NAME_RE.match(n):
        return True
    compact = re.sub(r"[\s\-]", "", n)
    if len(compact) >= 32 and re.fullmatch(r"[0-9a-fA-F]+", compact):
        return True
    if n.lower().startswith("tmp") and len(n) <= 20:
        return True
    return False


def _pick_candidate_name(*names: str | None) -> str | None:
    """Prefer a real human name; never fall back to UUID/tmp stubs."""
    for name in names:
        if name and not _is_bad_candidate_name(name):
            return name.strip()
    return None


@router.post("/automation/run")
async def automation_run(
    file: UploadFile = File(...),
    email_from: str = Form(""),
    email_subject: str = Form(""),
    candidate_name: str = Form(""),
    _=Depends(get_current_staff),
):
    """
    Starts a headed Playwright browser on this machine:
    login → upload CV → match jobs → close browser.
    Called by n8n when a resume email arrives.
    """
    if not settings.RPA_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="RPA disabled. Set RPA_ENABLED=true in backend .env",
        )

    original_name = Path(file.filename or "resume.pdf").name
    # Keep the email attachment's real filename so HireFlow stores/shows it correctly.
    safe_name = (
        re.sub(r"[^\w.\- ()\[\]]+", "_", original_name).strip("._") or "resume.pdf"
    )
    tmp_dir = tempfile.mkdtemp(prefix="hireflow-rpa-")
    tmp_path = str(Path(tmp_dir) / safe_name)
    try:
        Path(tmp_path).write_bytes(await file.read())

        result = await asyncio.to_thread(
            run_visible_flow,
            tmp_path,
            email_from=email_from,
            email_subject=email_subject,
        )
        # Never let UUID/filename stubs overwrite a real scraped/DB name.
        result["candidate_name"] = _pick_candidate_name(
            result.get("candidate_name"),
            candidate_name,
        )
        result["resume_filename"] = original_name or result.get("resume_filename")
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "ok": False,
                "error": str(e),
                "trace": traceback.format_exc()[-1500:],
            },
        ) from e
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
            Path(tmp_dir).rmdir()
        except OSError:
            pass


@router.post("/show-slack")
async def show_slack(
    body: ShowSlackBody | None = None,
    _=Depends(get_current_staff),
):
    """Open Slack in a visible browser after n8n has already posted the message."""
    if not settings.RPA_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="RPA disabled. Set RPA_ENABLED=true in backend .env",
        )
    hold_ms = body.hold_ms if body else 12000
    try:
        return await asyncio.to_thread(show_slack_channel, hold_ms=hold_ms)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"ok": False, "error": str(e)},
        ) from e
