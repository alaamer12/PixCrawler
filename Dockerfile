# =============================================================================
# Stage 1: Base Image
# =============================================================================
FROM python:3.11-slim AS base

# Environment variables 
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \ 
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \  
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Stage 2: Builder - Install Python dependencies
# =============================================================================
FROM base AS builder

# Upgrade pip and install build tools
RUN pip install --upgrade pip wheel setuptools hatchling

# Copy workspace configuration first
COPY pyproject.toml ./

# Copy all workspace packages
COPY utility/ ./utility/
COPY celery_core/ ./celery_core/
COPY validator/ ./validator/
COPY builder/ ./builder/
COPY backend/ ./backend/

# Install workspace packages in dependency order
# This ensures proper installation of interdependent packages
RUN pip install --no-cache-dir -e ./utility && \
    pip install --no-cache-dir -e ./celery_core && \
    pip install --no-cache-dir -e ./validator && \
    pip install --no-cache-dir -e ./builder && \
    pip install --no-cache-dir -e ./backend

# Install flower for monitoring (optional dependency)
RUN pip install --no-cache-dir -e "./celery_core[monitoring]"

# =============================================================================
# Stage 3: Runtime - Final lean image
# =============================================================================
FROM base AS runtime

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app /app

# Create necessary directories
RUN mkdir -p /app/storage /app/logs && \
    chmod 755 /app/storage /app/logs

# Expose ports
EXPOSE 8000 5555

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]