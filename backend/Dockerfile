FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Pre-install CPU version of PyTorch to save massive download time and image size
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Copy application code
COPY . .

# Create the chroma data directory
RUN mkdir -p chroma_data

# The command will be overridden in docker-compose.yml 
# for either the API server or the Celery worker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
