#!/usr/bin/env bash
# =============================================================================
# OpenLI DMM - Service Health Verification
# =============================================================================
# Checks all services are running and healthy.
# Usage: bash scripts/healthcheck.sh
# =============================================================================

set -euo pipefail

BACKEND_PORT="${DMM_BACKEND_PORT:-9134}"
FRONTEND_PORT="${DMM_FRONTEND_PORT:-9133}"
HTTP_PORT="${DMM_HTTP_PORT:-9135}"

echo "============================================"
echo "  OpenLI DMM - Health Check"
echo "============================================"
echo ""

PASS=0
FAIL=0

check_service() {
    local name="$1"
    local url="$2"
    printf "  %-25s" "$name:"
    if response=$(curl -sf -o /dev/null -w "%{http_code}" "$url" 2>/dev/null); then
        if [ "$response" = "200" ]; then
            echo "PASS (HTTP $response)"
            ((PASS++))
        else
            echo "WARN (HTTP $response)"
            ((FAIL++))
        fi
    else
        echo "FAIL (unreachable)"
        ((FAIL++))
    fi
}

# Core services
check_service "Backend /health"        "http://localhost:$BACKEND_PORT/health"
check_service "Frontend /"             "http://localhost:$FRONTEND_PORT/"
check_service "Nginx /nginx-health"    "http://localhost:$HTTP_PORT/nginx-health"

echo ""

# API endpoints
check_service "API /api/connectors/types" "http://localhost:$BACKEND_PORT/api/connectors/types"
check_service "API /api/schema/source"    "http://localhost:$BACKEND_PORT/api/schema/source"
check_service "API /api/schema/target"    "http://localhost:$BACKEND_PORT/api/schema/target"
check_service "API /api/gates/profiles"   "http://localhost:$BACKEND_PORT/api/gates/profiles"

echo ""

# Docker container status
echo "  Container Status:"
docker compose ps --format "    {{.Name}}: {{.Status}}" 2>/dev/null || echo "    (docker compose not available)"

echo ""
echo "============================================"
echo "  Results: $PASS passed, $FAIL failed"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
