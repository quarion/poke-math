# Use official Python runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add build argument for commit SHA - moved down since it changes frequently
ARG COMMIT_SHA
ENV COMMIT_SHA=${COMMIT_SHA}

# Copy application code last since it changes most frequently
COPY . .

# Runtime command (adjust for your WSGI server)
CMD exec gunicorn --bind :${PORT:-5002} --workers 1 --threads 8 --timeout 0 src.app.app:app 