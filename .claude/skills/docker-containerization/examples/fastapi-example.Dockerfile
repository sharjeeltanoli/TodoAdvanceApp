# =============================================================================
# Example: FastAPI Production Dockerfile (with uv)
# =============================================================================
# Assumes:
#   - Python 3.13
#   - uv for dependency management
#   - ASGI app at app.main:app
#   - Port 8000
#   - PostgreSQL (asyncpg) as database
# =============================================================================

# Stage 1: Build
FROM python:3.13-slim AS builder

WORKDIR /app

# System build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install dependencies (cached if lockfile unchanged)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source and install project
COPY . .
RUN uv sync --frozen --no-dev

# Stage 2: Runner
FROM python:3.13-slim AS runner

WORKDIR /app

# Runtime system dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 wget && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup --create-home appuser

# Copy built application
COPY --from=builder --chown=appuser:appgroup /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
