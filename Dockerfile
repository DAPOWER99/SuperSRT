# ============================================
# SuperSRT Dockerfile
# ============================================

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    libmagic1 \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/data /app/cache /app/output /app/logs /app/backups

# Set volume mounts
VOLUME ["/app/data", "/app/cache", "/app/output", "/app/logs", "/app/backups"]

# Create non-root user
RUN useradd -m -u 1000 supersrt && \
    chown -R supersrt:supersrt /app
USER supersrt

# Expose ports
EXPOSE 8000 5000

# Entry point
ENTRYPOINT ["python", "supersrt.py"]

# Default command
CMD ["--help"]
