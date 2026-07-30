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


def analyze_resume_text(
    extracted_text: str,
) -> ResumeAnalysis:

    # First try LLM
    result = analyze_resume(extracted_text)

    analysis = ResumeAnalysis.model_validate(result)

    # Fallback if LLM gives empty skills
    if not analysis.skills:

        text = extracted_text.lower()

        skills = []

        for skill in SKILL_LIST:
            if skill.lower() in text:
                skills.append(skill)

        analysis.skills = skills

    return analysis