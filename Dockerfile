# =============================================================================
# Money Flow Backend - Multi-stage Docker Build
# =============================================================================
# Optimized for smaller production images with security best practices
#
# Build stages:
#   1. builder - Install dependencies and build wheels
#   2. production - Minimal runtime image
#
# Usage:
#   docker build -t money-flow-backend .
#   docker run -p 8000:8000 money-flow-backend
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and create wheels
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first (better layer caching)
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip wheel && \
    pip install --no-cache-dir .

# -----------------------------------------------------------------------------
# Stage 2: Production - Minimal runtime image
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

# Security: Don't run as root
ARG APP_USER=appuser
ARG APP_GROUP=appgroup

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd --system ${APP_GROUP} && \
    useradd --system --gid ${APP_GROUP} --create-home ${APP_USER}

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=${APP_USER}:${APP_GROUP} src/ ./src/

# Copy data files (bank profiles, etc.)
COPY --chown=${APP_USER}:${APP_GROUP} data/ ./data/

# Security: Set proper permissions
RUN chmod -R 550 /app/src && chmod -R 550 /app/data

# Switch to non-root user
USER ${APP_USER}

# Environment variables for Python optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
