#!/bin/bash

# Apply database migrations
echo "Executing database migrations..."
alembic upgrade head

# Start the Celery Worker in the background
echo "Starting Celery worker in background..."
celery -A app.workers.celery_app worker --loglevel=info &

# Start the FastAPI Uvicorn API server in the foreground
echo "Starting FastAPI gateway on port $PORT..."
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
