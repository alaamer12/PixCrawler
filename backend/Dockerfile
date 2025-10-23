# Multi-stage Docker build for PixCrawler Backend
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN pip install uv

# Development stage
FROM base as development

WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install dependencies
RUN uv sync --dev

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Run development server
CMD ["uv", "run", "pixcrawler-api"]

# Production stage
FROM base as production

WORKDIR /app

# Create non-root user
RUN groupadd -r pixcrawler && useradd -r -g pixcrawler pixcrawler

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install production dependencies only
RUN uv sync --no-dev

# Copy source code
COPY . .

# Change ownership to non-root user
RUN chown -R pixcrawler:pixcrawler /app
USER pixcrawler

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# Run production server
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
