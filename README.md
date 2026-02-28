# OpenLI DMM - NHS PAS Data Migration Platform

Enterprise-grade data migration platform for NHS PAS/EPR system migrations.

- **Source**: PC60/V83 Legacy PAS (417 tables, 5,387 fields)
- **Target**: PAS 18.4 (38 LOAD tables, 880 fields)
- **Stack**: FastAPI + Next.js + Python ETL Pipeline
- **Deployment**: Docker Compose on AWS Ubuntu 24.04 / Windows Server manual runtime

## Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env - at minimum change DMM_TOKEN_SECRET and DMM_BOOTSTRAP_ADMIN_PASSWORD

# 2. Build and deploy
bash scripts/deploy.sh

# 3. Access
# Application:  http://localhost:9135
# Backend API:  http://localhost:9134/health
# Frontend:     http://localhost:9133
# Login:        superadmin / <DMM_BOOTSTRAP_ADMIN_PASSWORD from .env>
```

## AWS Ubuntu 24.04 Deployment

```bash
# 1. Provision Ubuntu 24.04 EC2 instance (t3.medium or larger)

# 2. Install prerequisites
sudo bash scripts/setup-ubuntu.sh

# 3. Clone project
sudo mkdir -p /opt/dmm && sudo chown $USER:$USER /opt/dmm
git clone <repo-url> /opt/dmm
cd /opt/dmm

# 4. Configure
cp .env.example .env
nano .env   # Set DMM_TOKEN_SECRET, DM_ALLOW_ORIGINS, NEXT_PUBLIC_DM_API_BASE

# 5. Deploy
bash scripts/deploy.sh --prod

# 6. Verify
bash scripts/healthcheck.sh
```

## Project Structure

```
.
├── docker-compose.yml          # Docker Compose services
├── docker-compose.prod.yml     # Production overrides
├── .env.example                # Environment template
│
├── docker/                     # Docker build infrastructure
│   ├── backend.Dockerfile      # Python 3.11 + FastAPI
│   ├── frontend.Dockerfile     # Node 20 + Next.js (multi-stage)
│   └── nginx/
│       └── default.conf        # Reverse proxy configuration
│
├── services/                   # Application services
│   ├── backend/                # FastAPI control-plane API
│   │   ├── app/                # API endpoints, models, connectors, security
│   │   └── requirements.txt
│   └── frontend/               # Next.js control-plane UI
│       ├── app/                # 13+ page routes
│       ├── components/         # Shared UI components
│       └── lib/                # API client and data utilities
│
├── pipeline/                   # Core ETL pipeline
│   ├── enterprise/             # Enterprise ETL modules (checks, crosswalks, transforms)
│   └── *.py                    # Pipeline scripts (extract, map, migrate, gate)
│
├── schemas/                    # Data schemas and crosswalks
│   ├── crosswalks/             # Code translation dictionaries
│   ├── source_schema_catalog.csv
│   └── target_schema_catalog.csv
│
├── mock_data/                  # Test and mock data
│   ├── source/                 # Source system extracts
│   ├── target/                 # Target fixture tables
│   └── target_contract/        # Contract-driven ETL outputs
│
├── reports/                    # Generated pipeline reports
│   └── snapshots/              # Lifecycle snapshots
│
├── docs/                       # Documentation
│   ├── analysis/               # Design, architecture, gap analysis
│   ├── specs/                  # Source/target requirement specs
│   ├── release-notes/          # Version release notes
│   └── guides/                 # Deployment and user guides
│
└── scripts/                    # Deployment and operations
    ├── deploy.sh               # Docker compose deploy with health checks
    ├── setup-ubuntu.sh         # Ubuntu 24.04 prerequisites installer
    └── healthcheck.sh          # Service health verification
```

## Docker Architecture

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| `backend` | python:3.11-slim | 9134 | FastAPI API server |
| `frontend` | node:20-alpine | 3000 (mapped 9133) | Next.js UI server |
| `postgres` | postgres:16-alpine | 5432 (mapped 9136) | App relational database |
| `nginx` | nginx:alpine | 80 (mapped 9135) | Reverse proxy |

### Persistent Volumes

| Volume | Purpose |
|--------|---------|
| `dmm-reports` | Pipeline reports and snapshots (artifacts) |
| `dmm-mock-data` | Source/target mock data |
| `dmm-saas-store` | Optional file-store fallback for auth context data |
| `dmm-schemas` | Schema catalogs and crosswalks |
| `dmm-postgres` | PostgreSQL data files |

Runtime state (`mapping_workbench`, `quality_kpi_config`, `quality_history`) is persisted in PostgreSQL when `DM_STATE_BACKEND=postgres` (default).
Immutable audit events are persisted in PostgreSQL when `DM_AUDIT_BACKEND=postgres` and `DM_AUDIT_ENABLED=true` (default).

### Schema Migration Control

- Alembic migrations are the primary schema management path.
- Backend container startup runs `alembic upgrade head` when:
  - `DM_RUN_MIGRATIONS=true`
  - and either `DM_AUTH_BACKEND=postgres` or `DM_STATE_BACKEND=postgres`
- Legacy auto-create fallback is disabled by default:
  - `DM_SCHEMA_AUTOCREATE=false`
  - set to `true` only for emergency recovery scenarios.

### Port Allocation Policy

All exposed host ports are constrained to `9133-9139`:

- `9133` frontend
- `9134` backend
- `9135` nginx ingress
- `9136` postgres
- `9137-9139` reserved for future services

## Migration Pipeline

```
Extract Specs → Generate Mock Data → Semantic Mapping → Mapping Contract
    → Contract ETL → Enterprise Quality Gate → Release Gates
