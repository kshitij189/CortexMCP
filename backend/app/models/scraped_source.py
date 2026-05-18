"""Scraped source model — stores raw and processed content from each URL."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ScrapedSource(Base):
    __tablename__ = "scraped_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("research_jobs.id"), nullable=False, index=True)
    url = Column(Text, nullable=False)
    title = Column(String(500), nullable=True)
    raw_content = Column(Text, nullable=True)
    cleaned_content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False)
    relevance_score = Column(Float, nullable=True)
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    research_job = relationship("ResearchJob", back_populates="scraped_sources")
