# Admin Frontend Dockerfile
FROM python:3.11-slim

# Prevent Python stdout/stderr buffering (logs appear immediately in Docker)
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run as non-root user for security
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8081

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8081", "--workers", "2", "--timeout", "120", "run:app"]
