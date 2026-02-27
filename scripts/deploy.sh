#!/usr/bin/env bash
# =============================================================================
# OpenLI DMM - Docker Compose Deployment
# =============================================================================
# Builds and starts all services with health verification.
# Usage: bash scripts/deploy.sh [--prod]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_DIR"

PROD_FLAG=""
COMPOSE_FILES="-f docker-compose.yml"

if [[ "${1:-}" == "--prod" ]]; then
    PROD_FLAG="production"
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
    echo "============================================"
    echo "  OpenLI DMM - PRODUCTION Deployment"
    echo "============================================"
else
    echo "============================================"
    echo "  OpenLI DMM - Development Deployment"
    echo "============================================"
fi

# --- Check prerequisites ---
echo "[1/5] Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Run: sudo bash scripts/setup-ubuntu.sh"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "ERROR: Docker Compose plugin is not installed."
    exit 1
fi

# --- Check .env ---
if [ ! -f .env ]; then
    echo "WARNING: .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "  Please review and update .env before production use."
fi

# --- Stop existing services ---
echo "[2/5] Stopping existing services..."
docker compose $COMPOSE_FILES down --remove-orphans 2>/dev/null || true

# --- Build images ---
echo "[3/5] Building Docker images..."
docker compose $COMPOSE_FILES build --no-cache

# --- Start services ---
echo "[4/5] Starting services..."
docker compose $COMPOSE_FILES up -d

# --- Health verification ---
echo "[5/5] Verifying service health..."
echo ""

MAX_RETRIES=30
RETRY_INTERVAL=2

# Wait for backend health
echo -n "  Backend health: "
for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf http://localhost:${DMM_BACKEND_PORT:-9134}/health > /dev/null 2>&1; then
        echo "OK"
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "FAIL (timeout after $((MAX_RETRIES * RETRY_INTERVAL))s)"
        echo "  Check logs: docker compose logs backend"
        exit 1
    fi
    sleep $RETRY_INTERVAL
done

# Wait for frontend health
echo -n "  Frontend health: "
for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf http://localhost:${DMM_FRONTEND_PORT:-9133}/ > /dev/null 2>&1; then
        echo "OK"
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "FAIL (timeout after $((MAX_RETRIES * RETRY_INTERVAL))s)"
        echo "  Check logs: docker compose logs frontend"
        exit 1
    fi
    sleep $RETRY_INTERVAL
done

# Wait for nginx health
echo -n "  Nginx health:    "
for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf http://localhost:${DMM_HTTP_PORT:-9135}/nginx-health > /dev/null 2>&1; then
        echo "OK"
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "FAIL (timeout after $((MAX_RETRIES * RETRY_INTERVAL))s)"
        echo "  Check logs: docker compose logs nginx"
        exit 1
    fi
    sleep $RETRY_INTERVAL
done

echo ""
echo "============================================"
echo "  Deployment successful!"
echo "============================================"
echo ""
echo "  Application:  http://localhost:${DMM_HTTP_PORT:-9135}"
echo "  Backend API:  http://localhost:${DMM_BACKEND_PORT:-9134}/health"
echo "  Frontend:     http://localhost:${DMM_FRONTEND_PORT:-9133}"
echo ""
echo "  Default login: superadmin / Admin@123"
echo ""
echo "  Logs:     docker compose logs -f"
echo "  Stop:     docker compose down"
echo "  Restart:  docker compose restart"
echo ""
