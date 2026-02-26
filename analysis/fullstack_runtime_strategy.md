# Full-Stack Runtime Strategy (FastAPI + Next.js)

Date: 2026-02-25

## Direct answer

Yes, use a dedicated Python virtual environment for FastAPI.
This is the correct baseline for reliability and reproducibility.

## Recommended approach for enterprise quality

1. Backend environment isolation
- create `product/backend/.venv`
- install pinned dependencies from `requirements.txt`
- run `uvicorn app.main:app`

2. Frontend dependency isolation
- keep `product/frontend/node_modules` local to the app
- use `npm.cmd` on Windows when PowerShell script policy blocks `npm`

3. Controlled startup model
- backend and frontend as separate processes/services
- health checks:
  - backend: `/health`
  - frontend: HTTP availability on configured port

4. Release governance
- run full lifecycle pipeline before UI operations:
  - extract -> generate -> mapping -> contract ETL -> quality -> gates
- enforce profile-based release gates:
  - `development`
  - `pre_production`
  - `cutover_ready`

5. Security posture for scale-up
- introduce API auth and RBAC
- move connector credentials to secret vault
- enforce read-only DB users for connector integrations
- maintain immutable run/audit logs

## Local run commands (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\setup_backend.ps1
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\setup_frontend.ps1
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\run_fullstack.ps1
```
