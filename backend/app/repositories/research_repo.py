"""Data access layer for research job operations."""

import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.research_job import ResearchJob
from app.models.scraped_source import ScrapedSource
from app.models.generated_report import GeneratedReport
from app.models.workflow_log import WorkflowLog


def create_job(
    db: Session,
    user_id: str,
    query: str,
    depth: str,
    settings: Optional[dict] = None,
    parent_job_id: Optional[str] = None,
) -> ResearchJob:
    """Create a new research job."""
    job = ResearchJob(
        user_id=user_id,
        query=query,
        depth=depth,
        status="JOB_CREATED",
        progress=0,
        settings=settings or {},
        parent_job_id=uuid.UUID(parent_job_id) if parent_job_id else None,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: str, user_id: str) -> Optional[ResearchJob]:
    """Fetch a job by ID, scoped to the authenticated user."""
    return (
        db.query(ResearchJob)
        .filter(ResearchJob.id == job_id, ResearchJob.user_id == user_id)
        .first()
    )


def get_job_unscoped(db: Session, job_id: str) -> Optional[ResearchJob]:
    """Fetch a job by ID without user scope (for internal/SSE use)."""
    return db.query(ResearchJob).filter(ResearchJob.id == job_id).first()


def list_jobs(
    db: Session,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[List[ResearchJob], int]:
    """List jobs for a user with optional status filter. Returns (jobs, total_count)."""
    query = db.query(ResearchJob).filter(ResearchJob.user_id == user_id)

    if status:
        if status in ["FAILED", "JOB_FAILED"]:
            query = query.filter(ResearchJob.status.in_(["FAILED", "JOB_FAILED"]))
        else:
            query = query.filter(ResearchJob.status == status)

    total = query.count()
    jobs = query.order_by(desc(ResearchJob.created_at)).offset(offset).limit(limit).all()

    return jobs, total


def update_job_status(
    db: Session,
    job_id: str,
    status: str,
    progress: int,
    error_message: Optional[str] = None,
) -> Optional[ResearchJob]:
    """Update job status and progress. Used by Celery workers."""
    job = db.query(ResearchJob).filter(ResearchJob.id == job_id).first()
    if not job:
        return None

    job.status = status
    job.progress = progress
    job.updated_at = datetime.now(timezone.utc)

    if error_message:
        job.error_message = error_message

    if status == "JOB_FINISHED":
        job.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(job)
    
    # Broadcast to SSE listeners
    from app.pubsub.progress import progress_pubsub
    progress_pubsub.publish_progress(
        job_id=job_id,
        status=status,
        progress=progress,
        message=f"Status changed to {status}"
    )
    
    return job


def delete_job(db: Session, job_id: str, user_id: str) -> bool:
    """Delete a job and all related data (cascade)."""
    job = get_job(db, job_id, user_id)
    if not job:
        return False

    db.delete(job)
    db.commit()
    return True


def add_workflow_log(
    db: Session,
    job_id: str,
    stage: str,
    message: str,
    level: str = "INFO",
    metadata: Optional[dict] = None,
) -> WorkflowLog:
    """Add a workflow log entry for a job."""
    log = WorkflowLog(
        job_id=job_id,
        stage=stage,
        level=level,
        message=message,
        metadata_=metadata or {},
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    # Broadcast detailed log to SSE listeners
    from app.pubsub.progress import progress_pubsub
    progress_pubsub.publish_progress(
        job_id=job_id,
        status="LOG",
        progress=-1, # Indicates this is just a log, don't update progress bar
        message=f"[{stage}] {message}"
    )
    
    return log


def create_scraped_source(
    db: Session, job_id: str, url: str, title: str, snippet: str, content: str = None
) -> ScrapedSource:
    """Create a scraped source record for a research job."""
    source = ScrapedSource(
        job_id=job_id,
        url=url,
        title=title,
        summary=snippet,
        raw_content=content,
        cleaned_content=content
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def get_scraped_sources(db: Session, job_id: str) -> List[ScrapedSource]:
    """Get all scraped sources for a given job."""
    return db.query(ScrapedSource).filter(ScrapedSource.job_id == job_id).all()


def create_generated_report(
    db: Session, job_id: str, report_markdown: str
) -> GeneratedReport:
    """Create a generated report record for a research job."""
    report = GeneratedReport(
        job_id=job_id,
        report_markdown=report_markdown,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
