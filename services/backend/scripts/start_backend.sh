#!/usr/bin/env sh
set -eu

DM_AUTH_BACKEND="${DM_AUTH_BACKEND:-postgres}"
DM_STATE_BACKEND="${DM_STATE_BACKEND:-postgres}"
DM_RUN_MIGRATIONS="${DM_RUN_MIGRATIONS:-true}"

should_migrate="false"
if [ "$DM_RUN_MIGRATIONS" = "true" ] || [ "$DM_RUN_MIGRATIONS" = "1" ]; then
  if [ "$DM_AUTH_BACKEND" = "postgres" ] || [ "$DM_STATE_BACKEND" = "postgres" ]; then
    should_migrate="true"
  fi
fi

if [ "$should_migrate" = "true" ]; then
  echo "[DMM] Running Alembic migrations..."
  cd /app/services/backend
  alembic -c alembic.ini upgrade head
  cd /app
fi

exec python -m uvicorn services.backend.app.main:app --host 0.0.0.0 --port 9134 --workers 2
