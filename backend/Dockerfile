FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Pre-install CPU version of PyTorch to save massive download time and image size
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install python dependencies (NO extra-index-url here to prevent querying PyTorch for non-pytorch packages)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy application code
COPY . .

# Create the chroma data directory
RUN mkdir -p chroma_data

# The command will be overridden in docker-compose.yml 
# for either the API server or the Celery worker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
