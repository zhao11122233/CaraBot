# ---- Builder Stage ----
FROM python:3.10-slim-bookworm AS builder

WORKDIR /app

# 配置阿里云国内源，仅用 bookworm 避免回退 deb.debian.org
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb http://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
        gcc g++ make curl \
        && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 替换为阿里源，添加超时参数
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    --default-timeout=100 \
    --retries=5 \
    --timeout=100

# ---- Runtime Stage ----
FROM python:3.10-slim-bookworm

WORKDIR /app

# Create carabot user first (before any chown operations)
RUN groupadd -r carabot && useradd -r -g carabot carabot

# 配置阿里云国内源，仅用 bookworm 避免回退 deb.debian.org
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb http://mirrors.aliyun.com/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 curl \
        && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create data and log directories (as root, later volumes will override)
RUN mkdir -p /app/data/models/bge-m3 /app/data/chroma /app/logs \
    && chown -R carabot:carabot /app

USER carabot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]