from typing import Optional
from sqlalchemy.orm import Session
from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.repositories import research_repo
from app.services.search_service import search_service
from app.services.scraper_service import scraper_service
import traceback

@celery_app.task(bind=True, name="app.workers.research_task.run_research_pipeline")
def run_research_pipeline(self, job_id: str):
    """
    Asynchronous Celery task that coordinates the entire research pipeline:
    1. Search (Tavily/Serper)
    2. Scrape (BeautifulSoup)
    3. Finalize
    """
    db: Session = SessionLocal()
    
    try:
        # Mark as SEARCHING
        job = research_repo.update_job_status(db, job_id, status="SEARCHING", progress=10)
        if not job:
            return f"Job {job_id} not found."
            
        research_repo.add_workflow_log(db, job_id, "SEARCH", f"Starting search for query: {job.query}")
        
        # 1. Execute Search
        search_results = search_service.search(job.query, num_results=5)
        research_repo.add_workflow_log(db, job_id, "SEARCH", f"Discovered {len(search_results)} URLs.")
        
        if not search_results:
            research_repo.update_job_status(db, job_id, status="FAILED", progress=0, error_message="No search results found.")
            return
            
        # 2. Execute Scraping
        job = research_repo.update_job_status(db, job_id, status="SCRAPING", progress=30)
        research_repo.add_workflow_log(db, job_id, "SCRAPE", "Starting content extraction...")
        
        successful_scrapes = 0
        total_urls = len(search_results)
        
        for idx, result in enumerate(search_results):
            url = result["url"]
            title = result["title"]
            snippet = result["snippet"]
            
            research_repo.add_workflow_log(db, job_id, "SCRAPE", f"Scraping {url}...")
            content = scraper_service.scrape_url(url)
            
            if content:
                # Save scraped content
                research_repo.create_scraped_source(db, job_id, url, title, snippet, content)
                successful_scrapes += 1
            
            # Update progress dynamically during scraping (30% to 80%)
            current_progress = 30 + int((idx + 1) / total_urls * 50)
            research_repo.update_job_status(db, job_id, status="SCRAPING", progress=current_progress)

        from app.services.llm_service import llm_service
        from app.prompts.summarize import SUMMARIZE_SYSTEM_PROMPT
        from app.services.dedup_service import dedup_service

        # 3. Execute Summarization with RAG Deduplication
        research_repo.update_job_status(db, job_id, status="SUMMARIZING", progress=80)
        research_repo.add_workflow_log(db, job_id, "SUMMARIZE", "Deduplicating and curating context for LLM synthesis...")
        
        # Retrieve all scraped sources for this job
        sources = research_repo.get_scraped_sources(db, job_id)
        raw_texts = [source.raw_content for source in sources if source.raw_content]
        
        # Deduplicate and extract highly unique chunks
        unique_context = dedup_service.get_unique_context(job_id, raw_texts)
        
        research_repo.add_workflow_log(db, job_id, "SUMMARIZE", f"Context curated. Sending to LLM for report generation...")
        report_markdown = llm_service.generate_summary(SUMMARIZE_SYSTEM_PROMPT, unique_context)
        
        if report_markdown:
            research_repo.create_generated_report(db, job_id, report_markdown)
            research_repo.add_workflow_log(db, job_id, "SUMMARIZE", "Report generated successfully.")
        else:
            research_repo.add_workflow_log(db, job_id, "SUMMARIZE", "Failed to generate report.", level="WARNING")

        research_repo.update_job_status(db, job_id, status="JOB_FINISHED", progress=100)
        research_repo.add_workflow_log(db, job_id, "COMPLETE", "Research pipeline completed successfully.")
        
        return f"Job {job_id} completed successfully."

    except Exception as e:
        error_trace = traceback.format_exc()
        research_repo.update_job_status(db, job_id, status="FAILED", progress=0, error_message=str(e))
        research_repo.add_workflow_log(db, job_id, "ERROR", f"Pipeline crashed: {str(e)}", level="ERROR")
        raise
        
    finally:
        db.close()
