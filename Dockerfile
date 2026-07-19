# Use official Python runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Create app directory
WORKDIR /app

# Install Python dependencies first
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Add build argument for commit SHA - moved down since it changes frequently
ARG COMMIT_SHA
ENV COMMIT_SHA=${COMMIT_SHA}

# Copy application code last since it changes most frequently
COPY . .

# Runtime command (adjust for your WSGI server)
CMD exec gunicorn --bind :${PORT:-8080} --workers 1 --threads 8 --timeout 300 src.app.app:app
