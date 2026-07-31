import re

from app.core.exceptions import LLMRateLimitError
from app.schemas.resume_analysis import ResumeAnalysis
from app.services.llm import analyze_resume


SKILL_LIST = [
    "Python",
    "JavaScript",
    "TypeScript",
    "FastAPI",
    "Django",
    "React",
    "Node.js",
    "PostgreSQL",
    "MongoDB",
    "Docker",
    "AWS",
    "LangChain",
    "Groq",
    "LLMs",
    "RAG",
    "FAISS",
    "Prompt Engineering",
    "Machine Learning",
    "Deep Learning",
    "PyTorch",
    "TensorFlow",
    "NLP",
    "Computer Vision",
    "OpenCV",
    "MediaPipe",
    "SQLAlchemy",
    "Redis",
    "Git",
    "REST APIs",
    "WebSockets",
    "JWT",
]


def _keyword_skills(extracted_text: str) -> list[str]:
    text = extracted_text.lower()
    return [skill for skill in SKILL_LIST if skill.lower() in text]


_NAME_BLOCKLIST = {
    "windows",
    "centos",
    "linux",
    "ubuntu",
    "macos",
    "android",
    "ios",
    "skills",
    "education",
    "experience",
    "projects",
    "summary",
    "objective",
    "profile",
    "contact",
    "technical",
    "technologies",
    "languages",
    "certifications",
    *{s.lower() for s in SKILL_LIST},
}


def _guess_candidate_name(extracted_text: str) -> str | None:
    for line in (extracted_text or "").splitlines():
        name = line.strip().strip("|•·-–—")
        if not name or len(name) > 60:
            continue
        lower = name.lower()
        if "@" in name or "http" in lower or "www." in lower:
            continue
        if any(ch.isdigit() for ch in name):
            continue
        if "," in name and all(
            part.strip().lower() in _NAME_BLOCKLIST
            for part in name.split(",")
            if part.strip()
        ):
            continue
        words = [w for w in re.split(r"\s+", name) if w]
        if not (2 <= len(words) <= 5):
            continue
        if any(w.lower().strip(",.") in _NAME_BLOCKLIST for w in words):
            continue
        if not all(w[:1].isalpha() for w in words):
            continue
        return name
    return None


def analyze_resume_text(
    extracted_text: str,
) -> ResumeAnalysis:
    try:
        result = analyze_resume(extracted_text)
        analysis = ResumeAnalysis.model_validate(result)
    except LLMRateLimitError:
        # Keep upload pipeline alive when Groq quota is exhausted.
        analysis = ResumeAnalysis(
            candidate_name=_guess_candidate_name(extracted_text) or "",
            email="",
            phone="",
            title="",
            skills=_keyword_skills(extracted_text),
            education=[],
            projects=[],
            experience=[],
        )

    if not analysis.skills:
        analysis.skills = _keyword_skills(extracted_text)

    guessed = _guess_candidate_name(extracted_text) or ""
    current = (analysis.candidate_name or "").strip()
    if not current:
        analysis.candidate_name = guessed
    elif current.lower() in _NAME_BLOCKLIST or (
        "," in current
        and all(
            p.strip().lower() in _NAME_BLOCKLIST
            for p in current.split(",")
            if p.strip()
        )
    ):
        analysis.candidate_name = guessed or current

    return analysis
