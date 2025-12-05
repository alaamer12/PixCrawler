# PixCrawler Development Container
FROM python:3.11-slim 
    
# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive
 
# Set working directory 
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build essentials
    build-essential \
    gcc \
    g++ \
    make \
    # Development tools
    git \
    curl \
    wget \
    vim \
    nano \
    # PostgreSQL client
    postgresql-client \
    libpq-dev \
    # Image processing libraries (for PIL/Pillow)
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    # SSL/TLS
    ca-certificates \
    openssl \
    # Other utilities
    jq \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20.x
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install UV (Python package manager)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Install Bun
RUN curl -fsSL https://bun.sh/install | bash
ENV BUN_INSTALL="/root/.bun"
ENV PATH="$BUN_INSTALL/bin:$PATH"

# Install global Python tools
RUN pip install --no-cache-dir \
    black \
    ruff \
    mypy \
    pytest \
    ipython

# Set Python environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/workspace

# Create non-root user (optional, currently using root)
# RUN useradd -m -s /bin/bash devuser && \
#     chown -R devuser:devuser /workspace
# USER devuser

# Default command
CMD ["/bin/bash"]
