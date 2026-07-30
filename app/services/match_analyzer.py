import json

from groq import RateLimitError

from app.core.exceptions import LLMRateLimitError
from app.prompts.match_prompt import MATCH_ANALYSIS_PROMPT
from app.services.llm import client


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
    except RateLimitError as e:
        raise LLMRateLimitError(
            "Groq daily token limit reached. Wait and retry, or upgrade Groq tier."
        ) from e

    return json.loads(
        response.choices[0].message.content
    )
