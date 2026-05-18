import os
from celery import Celery
from app.config import settings

# Initialize Celery using Redis as both broker and result backend
celery_app = Celery(
    "cortexmcp",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.research_task"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
