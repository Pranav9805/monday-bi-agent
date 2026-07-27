# Production-ready, optimized Dockerfile for Monday.com AI BI Agent
FROM python:3.12-slim

# Prevent Python from writing .pyc files to disk and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies and curl for container health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies without caching wheel files
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose ports for FastAPI (8000) and Streamlit UI (8501)
EXPOSE 8000
EXPOSE 8501

# Health check for the service container
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command launches FastAPI backend REST server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
