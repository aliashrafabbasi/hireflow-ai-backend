from uuid import UUID
import re

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import resume as resume_repository
from app.repositories import resume_skill as resume_skill_repository
from app.repositories import job as job_repository
from app.repositories import job_skill as job_skill_repository
from app.repositories import match_result as match_result_repository
from app.repositories import settings as settings_repository
from app.services.match_analyzer import analyze_match


def _normalize_skills(skills) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []

    for skill in skills:
        name = (skill.skill or "").strip()
        if not name:
            continue

        key = name.lower()
        if key in seen:
            continue

        seen.add(key)
        normalized.append(name)

    return normalized


def _candidate_name_from_filename(filename: str | None) -> str | None:
    if not filename:
        return None

    name = re.sub(r"\.(pdf|docx?)$", "", filename, flags=re.IGNORECASE)
    name = re.sub(r"[-_]+", " ", name)
    name = re.sub(r"\b(resume|cv)\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name).strip()
    return name or None


def _normalize_recommendations(raw) -> list[dict] | None:
    """Coerce stored recommendations into {skill, resource} objects."""
    if raw is None:
        return None
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if isinstance(item, dict) and item.get("skill") is not None:
            out.append(
                {
                    "skill": str(item.get("skill") or ""),
                    "resource": str(item.get("resource") or ""),
                }
            )
        elif isinstance(item, str):
            text = item.strip()
            if not text:
                continue
            skill = text
            for prefix in ("Add or highlight:", "Add:", "Highlight:"):
                if text.lower().startswith(prefix.lower()):
                    skill = text[len(prefix) :].strip()
                    break
            out.append(
                {
                    "skill": skill or text,
                    "resource": text,
                }
            )
    return out


def _to_response(match):
    resume = getattr(match, "resume", None)
    filename = resume.original_filename if resume else None
    candidate_name = None
    if resume:
        candidate_name = resume.candidate_name or _candidate_name_from_filename(
            filename
        )

    job = getattr(match, "job", None)
    checker = getattr(match, "checked_by", None)

    return {
        "id": match.id,
        "resume_id": match.resume_id,
        "job_id": match.job_id,
        "match_score": match.match_score,
        "matched_skills": match.matched_skills or [],
        "missing_skills": match.missing_skills or [],
        "explanation": match.explanation,
        "recommendations": _normalize_recommendations(match.recommendations),
        "created_at": match.created_at,
        "checked_at": match.checked_at,
        "candidate_name": candidate_name,
        "resume_filename": filename,
        "job_title": job.title if job else None,
        "company": job.company if job else None,
        "checked_by_id": match.checked_by_id,
        "checked_by": checker.full_name if checker else None,
        "checked_by_email": checker.email if checker else None,
    }


def calculate_match(
    db: Session,
    resume_id: UUID,
    job_id: UUID,
    force: bool = False,
    checked_by_id: UUID | None = None,
):
    # Reuse cached match to avoid burning LLM tokens
    if not force:
        existing = match_result_repository.get_match_result(
            db, resume_id, job_id
        )
        if existing:
            if checked_by_id is not None:
                existing = match_result_repository.touch_checked_by(
                    db, existing, checked_by_id
                )
            return existing

    resume_skills = _normalize_skills(
        resume_skill_repository.get_resume_skills(db, resume_id)
    )
    job_skills = _normalize_skills(
        job_skill_repository.get_job_skills(db, job_id)
    )
    job = job_repository.get_job_by_id(db, job_id)

    if not job_skills:
        return match_result_repository.upsert_match_result(
            db,
            resume_id,
            job_id,
            0.0,
            [],
            [],
            "No required skills were found for this job.",
            [],
            checked_by_id=checked_by_id,
        )

    try:
        analysis = analyze_match(
            resume_skills,
            job_skills,
            job_title=job.title if job else None,
            job_company=job.company if job else None,
            job_description=job.description if job else None,
        )
    except Exception:
        # Last-resort local score if analyzer raises unexpectedly.
        from app.services.match_analyzer import skill_overlap_match

        analysis = skill_overlap_match(
            resume_skills,
            job_skills,
            job_title=job.title if job else None,
        )

    matched_skills = analysis.get("matched_skills") or []
    missing_skills = analysis.get("missing_skills") or []

    score = analysis.get("match_score")
    if score is None:
        score = (
            (len(matched_skills) / len(job_skills)) * 100
            if job_skills
            else 0
        )
    score = round(float(score), 2)

    return match_result_repository.upsert_match_result(
        db,
        resume_id,
        job_id,
        score,
        matched_skills,
        missing_skills,
        analysis.get("explanation"),
        analysis.get("recommendations") or [],
        checked_by_id=checked_by_id,
    )


def calculate_best_match(
    db: Session,
    resume_id: UUID,
    force: bool = False,
    checked_by_id: UUID | None = None,
):
    resume = resume_repository.get_resume_by_id(db, resume_id)
    if not resume:
        return None

    jobs = job_repository.get_jobs(db)
    if not jobs:
        return {"error": "no_jobs", "resume_id": resume_id}

    threshold = settings_repository.get_match_score_threshold(db)

    summaries = []
    for job in jobs:
        match = calculate_match(
            db,
            resume_id,
            job.id,
            force=force,
            checked_by_id=checked_by_id,
        )
        full = match_result_repository.get_match_result_by_id(db, match.id)
        row = full or match
        job_obj = getattr(row, "job", None) or job

        summaries.append(
            {
                "job_id": row.job_id,
                "job_title": job_obj.title,
                "company": job_obj.company,
                "match_score": row.match_score,
                "matched_skills": row.matched_skills or [],
                "missing_skills": row.missing_skills or [],
                "summary": row.explanation,
            }
        )

    summaries.sort(key=lambda m: m["match_score"], reverse=True)
    best = summaries[0]

    qualified = [m for m in summaries if m["match_score"] >= threshold]
    if not qualified:
        qualified = [best]

    checker_name = None
    if checked_by_id is not None:
        user = db.query(User).filter(User.id == checked_by_id).first()
        checker_name = user.full_name if user else None

    return {
        "resume_id": resume_id,
        "candidate_name": resume.candidate_name
        or _candidate_name_from_filename(resume.original_filename),
        "resume_filename": resume.original_filename,
        "score_threshold": threshold,
        "best_job": best,
        "qualified_jobs": qualified,
        "checked_by_id": checked_by_id,
        "checked_by": checker_name,
    }


def list_all_matches(db: Session, limit: int = 100):
    return [
        _to_response(m)
        for m in match_result_repository.get_all_match_results(db, limit)
    ]


def list_matches_for_resume(db: Session, resume_id: UUID):
    return [
        _to_response(m)
        for m in match_result_repository.get_match_results_by_resume(
            db, resume_id
        )
    ]


def list_matches_for_job(db: Session, job_id: UUID):
    return [
        _to_response(m)
        for m in match_result_repository.get_match_results_by_job(db, job_id)
    ]


def get_match_by_id(db: Session, match_id: UUID):
    match = match_result_repository.get_match_result_by_id(db, match_id)
    if not match:
        return None
    return _to_response(match)


def list_checked_resumes(db: Session, limit: int = 500):
    resumes, by_checker = match_result_repository.get_checked_resumes_summary(
        db, limit=limit
    )
    return {
        "total_checked": len(resumes),
        "by_checker": by_checker,
        "resumes": resumes,
    }


def list_checks(db: Session, user_id: UUID, limit: int = 500):
    """
    Same source as /match/checked — every review attributed to a real user.
    """
    resumes, by_checker = match_result_repository.get_checked_resumes_summary(
        db, limit=limit
    )

    current_user = db.query(User).filter(User.id == user_id).first()
    my_count = 0
    for r in resumes:
        if r.get("checked_by_id") == user_id:
            my_count += 1
            continue
        for u in r.get("checked_by_users") or []:
            if u.get("user_id") == user_id:
                my_count += 1
                break

    people = [
        {
            "user_id": t["user_id"],
            "name": t["full_name"],
            "count": t["resumes_checked"],
        }
        for t in by_checker
        if t.get("user_id")
    ]

    recent = []
    for r in resumes:
        candidate = r.get("candidate_name") or r.get("resume_filename") or "Unknown"
        recent.append(
            {
                "who": r.get("checked_by") or "Unknown",
                "who_id": r.get("checked_by_id"),
                "candidate": candidate,
                "score": r.get("best_score") or 0,
                "when": r.get("checked_at"),
            }
        )

    return {
        "my_id": user_id,
        "my_name": current_user.full_name if current_user else "You",
        "my_count": my_count,
        "people": people,
        "recent": recent,
    }


def get_person_checks(db: Session, person_id: UUID, limit: int = 100):
    return match_result_repository.get_person_check_detail(
        db, person_id=person_id, limit=limit
    )
