#!/usr/bin/env python3
"""
Local webhook for n8n:

  Gmail (attachment) → POST /automation/run → visible Playwright browser
  → returns match summary → n8n posts Slack

Run (keep this terminal open):
  export HF_EMAIL='...'
  export HF_PASSWORD='...'
  export HF_BASE_URL='http://localhost:3000'
  # optional: export SLACK_CHANNEL_URL='https://app.slack.com/...'
  uvicorn scripts.rpa_mail_server:app --host 127.0.0.1 --port 8765
"""

from __future__ import annotations

import tempfile
import traceback
from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse

from scripts.rpa_hireflow_flow import run_visible_flow

app = FastAPI(title="HireFlow Mail RPA", version="1.0.0")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/automation/run")
async def automation_run(
    file: UploadFile = File(...),
    email_from: str = Form(""),
    email_subject: str = Form(""),
    candidate_name: str = Form(""),
):
    suffix = Path(file.filename or "resume.pdf").suffix or ".pdf"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        result = run_visible_flow(
            tmp_path,
            email_from=email_from,
            email_subject=email_subject,
        )
        if candidate_name:
            result["candidate_name"] = candidate_name
        result["resume_filename"] = file.filename or result.get("resume_filename")
        return result
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "trace": traceback.format_exc()[-2000:],
                "email_from": email_from,
                "email_subject": email_subject,
                "resume_filename": file.filename,
            },
        )
    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
