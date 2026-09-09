#!/bin/bash

# Apply database migrations
echo "Executing database migrations..."
alembic upgrade head

# Start the Celery Worker in the background
echo "Starting Celery worker in background..."
# Run in solo pool mode with concurrency limited to 1 to fit within Render's 512MB RAM free tier.
# gossip/mingle/heartbeat each poll Redis on their own schedule, which does not fit
# inside Upstash's 10k commands/day free quota — they are only useful in a multi-worker
# cluster, and this deployment runs exactly one worker.
celery -A app.workers.celery_app worker --loglevel=info --concurrency=1 -P solo \
  --without-gossip --without-mingle --without-heartbeat &

# Start the FastAPI Uvicorn API server in the foreground
echo "Starting FastAPI gateway on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