```

Run the full lifecycle via CLI:
```bash
python pipeline/run_product_lifecycle.py --rows 20 --seed 42 \
    --min-patients 20 --release-profile pre_production
```

Or via the UI: Navigate to `/lifecycle` and execute steps interactively.

## Current Status (v0.2.5)

- Schema extraction: **PASS** (417 source / 38 target tables)
- Contract-driven ETL: **PASS** (38 tables, 0 crosswalk rejects)
- Enterprise quality gate: **PASS** (0 errors, 0 warnings)
- Release gates: **pre_production PASS**
- SaaS foundation: Multi-tenant auth, RBAC, org/workspace/project context (PostgreSQL-backed)
- UI: Dashboard, Schemas, ERD, Mappings, Lifecycle, Runs, Quality, Connectors, Documents, Users & RBAC, Admin
- Enterprise controls: user lifecycle lock/unlock/session reset, role-permission matrix, audit explorer/export
- Versioning: manifest-driven source of truth (`services/version_manifest.json`) used by API and UI surfaces

## Operations

```bash
# View logs
docker compose logs -f
docker compose logs backend

# Restart services
docker compose restart

# Stop all services
docker compose down

# Rebuild after code changes
docker compose build --no-cache && docker compose up -d

# Run DB migrations manually (non-Docker/manual deployment)
cd services/backend
alembic -c alembic.ini upgrade head

# Production deployment with resource limits
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

Audit review API (org admin / super admin):
- `GET /api/audit/events?limit=200`

## Key Documentation

| Document | Location |
|----------|----------|
| Product blueprint | `docs/analysis/productization_blueprint.md` |
| API surface spec | `docs/analysis/api_surface_spec.md` |
| Deployment guide (Ubuntu) | `docs/analysis/deployment_guide_ubuntu.md` |
| Deployment guide (Windows Server, non-Docker) | `docs/guides/deployment_windows_server_manual.md` |
| Runtime data layout decision | `docs/guides/runtime_data_layout.md` |
| Enterprise user guide | `docs/analysis/enterprise_user_guide.md` |
| Gap register | `docs/analysis/gap_register.md` |
| E2E lifecycle | `docs/analysis/qvh_pas_migration_e2e_lifecycle.md` |
| SaaS RBAC design | `docs/analysis/saas_multitenancy_rbac_design.md` |
| Enterprise user/RBAC design (v0.2.5 baseline) | `docs/analysis/enterprise_user_management_rbac_design_v0.2.5.md` |
| Enterprise user/RBAC implementation plan | `docs/analysis/enterprise_user_management_rbac_implementation_plan.md` |
| Enterprise user/RBAC implementation status | `docs/analysis/enterprise_user_management_rbac_implementation_status_v0.2.5.md` |
| Release notes v0.2.5 | `docs/release-notes/v0.2.5.md` |
| Due diligence report | `docs/analysis/due_diligence_fullstack_e2e.md` |

## Licensing and IP

This product is proprietary software and is not open-source.

- Legal owner: Lightweight Integration Limited
- Copyright: Copyright (c) Lightweight Integration Limited. All rights reserved.
- Licensing terms: Enterprise commercial licensing only, under executed agreement.
- Contact: Zhong@li-ai.co.uk

See `LICENSE-ENTERPRISE.md` for enterprise licensing and IP terms.

## Default Credentials

| User | Password | Role |
|------|----------|------|
| `superadmin` | `DMM_BOOTSTRAP_ADMIN_PASSWORD` | Super Admin |
| `qvh_admin` | `DMM_BOOTSTRAP_ADMIN_PASSWORD` | Org Admin (QVH) |

## Connector Types

| Type | Status | Direction |
|------|--------|-----------|
| CSV | Active | Source/Target |
| Cache/IRIS Emulator | Active | Source |
| PostgreSQL Emulator | Active | Target |
| JSON Dummy | Active | Test |
| ODBC | Experimental | Source/Target |
| JDBC | Experimental | Source/Target |
