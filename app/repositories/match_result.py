from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.match_result import MatchResult
from app.models.resume import Resume
from app.models.user import User


def upsert_match_result(
    db: Session,
    resume_id: UUID,
    job_id: UUID,
    match_score: float,
    matched_skills: list[str],
    missing_skills: list[str],
    explanation: str = None,
    recommendations: list[dict] = None,
    checked_by_id: UUID | None = None,
):
    existing = (
        db.query(MatchResult)
        .filter(
            MatchResult.resume_id == resume_id,
            MatchResult.job_id == job_id,
        )
        .order_by(MatchResult.created_at.desc())
        .first()
    )

    now = datetime.utcnow()

    if existing:
        existing.match_score = match_score
        existing.matched_skills = matched_skills
        existing.missing_skills = missing_skills
        existing.explanation = explanation
        existing.recommendations = recommendations
        if checked_by_id is not None:
            existing.checked_by_id = checked_by_id
            existing.checked_at = now
        db.commit()
        db.refresh(existing)
        return existing

    match_result = MatchResult(
        resume_id=resume_id,
        job_id=job_id,
        match_score=match_score,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        explanation=explanation,
        recommendations=recommendations,
        checked_by_id=checked_by_id,
        checked_at=now if checked_by_id else None,
        created_at=now,
    )

    db.add(match_result)
    db.commit()
    db.refresh(match_result)
    return match_result


def create_match_result(
    db: Session,
    resume_id: UUID,
    job_id: UUID,
    match_score: float,
    matched_skills: list[str],
    missing_skills: list[str],
    explanation: str = None,
    recommendations: list[dict] = None,
    checked_by_id: UUID | None = None,
):
    """Backward-compatible alias — always upserts. """
    return upsert_match_result(
        db,
        resume_id,
        job_id,
        match_score,
        matched_skills,
        missing_skills,
        explanation,
        recommendations,
        checked_by_id=checked_by_id,
    )


def touch_checked_by(
    db: Session,
    match: MatchResult,
    checked_by_id: UUID,
):
    """Record who re-checked a cached match without re-scoring."""
    match.checked_by_id = checked_by_id
    match.checked_at = datetime.utcnow()
    db.commit()
    db.refresh(match)
    return match


def get_match_result(
    db: Session,
    resume_id: UUID,
    job_id: UUID,
):
    return (
        db.query(MatchResult)
        .filter(
            MatchResult.resume_id == resume_id,
            MatchResult.job_id == job_id,
        )
        .order_by(MatchResult.created_at.desc())
        .first()
    )


def _with_relations(query):
    return query.options(
        joinedload(MatchResult.resume).joinedload(Resume.user),
        joinedload(MatchResult.job),
        joinedload(MatchResult.checked_by),
    )


def get_match_result_by_id(db: Session, match_id: UUID):
    return (
        _with_relations(db.query(MatchResult))
        .join(Resume, MatchResult.resume_id == Resume.id)
        .join(User, Resume.user_id == User.id)
        .filter(User.role != "user")
        .filter(MatchResult.id == match_id)
        .first()
    )


def get_all_match_results(db: Session, limit: int = 100):
    return (
        _with_relations(db.query(MatchResult))
        .join(Resume, MatchResult.resume_id == Resume.id)
        .join(User, Resume.user_id == User.id)
        .filter(User.role != "user")
        .order_by(MatchResult.created_at.desc())
        .limit(limit)
        .all()
    )


def get_match_results_by_resume(db: Session, resume_id: UUID):
    return (
        _with_relations(db.query(MatchResult))
        .join(Resume, MatchResult.resume_id == Resume.id)
        .join(User, Resume.user_id == User.id)
        .filter(MatchResult.resume_id == resume_id)
        .filter(User.role != "user")
        .order_by(MatchResult.match_score.desc(), MatchResult.created_at.desc())
        .all()
    )


def get_match_results_by_job(db: Session, job_id: UUID):
    return (
        _with_relations(db.query(MatchResult))
        .join(Resume, MatchResult.resume_id == Resume.id)
        .join(User, Resume.user_id == User.id)
        .filter(MatchResult.job_id == job_id)
        .filter(User.role != "user")
        .order_by(MatchResult.match_score.desc(), MatchResult.created_at.desc())
        .all()
    )


