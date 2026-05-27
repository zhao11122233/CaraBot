# ---- Builder Stage ----
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Runtime Stage ----
FROM python:3.10-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r carabot && useradd -r -g carabot carabot

# Install runtime deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create data and log directories
RUN mkdir -p /app/data/models/bge-m3 /app/data/chroma /app/logs \
    && chown -R carabot:carabot /app

USER carabot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
