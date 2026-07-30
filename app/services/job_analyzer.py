from app.schemas.job_analysis import JobAnalysis
from app.services.llm import analyze_job_description


def analyze_job_text(
    job_description: str,
) -> JobAnalysis:
    result = analyze_job_description(job_description)

    return JobAnalysis.model_validate(result)