def get_checked_resumes_summary(db: Session, limit: int = 500):
    """
    One row per resume that has been matched at least once.
    Always attributes to a real user: checked_by, else resume uploader.
    """
    aggregates = (
        db.query(
            MatchResult.resume_id,
            func.count(MatchResult.id).label("jobs_matched"),
            func.max(MatchResult.match_score).label("best_score"),
            func.max(MatchResult.checked_at).label("last_checked_at"),
            func.max(MatchResult.created_at).label("last_created_at"),
        )
        .join(Resume, MatchResult.resume_id == Resume.id)
        .join(User, Resume.user_id == User.id)
        .filter(User.role != "user")
        .group_by(MatchResult.resume_id)
        .order_by(
            func.coalesce(
                func.max(MatchResult.checked_at),
                func.max(MatchResult.created_at),
            ).desc()
        )
        .limit(limit)
        .all()
    )

    if not aggregates:
        return [], []

    resume_ids = [row.resume_id for row in aggregates]

    matches = (
        _with_relations(db.query(MatchResult))
        .join(Resume, MatchResult.resume_id == Resume.id)
        .join(User, Resume.user_id == User.id)
        .filter(MatchResult.resume_id.in_(resume_ids))
        .filter(User.role != "user")
        .all()
    )

    by_resume: dict = {}
    for m in matches:
        bucket = by_resume.setdefault(
            m.resume_id,
            {"rows": [], "checkers": {}},
        )
        bucket["rows"].append(m)

        actor = m.checked_by
        if actor is None and m.resume is not None:
            actor = getattr(m.resume, "user", None)
        if actor is not None:
            bucket["checkers"][actor.id] = actor

    resumes_out = []
    for agg in aggregates:
        bucket = by_resume.get(agg.resume_id, {"rows": [], "checkers": {}})
        rows = bucket["rows"]
        rows_sorted = sorted(
            rows,
            key=lambda r: (r.checked_at or r.created_at or datetime.min),
            reverse=True,
        )
        latest = rows_sorted[0] if rows_sorted else None
        resume = latest.resume if latest else None

        checker = latest.checked_by if latest else None
        if checker is None and resume is not None:
            checker = getattr(resume, "user", None)

        checkers_list = [
            {
                "user_id": u.id,
                "full_name": u.full_name,
                "email": u.email,
            }
            for u in bucket["checkers"].values()
        ]

        # Primary reviewer for list view: explicit checker, else first known actor
        if checker is None and checkers_list:
            first = next(iter(bucket["checkers"].values()))
            checker = first

        resumes_out.append(
            {
                "resume_id": agg.resume_id,
                "candidate_name": (
                    resume.candidate_name if resume else None
                ),
                "resume_filename": (
                    resume.original_filename if resume else None
                ),
                "jobs_matched": agg.jobs_matched,
                "best_score": float(agg.best_score or 0),
                "checked_at": agg.last_checked_at or agg.last_created_at,
                "checked_by_id": checker.id if checker else None,
                "checked_by": checker.full_name if checker else "Unknown",
                "checked_by_email": checker.email if checker else None,
                "checked_by_users": checkers_list,
            }
        )

    ever_checked: dict = {}
    for item in resumes_out:
        actors = item["checked_by_users"]
        if not actors and item.get("checked_by_id"):
            actors = [
                {
                    "user_id": item["checked_by_id"],
                    "full_name": item["checked_by"],
                    "email": item.get("checked_by_email"),
                }
            ]
        for u in actors:
            key = u["user_id"]
            if key not in ever_checked:
                ever_checked[key] = {
                    "user_id": u["user_id"],
                    "full_name": u["full_name"],
                    "email": u.get("email"),
                    "resumes_checked": 0,
                }
            ever_checked[key]["resumes_checked"] += 1

    by_checker = sorted(
        ever_checked.values(),
        key=lambda x: x["resumes_checked"],
        reverse=True,
    )

    return resumes_out, by_checker


