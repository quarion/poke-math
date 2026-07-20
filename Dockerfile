# Use the same Python and uv installation in test and production targets.
FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Create app directory
WORKDIR /app

# Install the pinned uv binary once for every target derived from this base.
COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /usr/local/bin/uv

# Dependency metadata changes less often than source files, preserving Docker's
# cache for both test and production dependency installation.
COPY pyproject.toml uv.lock ./

FROM base AS production-dependencies
RUN uv sync --locked --no-dev

# The test target extends the exact production dependency environment, then adds
# only the locked development dependencies required to run the unit suite.
FROM production-dependencies AS test
RUN uv sync --locked --group dev
COPY pytest.ini ./
COPY src ./src
COPY tests ./tests
RUN uv run --locked --no-sync pytest tests/unit -q

FROM production-dependencies AS runtime

# Add build argument for commit SHA after dependency installation so it does not
# invalidate dependency layers.
ARG COMMIT_SHA
ENV COMMIT_SHA=${COMMIT_SHA}

# Copy only runtime application files. Build configuration, tests, docs, and
# local caches never belong in the deployed container.
COPY src ./src

ENV PATH="/app/.venv/bin:$PATH"

# Runtime command (adjust for your WSGI server)
CMD exec gunicorn --bind :${PORT:-8080} --workers 1 --threads 8 --timeout 60 src.app.app:app
