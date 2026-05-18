"""Workflow log model — tracks processing stages and events for live display."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class WorkflowLog(Base):
    __tablename__ = "workflow_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("research_jobs.id"), nullable=False, index=True)
    stage = Column(String(50), nullable=False)
    level = Column(String(10), nullable=False, default="INFO")  # INFO | WARN | ERROR
    message = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    research_job = relationship("ResearchJob", back_populates="workflow_logs")
