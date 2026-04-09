# --- Backend Dockerfile ---
# Target: Python 3.12 on Debian slim (works on both x86 and ARM)
# Used by: backend, hermes-worker, hermes-scheduler services

FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed by asyncpg and psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory and non-root user
RUN mkdir -p /app/uploads/pdfs && \
    adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default command — overridden in docker-compose for celery services
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
