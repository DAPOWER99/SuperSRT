# ============================================
# SuperSRT Dockerfile - Optimized Free Models
# Version: 2.0.0
# ============================================

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=UTC

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    ffmpeg \
    libmagic1 \
    libssl-dev \
    curl \
    wget \
    git \
    build-essential \
    libsndfile1 \
    libasound2-dev \
    portaudio19-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data \
    /app/cache \
    /app/output \
    /app/logs \
    /app/backups \
    /app/models \
    /app/config

# Set volume mounts
VOLUME ["/app/data", "/app/cache", "/app/output", "/app/logs", "/app/backups", "/app/config"]

# Create non-root user
RUN useradd -m -u 1000 supersrt && \
    chown -R supersrt:supersrt /app && \
    chmod -R 755 /app

USER supersrt

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose ports (API, Web UI)
EXPOSE 8000 5000 8080

# Set default environment variables
ENV OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-} \
    CACHE_LOCATION=/app/cache \
    SUPERSRT_OUTPUT_DIR=/app/output \
    SUPERSRT_LOG_LEVEL=INFO \
    SUPERSRT_DEFAULT_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free \
    SUPERSRT_CACHE_ENABLED=true \
    SUPERSRT_CACHE_TTL=86400 \
    SUPERSRT_PARALLEL_WORKERS=4 \
    SUPERSRT_VERBOSE=false \
    SUPERSRT_BACKUP_ENABLED=true

# Entry point with argument handling
ENTRYPOINT ["python", "supersrt.py"]

# Default command (show help)
CMD ["--help"]

# Alternative entry points for different use cases
# CMD ["translate", "--help"]  # Uncomment for translation help
# CMD ["wav", "--help"]        # Uncomment for WAV processing help
# CMD ["interactive", "-i", "/app/data/subtitle.srt"]  # Uncomment for interactive mode

# Build-time metadata
LABEL maintainer="DAPOWER99" \
      version="2.0.0" \
      description="SuperSRT - Advanced AI-Powered Subtitle Processing Suite (Free Models)" \
      license="MIT" \
      org.opencontainers.image.source="https://github.com/DAPOWER99/SuperSRT" \
      org.opencontainers.image.documentation="https://github.com/DAPOWER99/SuperSRT#readme"
