from datetime import datetime

import fitz
from sqlalchemy.orm import Session

from app.models.resume import Resume
from app.services.resume_analyzer import analyze_resume_text
from app.services.resume_skill import save_resume_skills


def process_resume(
    db: Session,
    resume: Resume,
):
    try:
        doc = fitz.open(resume.file_path)

        extracted_text = ""

        for page in doc:
            extracted_text += page.get_text()

        doc.close()

        analysis = analyze_resume_text(extracted_text)

        resume.extracted_text = extracted_text
        resume.processing_status = "completed"
        resume.parsed_at = datetime.utcnow()

        save_resume_skills(
            db=db,
            resume_id=resume.id,
            skills=analysis.skills,
        )

        db.commit()
        db.refresh(resume)

        return resume

    except Exception as e:
        resume.processing_status = "failed"

        db.commit()

        raise e