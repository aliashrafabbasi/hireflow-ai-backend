import json
from uuid import UUID

from groq import RateLimitError
from sqlalchemy.orm import Session

from app.core.exceptions import LLMRateLimitError
from app.models.user import User
from app.prompts.career_prompt import CAREER_ANALYSIS_PROMPT
from app.prompts.career_chat_prompt import CAREER_CHAT_PROMPT
from app.repositories import job as job_repository
from app.repositories import resume as resume_repository
from app.repositories import resume_skill as resume_skill_repository
from app.services.llm import client
from app.services.matching import calculate_match

MATCH_SCORE_THRESHOLD = 60.0


def _get_owned_resume(db: Session, resume_id: UUID, user: User):
    resume = resume_repository.get_resume_by_id(db, resume_id)
    if not resume or resume.user_id != user.id:
        raise ValueError("Resume not found")
    return resume


def match_existing_jobs(
    db: Session,
    resume_id: UUID,
    user: User,
) -> dict:
    _get_owned_resume(db, resume_id, user)
    jobs = job_repository.get_jobs(db)
    if not jobs:
        raise LookupError("No existing jobs are available")

    qualified_jobs = []
    for job in jobs:
        match = calculate_match(db, resume_id, job.id)
        if match.match_score > MATCH_SCORE_THRESHOLD:
            qualified_jobs.append(
                {
                    "job_id": job.id,
                    "job_title": job.title,
                    "company": job.company,
                    "match_score": match.match_score,
                    "matched_skills": match.matched_skills or [],
                    "missing_skills": match.missing_skills or [],
                    "summary": match.explanation,
                }
            )

    qualified_jobs.sort(key=lambda item: item["match_score"], reverse=True)
    if not qualified_jobs:
        raise LookupError("This resume does not match any existing job above 60%")

    return {
        "resume_id": resume_id,
        "score_threshold": MATCH_SCORE_THRESHOLD,
        "qualified_jobs": qualified_jobs,
    }


def get_ai_career_suggestions(
    db: Session,
    resume_id: UUID,
    user: User,
) -> dict:
    resume = _get_owned_resume(db, resume_id, user)
    skills = [
        skill.skill
        for skill in resume_skill_repository.get_resume_skills(db, resume_id)
        if skill.skill
    ]
    resume_text = (resume.extracted_text or "").strip()[:6000]

    if not skills and not resume_text:
        raise ValueError("Resume has not been processed yet")

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": CAREER_ANALYSIS_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Resume skills: {json.dumps(skills)}\n\n"
                        f"Resume text:\n{resume_text}"
                    ),
                },
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
    except RateLimitError as exc:
        raise LLMRateLimitError(
            "Groq daily token limit reached. Wait and retry, or upgrade Groq tier."
        ) from exc

    analysis = json.loads(response.choices[0].message.content)
    suggestions = analysis.get("career_suggestions")
    if not isinstance(suggestions, list):
        raise ValueError("AI returned an invalid career suggestion response")

    return {
        "resume_id": resume_id,
        "career_suggestions": suggestions,
    }


def chat_with_career_coach(
    db: Session,
    user: User,
    message: str,
    history: list,
    resume_id: UUID | None = None,
) -> str:
    """Give private career advice, optionally grounded in the user's own CV."""
    context = "No CV was selected. Give general career advice."
    if resume_id:
        resume = _get_owned_resume(db, resume_id, user)
        skills = [
            skill.skill
            for skill in resume_skill_repository.get_resume_skills(db, resume_id)
            if skill.skill
        ]
        context = (
            f"Selected CV skills: {json.dumps(skills)}\n\n"
            f"Selected CV text:\n{(resume.extracted_text or '').strip()[:6000]}"
        )

    messages = [{"role": "system", "content": CAREER_CHAT_PROMPT}]
    messages.append({"role": "system", "content": f"Career context:\n{context}"})
    messages.extend({"role": item.role, "content": item.content} for item in history)
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.35,
        )
    except RateLimitError as exc:
        raise LLMRateLimitError(
            "Groq daily token limit reached. Wait and retry, or upgrade Groq tier."
        ) from exc

    return (response.choices[0].message.content or "").strip()
