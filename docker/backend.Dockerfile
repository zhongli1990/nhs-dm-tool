FROM python:3.11-slim AS backend

LABEL maintainer="OpenLI DMM <support@openli.local>"
LABEL description="OpenLI DMM Backend - FastAPI migration control plane"

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r dmm && useradd -r -g dmm -d /app -s /sbin/nologin dmm

WORKDIR /app

COPY services/backend/requirements.txt /app/services/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/services/backend/requirements.txt

COPY services/backend/ /app/services/backend/
COPY pipeline/ /app/pipeline/
COPY schemas/ /app/schemas/
COPY mock_data/ /app/mock_data/
COPY reports/ /app/reports/
COPY docs/specs/ /app/requirement_spec/

RUN mkdir -p /app/services/backend/data \
    && mkdir -p /app/analysis \
    && mkdir -p /app/reports/snapshots \
    && chown -R dmm:dmm /app

ENV DM_DATA_ROOT=/app
ENV DM_ENV=production
ENV DM_LOG_LEVEL=INFO
ENV DM_ALLOW_ORIGINS=*
ENV DM_API_HOST=0.0.0.0
ENV DM_API_PORT=9134
ENV DMM_TOKEN_SECRET=change_me_in_production
ENV DMM_TOKEN_TTL_SECONDS=43200

EXPOSE 9134

USER dmm

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9134/health || exit 1

CMD ["python", "-m", "uvicorn", "services.backend.app.main:app", \
     "--host", "0.0.0.0", "--port", "9134", "--workers", "2"]
