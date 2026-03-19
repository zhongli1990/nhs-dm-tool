# QVH Data Migration Product Deployment Guide

Date: 2026-02-27  
Scope: `c:\Zhong\Windsurf\data_migration`

## 1. Deployment objective

Deploy and operate the full migration control plane and pipeline stack for mission-critical PAS to EPR migration delivery:
- pipeline batch lifecycle (schema, mapping, ETL, quality, gates)
- FastAPI control-plane backend
- Next.js operational frontend
- connector modes (CSV real, Cache/IRIS emulator, PostgreSQL emulator, ODBC/JDBC experimental)

## 2. Product vision alignment

This deployment supports the current product vision:
1. clinically safe execution with explicit quality/reject evidence
2. governed lifecycle operations with role-aware approvals and run controls
3. vendor-agnostic onboarding patterns across file and DB connectors
4. API and UI parity so operators and engineers run the same lifecycle

## 3. Environment prerequisites

## 3.1 Host baseline

1. Windows host with PowerShell.
2. Python 3.10+ on PATH.
3. Node.js 20+ and npm on PATH.
4. Access to project root: `c:\Zhong\Windsurf\data_migration`.

## 3.2 Required folders

1. `requirement_spec/`
2. `schemas/`
3. `mock_data/source/`
4. `mock_data/target/`
5. `mock_data/target_contract/`
6. `reports/`

## 3.3 Port plan

1. Backend API: `9134`
2. Frontend UI: `9133`

## 4. One-time setup

## 4.1 Backend setup (FastAPI)

