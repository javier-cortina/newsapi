# Multi-stage Dockerfile for Dagster Pipeline
# Stage 1: Build stage with all dependencies
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Stage 2: Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ src/
COPY pyproject.toml ./

# Install the package in editable mode
RUN pip install --no-cache-dir -e .

# Create directory for DuckDB (if used)
RUN mkdir -p /app/data

# Create non-root user for security
RUN useradd -m -u 1000 dagster && \
    chown -R dagster:dagster /app

USER dagster

# Expose Dagster webserver port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:3000/server_info || exit 1

# Default command (can be overridden in docker-compose or ECS)
CMD ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000", "-m", "newsapi_dentsu.definitions"]
