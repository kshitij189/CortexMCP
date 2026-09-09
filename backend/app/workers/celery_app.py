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

# Kombu polls the broker with BRPOP once per interval, so an idle worker issues
# ~86,400 commands a day at the default of 1 second. That is free against the
# in-container Redis this deploys with, but it would exhaust a metered hosted
# broker's allowance on its own — Upstash's free tier, for instance, caps at
# 10,000 commands per day. Raise this to 15 or more when pointing REDIS_URL at
# such a service, trading task pickup latency for command budget.
polling_interval = float(os.getenv("CELERY_BROKER_POLLING_INTERVAL", "1"))

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    broker_use_ssl=ssl_config,
    redis_backend_use_ssl=ssl_config,

    # ─── Free-tier Redis command budget ───
    broker_transport_options={
        "polling_interval": polling_interval,
        "socket_timeout": 10,
        "socket_connect_timeout": 10,
        "visibility_timeout": 3600,
    },
    worker_enable_remote_control=False,
    worker_send_task_events=False,
    task_ignore_result=True,

    # ─── Fail fast when the broker is unreachable ───
    # Progress is tracked in Postgres and pushed over Redis pub/sub, so nothing
    # reads task results; a request that cannot enqueue should surface that in
    # seconds rather than blocking the API worker for half a minute.
    broker_connection_timeout=5,
    broker_connection_retry_on_startup=True,
    task_publish_retry=True,
    task_publish_retry_policy={
        "max_retries": 2,
        "interval_start": 0,
        "interval_step": 0.5,
        "interval_max": 1.0,
    },
)
