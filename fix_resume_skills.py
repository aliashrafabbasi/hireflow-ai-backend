from app.dependencies.database import SessionLocal
from app.models.resume import Resume
from app.services.resume_analyzer import analyze_resume_text
from app.services.resume_skill import save_resume_skills


db = SessionLocal()


resumes = db.query(Resume).filter(
    Resume.extracted_text.isnot(None)
).all()


for resume in resumes:

    analysis = analyze_resume_text(
        resume.extracted_text
    )

    print(
        "Resume:",
        resume.id
    )

    print(
        "Skills:",
        analysis.skills
    )

    save_resume_skills(
        db=db,
        resume_id=resume.id,
        skills=analysis.skills
    )


db.close()