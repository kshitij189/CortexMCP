import json
import ssl
import redis
from app.config import settings

class ProgressPubSub:
    def __init__(self):
        # We use a synchronous Redis client to stay compatible with Celery and FastAPI sync routes.
        # Enforce SSL validation checks for secure cloud connections (e.g. Upstash) to satisfy protocol handshake.
        ssl_cert_reqs = ssl.CERT_REQUIRED if settings.REDIS_URL.startswith("rediss://") else None
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            ssl_cert_reqs=ssl_cert_reqs
        )

    def publish_progress(self, job_id: str, status: str, progress: int, message: str = ""):
        """Publishes a progress update to a specific job channel."""
        channel = f"job_{job_id}"
        payload = {
            "status": status,
            "progress": progress,
            "message": message
        }
        try:
            self.redis_client.publish(channel, json.dumps(payload))
        except Exception as e:
            print(f"Failed to publish progress to {channel}: {e}")

    def subscribe(self, job_id: str):
        """Returns a pubsub object subscribed to the job channel."""
        pubsub = self.redis_client.pubsub()
        channel = f"job_{job_id}"
        pubsub.subscribe(channel)
        return pubsub

progress_pubsub = ProgressPubSub()
