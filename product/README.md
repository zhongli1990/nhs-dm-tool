# Data Migration Product Control Plane

## Product vision

Enterprise NHS migration control plane for PAS/EPR transitions:
- one governed lifecycle across design, execution, quality, and release
- synchronized CLI + API + UI operations
- safety-first quality visibility and traceable approvals
- scalable interaction patterns for high-volume migration artifacts
- multi-tenant SaaS foundation (`organization -> workspace -> project`)

## Components

1. `backend/`
- FastAPI control-plane API over migration artifacts
- connector plugin framework (CSV active, ODBC/JDBC experimental)
  - PostgreSQL emulator (target) active
  - Cache/IRIS emulator (source) active
  - JSON dummy connector active

2. `frontend/`
- Next.js UI with dynamic rendering of schema/mapping/run artifacts
- login/register/admin UX for OpenLI DMM SaaS foundation

## Run backend

```powershell
cd c:\Zhong\Windsurf\data_migration\product\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 9134
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
- `/login` login
- `/register` registration request (admin approval workflow)
- `/onboarding` enterprise SaaS onboarding workflow (org/workspace/project setup)
- `/settings` application/runtime preferences and connectivity checks
- `/schemas` dynamic source/target explorer with table filter and field drill-down
- `/erd` visual ERD and inferred relationship explorer:
  - searchable table filter
  - force-layout density controls
  - relationship list IDs and cardinality display
- `/mappings` mapping contract explorer (summary + filtered field rows):
  - paged contract rows (default 200/page)
  - paged edit/approve workbench (default 200/page)
  - bulk edit and bulk status transitions
- `/lifecycle` step-by-step lifecycle orchestration (run each stage or all stages with run controls)
- `/runs` execution console with profile controls, gate checks and reject review tabs
- `/quality` data quality command centre:
  - Dashboard
  - KPI Widgets (sparkline, this-week value, threshold bar)
  - Issue Explorer
- `/connectors` connector strategy and dynamic connector config/test/preview console
- `/users` mission-critical user roles and lifecycle task ownership
- `/admin` organization/workspace/project and registration approval console

## Default seed users (development bootstrap)

1. `superadmin` / `Admin@123`
2. `qvh_admin` / `Admin@123`

The seed tenant context is initialized on first backend start:
1. Organization: `QVH`
2. Workspace: `PAS EPR`
3. Project: `PAS18.4 Migration`

## API coverage

See:
- `..\analysis\api_surface_spec.md`

Highlights:
- schema APIs for dynamic table/column rendering
- mapping APIs with filtering
- auth APIs (`/api/auth/login`, `/api/auth/register`, `/api/auth/me`, `/api/auth/switch-context`)
- tenancy APIs (`/api/orgs`, `/api/orgs/{org_id}/workspaces`, `/api/workspaces/{workspace_id}/projects`)
- lifecycle step APIs (`/api/lifecycle/steps`, `/api/lifecycle/steps/{step_id}/execute`)
- lifecycle rerun/snapshot APIs (`/api/lifecycle/execute-from/{step_id}`, `/api/lifecycle/snapshots`, `/api/lifecycle/snapshots/{snapshot_id}/restore`)
- run APIs (latest/history/execute)
- quality/reject APIs:
  - `/api/quality/trends`
  - `/api/quality/trends/seed`
  - `/api/quality/kpis`
  - `/api/quality/kpi-widgets`
- gate profile APIs
- connector exploration APIs

## One-command lifecycle run

```powershell
cd c:\Zhong\Windsurf\data_migration
python .\pipeline\run_product_lifecycle.py --rows 20 --seed 42 --min-patients 20 --release-profile pre_production
```

## Connector placeholders

ODBC/JDBC connectors are implemented as experimental connectors.
They support metadata introspection and row sampling where drivers are available.
Production hardening still required:
- secure credential integration
- read-only query policy
- timeout/query governance
- audit and telemetry

## Current maturity snapshot (v0.2.0)

Implemented:
- SaaS phase-1 foundation:
  - login/register/approval flow
  - tenant hierarchy (`organization -> workspace -> project`)
  - RBAC baseline (super admin, org admin, org roles)
- top-bar UX uplift:
  - compact `Context` popover (org/workspace/project selector)
  - cleaner app shell with less title bar congestion
- new operational pages:
  - onboarding (`/onboarding`)
  - settings (`/settings`)
- mapping workbench approvals and bulk operations
- ERD relationship graph with inferred cardinality
- quality command centre with KPI widgets and trend controls
- lifecycle rerun-from-step and snapshot restore
- enterprise pagination and UI rendering hardening

Pending for production-grade cutover:
- fine-grained RBAC policy matrix by role and function
- federated auth (OIDC/SAML, NHS enterprise identity)
- secrets vault and secure connector credentials
- async job orchestration and audit event stream
- tenant-level billing/licensing and policy packs

## Best-practice runtime approach

1. Keep backend dependencies isolated in `backend/.venv`.
2. Use pinned Python and Node versions in CI.
3. Run backend and frontend as separate services with health checks.
4. Treat `pre_production` gate as engineering readiness, `cutover_ready` as governance readiness.

