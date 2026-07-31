import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.resume import Resume
    from app.models.job import Job
    from app.models.user import User


class MatchResult(Base):
    __tablename__ = "match_results"
    __table_args__ = (
        UniqueConstraint(
            "resume_id",
            "job_id",
            name="uq_match_results_resume_job",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
    )

    checked_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    match_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    matched_skills: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    missing_skills: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    checked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=datetime.utcnow,
    )

    resume: Mapped["Resume"] = relationship()

    job: Mapped["Job"] = relationship()

    checked_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[checked_by_id],
    )

    explanation = Column(
        Text,
        nullable=True,
    )

    recommendations = Column(
        JSON,
        nullable=True,
    )