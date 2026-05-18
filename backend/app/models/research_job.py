"""Research job model — the central entity of the research pipeline."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    parent_job_id = Column(UUID(as_uuid=True), ForeignKey("research_jobs.id"), nullable=True, index=True)
    query = Column(Text, nullable=False)
    depth = Column(String(20), nullable=False, default="standard")  # basic | standard | deep
    status = Column(String(50), nullable=False, default="JOB_CREATED", index=True)
    progress = Column(Integer, nullable=False, default=0)
    settings = Column(JSONB, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="research_jobs")
    parent_job = relationship("ResearchJob", remote_side=[id], backref="child_jobs")
    scraped_sources = relationship("ScrapedSource", back_populates="research_job", cascade="all, delete-orphan")
    report = relationship("GeneratedReport", back_populates="research_job", uselist=False, cascade="all, delete-orphan")
    workflow_logs = relationship("WorkflowLog", back_populates="research_job", cascade="all, delete-orphan")
