#!/bin/bash

# Apply database migrations
echo "Executing database migrations..."
alembic upgrade head

# Start the Celery Worker in the background
echo "Starting Celery worker in background..."
# Run in solo pool mode with concurrency limited to 1 to fit within Render's 512MB RAM free tier
celery -A app.workers.celery_app worker --loglevel=info --concurrency=1 -P solo &

# Start the FastAPI Uvicorn API server in the foreground
echo "Starting FastAPI gateway on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
