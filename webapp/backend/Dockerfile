# ══════════════════════════════════════════════════════════════════
# Stage 1: Build & Dependencies
# ══════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install CPU-only PyTorch first to keep image lean (~500MB vs ~4GB CUDA)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install application dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN pip install --no-cache-dir asyncpg structlog alembic

# ══════════════════════════════════════════════════════════════════
# Stage 2: Production Runtime
# ══════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8000

WORKDIR /app

# Install minimal runtime dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create unprivileged user for security
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /app/webapp/backend/tmp/uploads /app/model/checkpoints && \
    chown -R appuser:appuser /app

# Copy model architecture, configuration and checkpoint
COPY --chown=appuser:appuser model/ /app/model/

# Copy backend source code
COPY --chown=appuser:appuser webapp/backend/ /app/webapp/backend/

USER appuser

WORKDIR /app/webapp/backend

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start FastAPI application with Uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
