# Data Migration Product Control Plane

## Components

1. `backend/`
- FastAPI control-plane API over migration artifacts
- connector plugin framework (CSV active, ODBC/JDBC stubs)
  - PostgreSQL emulator (target) active
  - Cache/IRIS emulator (source) active
  - JSON dummy connector active

2. `frontend/`
- Next.js UI with dynamic rendering of schema/mapping/run artifacts

## Run backend

```powershell
cd c:\Zhong\Windsurf\data_migration\product\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8099
```

Windows scripted setup:

```powershell
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\setup_backend.ps1
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\run_backend.ps1
```

## Run frontend

```powershell
cd c:\Zhong\Windsurf\data_migration\product\frontend
npm.cmd install
npm.cmd run dev
```

Windows scripted setup:

```powershell
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\setup_frontend.ps1
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\run_frontend.ps1
```

Run both:

```powershell
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\run_fullstack.ps1
```

## UI pages

- `/` dashboard
- `/schemas` dynamic source/target table and column summaries
- `/mappings` mapping contract inspection
- `/runs` contract run, enterprise quality, release gates, rejects
- `/connectors` connector strategy and coverage
- `/connectors` dynamic connector selection/config + discovery preview via API
- `/users` mission-critical user roles and lifecycle task ownership

## API coverage

See:
- `..\analysis\api_surface_spec.md`

Highlights:
- schema APIs for dynamic table/column rendering
- mapping APIs with filtering
- run APIs (latest/history/execute)
- quality/reject APIs
- gate profile APIs
- connector exploration APIs

## One-command lifecycle run

```powershell
cd c:\Zhong\Windsurf\data_migration
python .\pipeline\run_product_lifecycle.py --rows 20 --seed 42 --min-patients 20 --release-profile pre_production
```

## Connector placeholders

ODBC/JDBC connectors are implemented as structured stubs with full interface contracts.
They are intentionally non-executable in this build and are ready for:
- secure credential integration
- read-only query policy
- metadata introspection
- paged sampling

## Best-practice runtime approach

1. Keep backend dependencies isolated in `backend/.venv`.
2. Use pinned Python and Node versions in CI.
3. Run backend and frontend as separate services with health checks.
4. Treat `pre_production` gate as engineering readiness, `cutover_ready` as governance readiness.
