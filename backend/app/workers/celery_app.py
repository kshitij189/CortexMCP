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

# Upstash's free tier allows only 10,000 Redis commands per day. Kombu's default
# brpop_timeout of 1 second makes an idle worker issue ~86,400 BRPOP calls a day,
# which burns through the whole quota within minutes and then makes every
# enqueue fail with "max daily request limit exceeded". Lengthening the poll and
# switching off the chatty extras (remote control pidbox, event stream, result
# writes) keeps a permanently-running worker inside the free allowance, at the
# cost of up to CELERY_BROKER_POLLING_INTERVAL seconds of task pickup latency.
polling_interval = float(os.getenv("CELERY_BROKER_POLLING_INTERVAL", "15"))

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
