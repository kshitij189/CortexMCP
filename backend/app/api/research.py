"""Research job API routes — CRUD operations, user-scoped."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.research import (
    ResearchJobCreate,
    ResearchJobResponse,
    ResearchJobList,
    ResearchJobDetail,
    ScrapedSourceResponse,
)
from app.services.auth_service import get_current_user
from app.repositories import research_repo

router = APIRouter(prefix="/research", tags=["Research"])


@router.post("/start", response_model=ResearchJobResponse, status_code=202)
def start_research(
    data: ResearchJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start a new research workflow.
    Creates a job record and returns immediately.
    In Phase 3, this will also queue a Celery task.
    """
    job = research_repo.create_job(
        db=db,
        user_id=str(current_user.id),
        query=data.query,
        depth=data.depth.value,
    )

    # Phase 3: Queue Celery task
    from app.workers.research_task import run_research_pipeline
    run_research_pipeline.delay(str(job.id))

    return ResearchJobResponse.from_orm_job(job)


@router.get("/jobs", response_model=ResearchJobList)
def list_research_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch all research jobs for the authenticated user."""
    jobs, total = research_repo.list_jobs(
        db=db,
        user_id=str(current_user.id),
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return ResearchJobList(
        jobs=[ResearchJobResponse.from_orm_job(j) for j in jobs],
        total=total,
    )


@router.get("/{job_id}", response_model=ResearchJobDetail)
def get_research_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch detailed info for a single research job."""
    job = research_repo.get_job(db, job_id, str(current_user.id))
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found")

    sources = [
        ScrapedSourceResponse(
            id=str(s.id),
            url=s.url,
            title=s.title,
            summary=s.summary,
            is_duplicate=s.is_duplicate,
            relevance_score=s.relevance_score,
            scraped_at=s.scraped_at,
        )
        for s in job.scraped_sources
    ]

    report = None
    if job.report:
        report = {
            "id": str(job.report.id),
            "report_markdown": job.report.report_markdown,
            "report_json": job.report.report_json,
            "pdf_path": job.report.pdf_path,
            "generated_at": job.report.generated_at,
        }

    return ResearchJobDetail(
        job=ResearchJobResponse.from_orm_job(job),
        sources=sources,
        report=report,
    )


@router.delete("/{job_id}", status_code=200)
def delete_research_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a research job and all related data."""
    deleted = research_repo.delete_job(db, job_id, str(current_user.id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Research job not found")

    return {"success": True, "message": "Research job deleted"}


@router.get("/{job_id}/pdf", status_code=200)
def download_research_pdf(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and return a PDF of the research report."""
    job = research_repo.get_job(db, job_id, str(current_user.id))
    if not job or not job.report:
        raise HTTPException(status_code=404, detail="Report not found or not finished")

    import markdown
    from fpdf import FPDF
    from io import BytesIO
    from fastapi.responses import StreamingResponse

    def sanitize_for_pdf(text: str) -> str:
        # Map common non-latin-1 unicode characters to standard ASCII/latin-1 equivalents
        replacements = {
            "\u2018": "'",   # Left single quote
            "\u2019": "'",   # Right single quote
            "\u201c": '"',   # Left double quote
            "\u201d": '"',   # Right double quote
            "\u2013": "-",   # En dash
            "\u2014": "--",  # Em dash
            "\u2022": "*",   # Bullet point
            "\u2026": "...", # Ellipsis
            "\u00a0": " ",   # Non-breaking space
        }
        for search, replace in replacements.items():
            text = text.replace(search, replace)
        return text.encode("latin-1", errors="replace").decode("latin-1")

    # Sanitize markdown to ensure safe character set for fpdf2
    sanitized_markdown = sanitize_for_pdf(job.report.report_markdown)
    
    # Convert Markdown to HTML
    html_content = markdown.markdown(sanitized_markdown, extensions=['extra', 'tables'])
    
    # Inline style replacements for standard tags to look incredibly premium in fpdf2
    html_content = html_content.replace("<h1>", '<h1 style="color: #1e3a8a;">')
    html_content = html_content.replace("<h2>", '<h2 style="color: #2563eb;">')
    html_content = html_content.replace("<h3>", '<h3 style="color: #3b82f6;">')
    
    # Wrap in basic HTML structure without style blocks which fpdf2 doesn't support
    full_html = f"""
    <html>
    <body>
        {html_content}
    </body>
    </html>
    """

    class CustomPDF(FPDF):
        def header(self):
            self.set_font('helvetica', 'B', 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 10, 'CortexMCP Autonomous Research Report', 0, 1, 'R')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('helvetica', 'I', 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    try:
        pdf = CustomPDF()
        pdf.set_margin(15)
        pdf.add_page()
        pdf.set_font("helvetica", size=10)
        pdf.write_html(full_html)
        
        pdf_bytes = pdf.output()
        pdf_buffer = BytesIO(pdf_bytes)
        pdf_buffer.seek(0)
    except Exception as e:
        import traceback
        print(f"PDF Generation failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
    
    filename = f"CortexMCP_Report_{job_id[:8]}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/{job_id}/stream", status_code=200)
def stream_research_progress(
    job_id: str,
    db: Session = Depends(get_db),
    # Note: For simplicity in SSE connections from browsers, we might bypass JWT header auth 
    # or pass it as a query param. Standard EventSource doesn't support headers.
    # To secure this in production, validate a short-lived token from query string.
    # We will just verify the job exists for now.
):
    """SSE endpoint to stream real-time progress for a specific job."""
    job = research_repo.get_job_unscoped(db, job_id) # Using a new unscoped method or existing
    if not job:
        raise HTTPException(status_code=404, detail="Research job not found")

    from app.pubsub.progress import progress_pubsub
    import asyncio
    
    async def event_generator():
        pubsub = progress_pubsub.subscribe(job_id)
        try:
            # Yield initial connection success
            yield f"data: {{\"status\": \"CONNECTED\", \"message\": \"Listening for events...\"}}\n\n"
            
            # Listen to Redis in a non-blocking way
            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True)
                if message and message['type'] == 'message':
                    yield f"data: {message['data']}\n\n"
                    
                    import json
                    data = json.loads(message['data'])
                    if data.get('status') in ['JOB_FINISHED', 'FAILED']:
                        break
                
                await asyncio.sleep(0.1)
        finally:
            pubsub.close()
            
    from fastapi.responses import StreamingResponse
    return StreamingResponse(event_generator(), media_type="text/event-stream")