```powershell
cd c:\Zhong\Windsurf\data_migration\product\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Or scripted:

```powershell
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\setup_backend.ps1
```

## 4.2 Frontend setup (Next.js)

```powershell
cd c:\Zhong\Windsurf\data_migration\product\frontend
npm.cmd install
```

Or scripted:

```powershell
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\setup_frontend.ps1
```

## 4.3 Environment files

Backend (`product/backend/.env`):

```env
DM_ENV=local
DM_LOG_LEVEL=INFO
DM_ALLOW_ORIGINS=*
DM_API_HOST=127.0.0.1
DM_API_PORT=9134
```

Frontend (`product/frontend/.env.local`):

```env
NEXT_PUBLIC_DM_API_BASE=http://127.0.0.1:9134
```

## 5. Full lifecycle data pipeline deployment

Run from root:

```powershell
cd c:\Zhong\Windsurf\data_migration
python .\pipeline\run_product_lifecycle.py --rows 20 --seed 42 --min-patients 20 --release-profile pre_production
```

Expected artifacts:

1. `schemas/source_schema_catalog.csv`
2. `schemas/target_schema_catalog.csv`
3. `reports/mapping_contract.csv`
4. `mock_data/target_contract/*.csv` (38 target tables)
5. `reports/contract_migration_report.json`
6. `reports/enterprise_pipeline_report.json`
7. `reports/release_gate_report.json`
8. `reports/product_lifecycle_run.json`

## 6. Full stack deployment

## 6.1 Clean restart

```powershell
$ports=@(9133,9134)
foreach($p in $ports){
  $conns=Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue
  if($conns){
    $ids=$conns | Select-Object -ExpandProperty OwningProcess -Unique
    foreach($id in $ids){ Stop-Process -Id $id -Force }
  }
}
```

## 6.2 Start services

```powershell
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\run_fullstack.ps1 -BackendPort 9134 -FrontendPort 9133
```

## 6.3 Health checks

```powershell
Invoke-WebRequest http://127.0.0.1:9134/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:9133 -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:9134/api/connectors/types -UseBasicParsing
```

Success criteria:

1. Backend health returns `{"status":"ok"}`.
2. Frontend returns HTTP `200`.
3. Connector types API returns `csv`, `cache_iris_emulator`, `postgres_emulator`.

## 6.4 UI control-plane readiness checks

Validate these operational pages after startup:

1. `/` dashboard:
   - live KPIs loaded from backend APIs
2. `/schemas`:
   - source/target tabs, table filters, field drill-down
3. `/erd`:
   - relationship graph loads
   - searchable table filter and density controls
   - relationship list row IDs and cardinality labels
4. `/mappings`:
   - contract rows tab with server-side pagination
   - edit/approve tab with page size and page navigation
   - bulk edit and bulk status actions
5. `/lifecycle`:
   - step execution, run-from-step, snapshots, restore
6. `/runs`:
   - full lifecycle trigger with gate/reject review
7. `/quality`:
   - Dashboard, KPI Widgets, Issue Explorer
   - widget refresh, interval, and weeks controls
8. `/connectors`:
   - dynamic connector type selection and previews
9. `/users`:
   - role model and lifecycle ownership reference
10. `/onboarding`:
   - enterprise tenant/workspace/project onboarding flow
11. `/settings`:
   - runtime defaults and connectivity checks

UI and CLI synchronization rule:

1. UI executions call backend lifecycle APIs.
2. Backend executes the same `pipeline/*.py` commands used by CLI.
3. Both write shared artifacts under `reports/` and `mock_data/target_contract/`.

## 7. Production-like operational controls

## 7.1 Release gate policy

1. `pre_production` profile: engineering readiness gate.
2. `cutover_ready` profile: governance/cutover gate.
3. Block deployment if gate status is `FAIL`.

## 7.2 Minimum runbook controls

1. Immutable run ID via `reports/product_lifecycle_run.json`.
2. Persist all reports and issue CSVs per run.
3. Archive `mapping_contract.csv` and crosswalk versions for traceability.
4. Capture operator and timestamp in release pack.

## 7.3 Data safety controls

1. Read-only connector policy for source systems in execution phase.
2. Reject files enabled for crosswalk failures.
3. No silent coercion for invalid NHS-critical code translations.

## 8. Manual E2E validation protocol

1. Open UI: `http://127.0.0.1:9133`.
2. Validate schema table counts against catalogs.
3. Validate mappings pagination and edit/approve workbench behavior.
4. Trigger run from `/runs` or POST `/api/runs/execute`.
5. Verify status chain:
   - contract migration PASS
   - enterprise quality PASS
   - release gate PASS (selected profile)
6. Verify quality/reject endpoints:
   - `/api/rejects/crosswalk`
   - `/api/quality/issues?kind=enterprise`
   - `/api/quality/issues?kind=contract`

## 9. Troubleshooting

1. Port already in use:
   - stop listeners on `9133` and `9134`, restart.
2. Backend not starting:
   - run `run_backend.ps1` and inspect traceback.
3. Frontend cannot call backend:
   - verify `NEXT_PUBLIC_DM_API_BASE=http://127.0.0.1:9134`.
4. Lifecycle fails:
   - inspect `reports/product_lifecycle_run.json` step return codes.
5. Gate fails:
   - inspect `reports/release_gate_report.json` and issue CSVs.

## 10. User management (Docker Compose)

When the platform is deployed via Docker Compose, use these commands to manage user accounts directly in the database.

### 10.1 List all users

```bash
docker exec dmm-postgres psql -U dmm_app -d dmm \
  -c "SELECT email, display_name, status, is_super_admin FROM users ORDER BY email;"
```

### 10.2 Reset all user passwords

Passwords are hashed with PBKDF2-SHA256. Generate the hash using the backend's own security module, then update the database.

```bash
docker exec dmm-backend python -c "
import sys, os
sys.path.insert(0, '/app/services/backend')
from app.security import hash_password
import psycopg2
new_hash = hash_password('NEW_PASSWORD_HERE')
conn = psycopg2.connect(os.environ.get('DM_DATABASE_URL', 'postgresql://dmm_app:change_me_postgres_password@postgres:5432/dmm'))
cur = conn.cursor()
cur.execute('UPDATE users SET password_hash = %s', (new_hash,))
conn.commit()
print(f'Updated {cur.rowcount} users')
cur.close()
conn.close()
"
```

Replace `NEW_PASSWORD_HERE` with the desired password.

The reported row count is the number of application login accounts currently present in the `users` table. In a freshly bootstrapped environment this may be only the two default users.

### 10.3 Reset a single user's password

```bash
docker exec dmm-backend python -c "
import sys, os
sys.path.insert(0, '/app/services/backend')
from app.security import hash_password
import psycopg2
new_hash = hash_password('NEW_PASSWORD_HERE')
conn = psycopg2.connect(os.environ.get('DM_DATABASE_URL', 'postgresql://dmm_app:change_me_postgres_password@postgres:5432/dmm'))
cur = conn.cursor()
cur.execute('UPDATE users SET password_hash = %s WHERE email = %s', (new_hash, 'TARGET_EMAIL'))
conn.commit()
print(f'Updated {cur.rowcount} user(s)')
cur.close()
conn.close()
"
```

Replace `NEW_PASSWORD_HERE` and `TARGET_EMAIL` with the desired values.

### 10.4 Invalidate all sessions and unlock accounts

Force all users to re-login with their new password and restore any locked accounts to `ACTIVE`:

```bash
docker exec dmm-postgres psql -U dmm_app -d dmm \
  -c "UPDATE users SET status = 'ACTIVE', session_revoked_at_utc = NOW()::text, failed_login_count = 0, locked_until_utc = '' WHERE TRUE;"
```

The login flow denies access to any user whose `status` is not `ACTIVE`, so clearing `locked_until_utc` alone does not unlock a user that is already marked `LOCKED`.

### 10.5 Verify login works

```bash
curl -s -X POST http://localhost:9134/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email": "TARGET_EMAIL", "password": "NEW_PASSWORD_HERE"}' | python3 -m json.tool
```

A successful response returns an `access_token` and `user` object.

## 11. Hardening backlog for true production cutover

1. Containerized deployment and pinned runtime images.
2. Secrets manager integration for ODBC/JDBC credentials.
3. TLS termination and strict CORS policy.
4. Authentication/authorization for all control-plane APIs.
5. Audit logging to SIEM and immutable run ledger.
6. Blue/green deployment for backend/frontend services.
