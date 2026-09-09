#!/bin/bash

EMBEDDED_REDIS_URL="redis://127.0.0.1:6379/0"

# ─── Embedded Redis ───
# The API and the Celery worker share one container on Render's free tier, so the
# broker can live here too instead of depending on an external managed instance.
# Persistence is off: every durable thing (job status, sources, reports) lives in
# Postgres, and Redis only holds the in-flight task queue and progress pub/sub.
echo "Starting embedded Redis on 127.0.0.1:6379..."
redis-server \
  --bind 127.0.0.1 \
  --port 6379 \
  --save '' \
  --appendonly no \
  --maxmemory 64mb \
  --maxmemory-policy allkeys-lru \
  --loglevel warning &

# Wait for it to accept connections before anything tries to enqueue.
for _ in $(seq 1 30); do
  if redis-cli -h 127.0.0.1 -p 6379 ping > /dev/null 2>&1; then
    echo "Embedded Redis is ready."
    break
  fi
  sleep 1
done

# ─── Broker selection ───
# If REDIS_URL points at an external instance, keep using it — but only when it
# actually answers. A managed free-tier instance that has been deleted resolves to
# nothing, and without this check every research request fails with an opaque 500.
if [ -n "$REDIS_URL" ] && [ "$REDIS_URL" != "$EMBEDDED_REDIS_URL" ]; then
  if python -c "
import sys, redis
url = '$REDIS_URL'
kwargs = {'ssl_cert_reqs': 'required'} if url.startswith('rediss://') else {}
try:
    redis.Redis.from_url(url, socket_connect_timeout=5, socket_timeout=5, **kwargs).ping()
except Exception as e:
    print(f'  external Redis unreachable: {type(e).__name__}: {e}', file=sys.stderr)
    sys.exit(1)
"; then
    echo "Using external Redis from REDIS_URL."
  else
    echo "Falling back to the embedded Redis instance."
    export REDIS_URL="$EMBEDDED_REDIS_URL"
  fi
else
  export REDIS_URL="$EMBEDDED_REDIS_URL"
  echo "Using embedded Redis."
fi

# Apply database migrations
echo "Executing database migrations..."
alembic upgrade head

# Start the Celery Worker in the background
echo "Starting Celery worker in background..."
# Run in solo pool mode with concurrency limited to 1 to fit within Render's 512MB RAM free tier.
# gossip/mingle/heartbeat each poll Redis on their own schedule and are only useful in a
# multi-worker cluster; this deployment runs exactly one worker.
celery -A app.workers.celery_app worker --loglevel=info --concurrency=1 -P solo \
  --without-gossip --without-mingle --without-heartbeat &

# Start the FastAPI Uvicorn API server in the foreground
echo "Starting FastAPI gateway on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
