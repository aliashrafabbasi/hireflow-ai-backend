from app.schemas.resume_analysis import ResumeAnalysis
from app.services.llm import analyze_resume


def analyze_resume_text(
    extracted_text: str,
) -> ResumeAnalysis:
    result = analyze_resume(extracted_text)

    return ResumeAnalysis.model_validate(result)