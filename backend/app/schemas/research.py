"""Pydantic schemas for research job endpoints."""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ResearchDepth(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    DEEP = "deep"


class JobStatus(str, Enum):
    JOB_CREATED = "JOB_CREATED"
    SEARCH_STARTED = "SEARCH_STARTED"
    SEARCH_COMPLETED = "SEARCH_COMPLETED"
    SCRAPING_STARTED = "SCRAPING_STARTED"
    SCRAPING_COMPLETED = "SCRAPING_COMPLETED"
    SUMMARIZATION_STARTED = "SUMMARIZATION_STARTED"
    SUMMARIZATION_COMPLETED = "SUMMARIZATION_COMPLETED"
    DEDUPLICATION_STARTED = "DEDUPLICATION_STARTED"
    DEDUPLICATION_COMPLETED = "DEDUPLICATION_COMPLETED"
    REPORT_GENERATION_STARTED = "REPORT_GENERATION_STARTED"
    REPORT_GENERATION_COMPLETED = "REPORT_GENERATION_COMPLETED"
    JOB_FINISHED = "JOB_FINISHED"
    JOB_FAILED = "JOB_FAILED"


class ResearchJobCreate(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    depth: ResearchDepth = ResearchDepth.STANDARD


class ResearchJobResponse(BaseModel):
    id: str
    query: str
    depth: str
    status: str
    progress: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_job(cls, job):
        return cls(
            id=str(job.id),
            query=job.query,
            depth=job.depth,
            status=job.status,
            progress=job.progress,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
        )


class ResearchJobList(BaseModel):
    jobs: List[ResearchJobResponse]
    total: int


class ScrapedSourceResponse(BaseModel):
    id: str
    url: str
    title: Optional[str] = None
    summary: Optional[str] = None
    is_duplicate: bool = False
    relevance_score: Optional[float] = None
    scraped_at: datetime

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    id: str
    report_markdown: Optional[str] = None
    report_json: Optional[dict] = None
    pdf_path: Optional[str] = None
    generated_at: datetime

    model_config = {"from_attributes": True}


class ResearchJobDetail(BaseModel):
    job: ResearchJobResponse
    sources: List[ScrapedSourceResponse] = []
    report: Optional[ReportResponse] = None


class ProgressEvent(BaseModel):
    job_id: str
    stage: str
    progress: int
    message: str
    timestamp: datetime
