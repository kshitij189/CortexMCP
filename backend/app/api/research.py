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
        settings={"persona": data.persona},
        parent_job_id=data.parent_job_id,
    )

    # Phase 3: Queue Celery task
    from app.workers.research_task import run_research_pipeline

    try:
        run_research_pipeline.delay(str(job.id))
    except Exception as e:
        # The job row already exists, so leaving it in JOB_CREATED would strand it
        # as a permanently pending item in the dashboard. Mark it failed and tell
        # the caller why instead of surfacing a bare 500.
        research_repo.update_job_status(
            db,
            str(job.id),
            status="FAILED",
            progress=0,
            error_message=f"Could not queue research task: {type(e).__name__}: {e}",
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "Research queue is unavailable, so the job could not be started. "
                f"Broker error: {type(e).__name__}: {e}"
            ),
        )

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


@router.get("/{job_id}/docx", status_code=200)
def download_research_docx(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate and return a Microsoft Word DOCX version of the research report."""
    job = research_repo.get_job(db, job_id, str(current_user.id))
    if not job or not job.report:
        raise HTTPException(status_code=404, detail="Report not found or not finished")

    from io import BytesIO
    import re
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls
    from fastapi.responses import StreamingResponse

    def parse_styled_text(paragraph, text: str):
        # Splitting by markdown bold (**) and italic (*) syntax
        parts = re.split(r'(\*\*.*?\*\*|\*.*?\*)', text)
        for part in parts:
            if part.startswith('**') and part.endswith('**'):
                run = paragraph.add_run(part[2:-2])
                run.bold = True
            elif part.startswith('*') and part.endswith('*'):
                run = paragraph.add_run(part[1:-1])
                run.italic = True
            else:
                paragraph.add_run(part)

    def render_docx_table(doc, rows: list[str]):
        parsed_rows = []
        for r in rows:
            cells = [c.strip() for c in r.split('|')[1:-1]]
            if not cells:
                continue
            # Skip separator lines
            if all(all(char == '-' for char in cell) or not cell for cell in cells):
                continue
            parsed_rows.append(cells)
            
        if not parsed_rows:
            return
            
        cols_count = len(parsed_rows[0])
        table = doc.add_table(rows=len(parsed_rows), cols=cols_count)
        table.style = 'Light Shading Accent 1'
        
        for r_idx, cells in enumerate(parsed_rows):
            row = table.rows[r_idx]
            for c_idx, val in enumerate(cells):
                if c_idx < len(row.cells):
                    cell = row.cells[c_idx]
                    cell.text = val
                    
                    # Style headers
                    if r_idx == 0:
                        for paragraph in cell.paragraphs:
                            for run in paragraph.runs:
                                run.bold = True
                                run.font.color.rgb = RGBColor(255, 255, 255)
                        # Dark blue background shading for headers
                        shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="1E3A8A"/>')
                        cell._tc.get_or_add_tcPr().append(shading_elm)

    try:
        doc = Document()
        
        # Format margins (1 inch)
        for section in doc.sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)

        # Base normal paragraph styling (Calibri 11pt, charcoal text)
        style_normal = doc.styles['Normal']
        font = style_normal.font
        font.name = 'Calibri'
        font.size = Pt(11)
        font.color.rgb = RGBColor(0x33, 0x33, 0x33)

        # Right-aligned header
        header = doc.sections[0].header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("CortexMCP Autonomous Research Report")
        hrun.font.name = 'Calibri'
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(120, 120, 120)

        lines = job.report.report_markdown.split('\n')
        in_table = False
        table_rows = []

        for line in lines:
            stripped = line.strip()

            if in_table and not stripped.startswith('|'):
                render_docx_table(doc, table_rows)
                in_table = False
                table_rows = []

            if not stripped:
                continue

            # Title styles (H1, H2, H3)
            if stripped.startswith('# '):
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(18)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.keep_with_next = True
                run = p.add_run(stripped[2:])
                run.bold = True
                run.font.size = Pt(20)
                run.font.color.rgb = RGBColor(0x1e, 0x3a, 0x8a)
            elif stripped.startswith('## '):
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(14)
                p.paragraph_format.space_after = Pt(4)
                p.paragraph_format.keep_with_next = True
                run = p.add_run(stripped[3:])
                run.bold = True
                run.font.size = Pt(16)
                run.font.color.rgb = RGBColor(0x25, 0x63, 0xeb)
            elif stripped.startswith('### '):
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(10)
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.keep_with_next = True
                run = p.add_run(stripped[4:])
                run.bold = True
                run.font.size = Pt(12)
                run.font.color.rgb = RGBColor(0x3b, 0x82, 0xf6)
            elif stripped.startswith('- ') or stripped.startswith('* ') or stripped.startswith('• '):
                p = doc.add_paragraph(style='List Bullet')
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.15
                parse_styled_text(p, stripped[2:])
            elif stripped.startswith('|'):
                in_table = True
                table_rows.append(stripped)
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.line_spacing = 1.15
                parse_styled_text(p, stripped)

        if in_table and table_rows:
            render_docx_table(doc, table_rows)

        docx_buffer = BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)
    except Exception as e:
        import traceback
        print(f"DOCX Generation failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"DOCX generation failed: {str(e)}")

    filename = f"CortexMCP_Report_{job_id[:8]}.docx"

    return StreamingResponse(
        docx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
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


@router.get("/{job_id}/compare", status_code=200)
def compare_research_jobs(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate an AI-powered comparison report (Delta report) between a child job and its parent job.
    """
    child_job = research_repo.get_job(db, job_id, str(current_user.id))
    if not child_job:
        raise HTTPException(status_code=404, detail="Research job not found")
        
    if not child_job.parent_job_id:
        raise HTTPException(status_code=400, detail="This research job does not have a previous version to compare against")
        
    parent_job = research_repo.get_job(db, str(child_job.parent_job_id), str(current_user.id))
    if not parent_job:
        raise HTTPException(status_code=404, detail="Previous version of research job not found")
        
    if child_job.status != "JOB_FINISHED" or not child_job.report:
        raise HTTPException(status_code=400, detail="The latest research job report has not finished generating yet")
        
    if parent_job.status != "JOB_FINISHED" or not parent_job.report:
        raise HTTPException(status_code=400, detail="The previous research job report has no finished content to compare")
        
    # Generate the comparison report using LLM Service
    from app.services.llm_service import llm_service
    
    system_prompt = (
        "You are an expert technical intelligence analyst. Your task is to perform a detailed "
        "comparative temporal analysis between two versions of a research report on the same topic.\n\n"
        "Analyze what has changed from the Previous Report to the Current Report. Focus on:\n"
        "1. NEW FINDINGS & ADDITIONS: Brand new information, events, statistics, or capabilities discovered.\n"
        "2. UPDATED/CHANGED INFORMATION: Corrections, updates on statuses, changes in metrics, or shifts in timeline/sentiment.\n"
        "3. DEPRECATED OR REPLACED DETAILS: Information that has become obsolete, corrected, or superseded in the new version.\n"
        "4. STABLE INSIGHTS: High-confidence key findings that remain unchanged and validated across both reports.\n\n"
        "Format the output strictly as a highly structured, professional, and visually stunning Markdown report. "
        "Use distinct indicators/emojis such as '[+]' for additions, '[Δ]' for updates, '[-]' for deprecations, "
        "and '[✓]' for verified stable insights. Make the analysis actionable, crisp, and analytical."
    )
    
    context = (
        f"RESEARCH TOPIC/QUERY: {child_job.query}\n\n"
        f"--- PREVIOUS REPORT ---\n{parent_job.report.report_markdown}\n\n"
        f"--- CURRENT REPORT ---\n{child_job.report.report_markdown}\n"
    )
    
    try:
        delta_markdown = llm_service.generate_summary(system_prompt, context)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate comparison: {str(e)}")
        
    return {
        "child_job_id": str(child_job.id),
        "parent_job_id": str(parent_job.id),
        "query": child_job.query,
        "parent_report": parent_job.report.report_markdown,
        "child_report": child_job.report.report_markdown,
        "delta_report": delta_markdown
    }
