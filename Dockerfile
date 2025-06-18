# AI Coder Assistant - Dockerfile
# This project is licensed under the GNU General Public License v3.0
# See LICENSE file for details
#
# Multi-stage build for optimized binaries
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UPX for binary compression
RUN wget https://github.com/upx/upx/releases/download/v4.0.2/upx-4.0.2-amd64_linux.tar.xz \
    && tar -xf upx-4.0.2-amd64_linux.tar.xz \
    && mv upx-4.0.2-amd64_linux/upx /usr/local/bin/ \
    && rm -rf upx-4.0.2-amd64_linux*

# Set up Python environment
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pyinstaller nuitka cx_freeze

# Copy source code
COPY . .

# Build stage
FROM base as builder

# Create build environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install build dependencies
RUN pip install pyinstaller upx

# Build all components
RUN python build_all.py

# Final stage - minimal runtime
FROM alpine:latest as final

# Install runtime dependencies
RUN apk add --no-cache \
    libstdc++ \
    libgcc \
    && rm -rf /var/cache/apk/*

# Copy binaries
COPY --from=builder /app/dist /app

# Set permissions
RUN chmod +x /app/*

# Set working directory
WORKDIR /app

# Default command
CMD ["./ai-coder-launcher", "core"] 