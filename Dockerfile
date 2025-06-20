# Multi-stage Docker build for AI Coder Assistant
# Stage 1: Base image with Poetry
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry'

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="${POETRY_HOME}/bin:$PATH"

# Stage 2: Dependencies
FROM base as dependencies

WORKDIR /app

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --only=main --no-root

# Stage 3: Development dependencies
FROM dependencies as dev-dependencies

# Install development dependencies
RUN poetry install --with dev --no-root

# Stage 4: Build stage
FROM dev-dependencies as builder

# Copy source code
COPY . .

# Build the application
RUN poetry build

# Stage 5: Production runtime
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libgconf-2-4 \
    libnss3 \
    libasound2 \
    libatk1.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpulse0 \
    libxss1 \
    libxtst6 \
    libxrandr2 \
    libgconf-2-4 \
    libnss3 \
    libatk1.0-0 \
    libgtk-3-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libgbm1 \
    libasound2 \
    libpulse0 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r aicoder && useradd -r -g aicoder aicoder

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy built application
COPY --from=builder /app/dist /app/dist

# Copy configuration files
COPY --from=builder /app/config /app/config
COPY --from=builder /app/docs /app/docs

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src"

# Change ownership to non-root user
RUN chown -R aicoder:aicoder /app

# Switch to non-root user
USER aicoder

# Expose ports
EXPOSE 8000 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Default command
CMD ["python", "-m", "src.main"]

# Stage 6: Development runtime
FROM dev-dependencies as development

# Install additional development tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy source code
COPY . .

# Set environment variables
ENV PYTHONPATH="/app/src" \
    FLASK_ENV=development \
    FLASK_DEBUG=1

# Expose ports
EXPOSE 8000 8080 5000

# Default command for development
CMD ["poetry", "run", "python", "-m", "src.main"]

# Stage 7: Testing runtime
FROM dev-dependencies as testing

# Copy source code
COPY . .

# Set environment variables
ENV PYTHONPATH="/app/src" \
    PYTEST_ADDOPTS="--cov=src --cov-report=html --cov-report=term-missing"

# Run tests
CMD ["poetry", "run", "pytest"]

# Stage 8: API server
FROM production as api-server

# Set environment variables for API
ENV APP_MODE=api \
    HOST=0.0.0.0 \
    PORT=8000

# Expose API port
EXPOSE 8000

# Run API server
CMD ["poetry", "run", "python", "-m", "src.backend.services.web_server"]

# Stage 9: CLI tool
FROM production as cli

# Set environment variables for CLI
ENV APP_MODE=cli

# Run CLI
CMD ["poetry", "run", "python", "-m", "src.cli.main"]

# Stage 10: Scanner tool
FROM production as scanner

# Set environment variables for scanner
ENV APP_MODE=scanner

# Run scanner
CMD ["poetry", "run", "python", "-m", "src.backend.services.scanner"]

# Stage 11: Trainer tool
FROM production as trainer

# Install additional dependencies for training
RUN apt-get update && apt-get install -y \
    nvidia-cuda-toolkit \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for trainer
ENV APP_MODE=trainer \
    CUDA_VISIBLE_DEVICES=0

# Run trainer
CMD ["poetry", "run", "python", "-m", "src.backend.services.trainer"] 