def get_checks_for_user(db: Session, user_id: UUID, limit: int = 200):
    """
    Clear accountability view:
    - unique resumes each staff member has checked
    - chronological sequence of checks
    - focused "me" block for the logged-in user
    """
    # One row per (checker, resume) with latest check time + best score
    pairs = (
        db.query(
            MatchResult.checked_by_id,
            MatchResult.resume_id,
            func.max(MatchResult.checked_at).label("checked_at"),
            func.max(MatchResult.match_score).label("best_score"),
        )
        .join(Resume, MatchResult.resume_id == Resume.id)
        .join(User, Resume.user_id == User.id)
        .filter(MatchResult.checked_by_id.isnot(None))
        .filter(User.role != "user")
        .group_by(MatchResult.checked_by_id, MatchResult.resume_id)
        .order_by(func.max(MatchResult.checked_at).desc().nullslast())
        .limit(limit)
        .all()
    )

    current_user = db.query(User).filter(User.id == user_id).first()
    me = {
        "user_id": user_id,
        "full_name": current_user.full_name if current_user else "You",
        "email": current_user.email if current_user else "",
        "resumes_checked": 0,
        "resumes": [],
    }

    if not pairs:
        return {
            "total_unique_resumes": 0,
            "me": me,
            "team": [],
            "sequence": [],
        }

    resume_ids = list({p.resume_id for p in pairs})
    user_ids = list({p.checked_by_id for p in pairs})

    resumes = {
        r.id: r
        for r in db.query(Resume).filter(Resume.id.in_(resume_ids)).all()
    }
    users = {
        u.id: u
        for u in db.query(User).filter(User.id.in_(user_ids)).all()
    }

    sequence = []
    team_map: dict = {}

    for p in pairs:
        user = users.get(p.checked_by_id)
        resume = resumes.get(p.resume_id)
        if not user:
            continue

        item = {
            "resume_id": p.resume_id,
            "candidate_name": resume.candidate_name if resume else None,
            "resume_filename": resume.original_filename if resume else None,
            "checked_by_id": user.id,
            "checked_by": user.full_name,
            "checked_by_email": user.email,
            "checked_at": p.checked_at,
            "best_score": float(p.best_score or 0),
        }
        sequence.append(item)

        bucket = team_map.setdefault(
            user.id,
            {
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "resumes_checked": 0,
            },
        )
        bucket["resumes_checked"] += 1

        if user.id == user_id:
            me["resumes"].append(item)

    me["resumes_checked"] = len(me["resumes"])

    team = sorted(
        team_map.values(),
        key=lambda x: x["resumes_checked"],
        reverse=True,
    )

    unique_resumes = len({s["resume_id"] for s in sequence})

    return {
        "total_unique_resumes": unique_resumes,
        "me": me,
        "team": team,
        "sequence": sequence,
    }


def get_person_check_detail(db: Session, person_id: UUID, limit: int = 100):
    """All resumes checked by one staff member, with best score + job."""
    person = db.query(User).filter(User.id == person_id).first()
    if not person:
        return None

    # Latest check time + best score per resume for this checker
    pairs = (
        db.query(
            MatchResult.resume_id,
            func.max(MatchResult.checked_at).label("checked_at"),
            func.max(MatchResult.match_score).label("best_score"),
        )
        .join(Resume, MatchResult.resume_id == Resume.id)
        .join(User, Resume.user_id == User.id)
        .filter(MatchResult.checked_by_id == person_id)
        .filter(User.role != "user")
        .group_by(MatchResult.resume_id)
        .order_by(func.max(MatchResult.checked_at).desc().nullslast())
        .limit(limit)
        .all()
    )

    items = []
    for p in pairs:
        # Row with best score for this resume+checker (prefer highest score)
        best_row = (
            _with_relations(db.query(MatchResult))
            .filter(
                MatchResult.resume_id == p.resume_id,
                MatchResult.checked_by_id == person_id,
            )
            .order_by(
                MatchResult.match_score.desc(),
                MatchResult.checked_at.desc().nullslast(),
            )
            .first()
        )
        resume = best_row.resume if best_row else None
        job = best_row.job if best_row else None
        candidate = (
            (resume.candidate_name if resume else None)
            or (resume.original_filename if resume else None)
            or "Unknown"
        )
        items.append(
            {
                "resume_id": p.resume_id,
                "job_id": best_row.job_id if best_row else None,
                "candidate": candidate,
                "score": float(
                    (best_row.match_score if best_row else p.best_score) or 0
                ),
                "best_job": job.title if job else None,
                "company": job.company if job else None,
                "when": p.checked_at
                or (best_row.checked_at if best_row else None),
                "matched_skills": (best_row.matched_skills if best_row else None)
                or [],
                "missing_skills": (best_row.missing_skills if best_row else None)
                or [],
                "explanation": best_row.explanation if best_row else None,
            }
        )

    return {
        "user_id": person.id,
        "name": person.full_name,
        "email": person.email,
        "count": len(items),
        "resumes": items,
    }
