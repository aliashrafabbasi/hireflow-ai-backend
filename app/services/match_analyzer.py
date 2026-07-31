import json
import re

from groq import RateLimitError

from app.prompts.match_prompt import MATCH_ANALYSIS_PROMPT
from app.services.llm import client


def _norm(skill: str) -> str:
    return re.sub(r"\s+", " ", (skill or "").strip().lower())


def skill_overlap_match(
    resume_skills: list[str],
    job_skills: list[str],
    *,
    job_title: str | None = None,
) -> dict:
    """Deterministic fallback when Groq is rate-limited."""
    resume_norms = [_norm(s) for s in resume_skills if _norm(s)]
    matched: list[str] = []
    missing: list[str] = []

    for job_skill in job_skills:
        jn = _norm(job_skill)
        if not jn:
            continue
        hit = False
        for rn in resume_norms:
            if rn == jn or rn in jn or jn in rn:
                hit = True
                break
        if hit:
            matched.append(job_skill)
        else:
            missing.append(job_skill)

    score = (
        round((len(matched) / len(job_skills)) * 100, 2) if job_skills else 0.0
    )
    title = f" for {job_title}" if job_title else ""
    return {
        "match_score": score,
        "matched_skills": matched,
        "missing_skills": missing,
        "explanation": (
            f"Skill-overlap score{title} "
            f"({len(matched)}/{len(job_skills)} required skills). "
            "LLM was rate-limited, so heuristic scoring was used."
        ),
        "recommendations": [
            {
                "skill": s,
                "resource": "Highlight this skill on the resume or gain related experience.",
            }
            for s in missing[:5]
        ],
        "scoring_mode": "skill_overlap_fallback",
    }


def analyze_match(
    resume_skills: list[str],
    job_skills: list[str],
    job_title: str | None = None,
    job_company: str | None = None,
    job_description: str | None = None,
) -> dict:
    context_parts = []
    if job_title:
        context_parts.append(f"Job title: {job_title}")
    if job_company:
        context_parts.append(f"Company: {job_company}")
    if job_description:
        desc = job_description.strip()
        if len(desc) > 1200:
            desc = desc[:1200] + "..."
        context_parts.append(f"Job description:\n{desc}")

    context_block = "\n".join(context_parts)
    if context_block:
        context_block += "\n\n"

    user_content = (
        f"{context_block}"
        f"Resume skills:\n{json.dumps(resume_skills)}\n\n"
        f"Job required skills:\n{json.dumps(job_skills)}\n\n"
        "Evaluate fit carefully using the job title/description domain."
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": MATCH_ANALYSIS_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            temperature=0,
            response_format={
                "type": "json_object",
            },
        )
    except RateLimitError:
        return skill_overlap_match(
            resume_skills,
            job_skills,
            job_title=job_title,
        )

    return json.loads(
        response.choices[0].message.content
    )
