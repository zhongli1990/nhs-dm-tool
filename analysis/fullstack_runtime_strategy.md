# Full-Stack Runtime Strategy (FastAPI + Next.js)

Date: 2026-02-26

## Direct answer

Yes, use a dedicated Python virtual environment for FastAPI.
This remains the correct baseline for reliability and reproducibility.

## Runtime strategy for enterprise-quality lifecycle operations

1. Backend isolation
- create `product/backend/.venv`
- install pinned dependencies from `requirements.txt`
- run `uvicorn app.main:app --host 127.0.0.1 --port 8099`

2. Frontend isolation
- keep `product/frontend/node_modules` local
- run Next.js on `3133`
- set `NEXT_PUBLIC_DM_API_BASE=http://localhost:8099`

3. Controlled startup model
- backend and frontend as separate managed processes
- clean-stop existing listeners before restart
- verify health endpoints before user access

4. Lifecycle governance sequence
- execute extract -> mock/profile -> semantic map -> mapping contract -> contract ETL -> enterprise checks -> release gates
- enforce profile-based release policy:
  - `development`
  - `pre_production`
  - `cutover_ready`

5. Operational UX expectations
- mappings workflows use pagination and bulk actions for scale
- ERD supports filtered relationship visualization
- lifecycle UI supports step execution, rerun-from-step, and snapshot restore

6. Security posture for production scale-up
- introduce API auth and RBAC
- move connector credentials to secret vault
- enforce read-only DB users for source connectivity
- maintain immutable run/audit logs
- add async execution queue for long-running operations

## Local run commands (Windows)

```powershell
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\setup_backend.ps1
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\setup_frontend.ps1
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\run_fullstack.ps1 -BackendPort 8099 -FrontendPort 3133
```
