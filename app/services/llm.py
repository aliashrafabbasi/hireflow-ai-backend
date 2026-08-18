import json

from groq import Groq, RateLimitError

from app.core.config import settings
from app.core.exceptions import LLMRateLimitError
from app.prompts.job_prompt import JOB_ANALYSIS_PROMPT
from app.prompts.resume_prompt import RESUME_ANALYSIS_PROMPT

client = Groq(
    api_key=settings.GROQ_API_KEY,
)


def analyze_resume(
    resume_text: str,
) -> dict:
    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": RESUME_ANALYSIS_PROMPT,
                },
                {
                    "role": "user",
                    "content": resume_text,
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

    content = response.choices[0].message.content
    return json.loads(content)


def analyze_job_description(
    job_description: str,
) -> dict:
    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": JOB_ANALYSIS_PROMPT,
                },
                {
                    "role": "user",
                    "content": job_description,
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

    content = response.choices[0].message.content
    return json.loads(content)
