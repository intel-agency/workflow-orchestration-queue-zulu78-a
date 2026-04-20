# OS-APOW Application Dockerfile
# Multi-stage build for the headless agentic orchestration platform

# ---- Build stage ----
FROM python:3.12-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency manifests first for cache efficiency
COPY pyproject.toml .python-version ./
COPY src/ src/

# Install dependencies (no project itself, just deps)
RUN uv sync --no-dev --no-install-project

# ---- Runtime stage ----
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY src/ src/
COPY pyproject.toml ./

# Use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Default: run the notifier service
# Override with: docker run ... python -m src.orchestrator_sentinel
CMD ["python", "-m", "uvicorn", "src.notifier_service:app", "--host", "0.0.0.0", "--port", "8000"]
