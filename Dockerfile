# Use official Python runtime
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Create app directory
WORKDIR /app

# Install locked production dependencies first. Keep the virtual environment in
# the application directory for a self-contained runtime.
COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev

# Add build argument for commit SHA - moved down since it changes frequently
ARG COMMIT_SHA
ENV COMMIT_SHA=${COMMIT_SHA}

# Copy only runtime application files. Build configuration, tests, docs, and
# local caches never belong in the deployed container.
COPY src ./src

ENV PATH="/app/.venv/bin:$PATH"

# Runtime command (adjust for your WSGI server)
CMD exec gunicorn --bind :${PORT:-8080} --workers 1 --threads 8 --timeout 60 src.app.app:app
