import json

from app.prompts.match_prompt import MATCH_ANALYSIS_PROMPT
from app.services.llm import client


def analyze_match(
    resume_skills: list[str],
    job_skills: list[str],
) -> dict:
    user_content = (
        f"Resume skills:\n{json.dumps(resume_skills)}\n\n"
        f"Job required skills:\n{json.dumps(job_skills)}"
    )

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

    return json.loads(
        response.choices[0].message.content
    )
