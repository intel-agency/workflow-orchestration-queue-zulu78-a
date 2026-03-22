# OS-APOW Application Dockerfile
# Multi-stage build for production-ready Python application

# Build stage
FROM python:3.12-slim AS builder

# Install uv - Rust-based Python package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system --no-cache -e .

# Production stage
FROM python:3.12-slim AS production

# Create non-root user for security
RUN groupadd --gid 1000 osapow && \
    useradd --uid 1000 --gid osapow --shell /bin/bash --create-home osapow

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=osapow:osapow src/ ./src/
COPY --chown=osapow:osapow pyproject.toml ./

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

# Switch to non-root user
USER osapow

# Expose webhook port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

# Default command runs the notifier
CMD ["python", "-m", "os_apow.main"]
