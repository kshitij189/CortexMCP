import os
import ssl
from celery import Celery
from app.config import settings

# Initialize Celery using Redis as both broker and result backend
celery_app = Celery(
    "cortexmcp",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.research_task"]
)

# Configure SSL parameters for secure Redis connections (rediss://)
ssl_config = None
if settings.REDIS_URL.startswith("rediss://"):
    ssl_config = {
        "ssl_cert_reqs": ssl.CERT_REQUIRED
    }

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_use_ssl=ssl_config,
    redis_backend_use_ssl=ssl_config,
)
