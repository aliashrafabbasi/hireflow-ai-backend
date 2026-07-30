import json

from groq import Groq

from app.core.config import settings
from app.prompts.resume_prompt import (
    RESUME_ANALYSIS_PROMPT,
)

client = Groq(
    api_key=settings.GROQ_API_KEY,
)


def analyze_resume(
    resume_text: str,
) -> dict:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
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

    content = response.choices[0].message.content

    return json.loads(content)