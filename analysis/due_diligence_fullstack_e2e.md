# Full-Stack Due Diligence Report (Mission-Critical Readiness)

Date: 2026-02-25  
Scope: QVH PAS/EPR DM lifecycle across backend pipelines, emulated connectors, runtime config, and Next.js control plane.

## Executive outcome

Current state is **operational for engineering/pre-production simulation** and passes lifecycle quality gates.  
Current state is **not yet production-safe** for mission-critical deployment without security and governance hardening.

## Runtime verification performed

1. Full stack launch:
- Backend started on `127.0.0.1:8099`
- Frontend started on `127.0.0.1:3133`

2. Live endpoint checks:
- `GET /health` -> `200`
- Frontend root page -> `200`
- `GET /api/connectors/types` -> `200`
- `POST /api/connectors/explore` tested for:
  - `cache_iris_emulator`
  - `postgres_emulator`
  - `json_dummy`

3. API-triggered lifecycle execution:
- `POST /api/runs/execute?rows=20&seed=42&min_patients=20&release_profile=pre_production`
- Result: return_code `0`, lifecycle status `PASS`

## Data and emulator checks

1. Mock source dataset:
- 38 source tables
- row count per table: min=20, max=20
- under-20 tables: 0

2. Mock target_contract dataset:
- 38 target tables
- row count per table: min=20, max=20
- under-20 tables: 0

3. Connector templates exposed:
- `cache_iris_emulator`
- `postgresql_emulator`
- `csv_source`
- `csv_target`
- `json_dummy`
- `odbc`
- `jdbc`

## E2E lifecycle controls

1. Product lifecycle report:
- `reports/product_lifecycle_run.json`
- Status: `PASS`

2. Enterprise quality report:
- `reports/enterprise_pipeline_report.json`
- Status: `PASS`
- Errors: `0`
- Warnings: `0`

3. Release gate report (`cutover_ready` profile):
- `reports/release_gate_report.json`
- Status: `PASS`
- Threshold checks all passed

## Security and operational due diligence findings

### High/Critical findings

1. Next.js dependency vulnerability (critical)
- `npm audit` reports critical advisory chain on current `next` version.
- Required action:
  - upgrade to patched `next` version (`14.2.35` or higher from advisory output)
  - rerun `npm audit`
  - rerun `npm run build` and regression test UI pages

2. Backend CORS currently `allow_origins=["*"]`
- acceptable for local engineering only
- not acceptable for production healthcare deployment
- required action:
  - restrict allowed origins by environment
  - add API auth, RBAC, and request auditing

### Medium findings

3. ODBC/JDBC are structured stubs
- connectors are intentionally placeholders and non-operational
- required action:
  - implement read-only DB credentials
  - add secret vault integration
  - add query timeout/limit controls
  - add connector telemetry and failure handling

4. API run execution uses direct subprocess
- functional for internal control plane
- required action:
  - move to managed async job runner/queue
  - persist run-state transitions and operator attribution

## Mission-critical go-live checklist (remaining)

1. Security:
- upgrade Next.js to patched version
- introduce auth/RBAC/session controls
- harden CORS, headers, and rate limits

2. Connectivity:
- implement real ODBC/JDBC connectors with read-only safeguards
- add integration tests against representative test DBs

3. Governance:
- finalize policy override sign-off with clinical governance
- lock `cutover_ready` thresholds and release process

4. Operations:
- package backend/frontend as managed services
- add centralized logging and alerting
- add disaster recovery and rollback runbook

## Verdict

Engineering due diligence status: **PASS for pre-production simulation**  
Production due diligence status: **CONDITIONAL** pending security/connectivity hardening actions above.
