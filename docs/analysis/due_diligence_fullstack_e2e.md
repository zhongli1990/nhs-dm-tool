# Full-Stack Due Diligence Report (Mission-Critical Readiness)

Date: 2026-02-27  
Scope: QVH PAS/EPR DM lifecycle across backend pipelines, emulated connectors, runtime config, and Next.js control plane.

## Executive outcome

Current state is **operational for engineering/pre-production simulation** and passes lifecycle quality gates.  
Current state is **not yet production-safe** for mission-critical deployment without security and governance hardening.

## Runtime verification baseline

1. Full stack launch verified:
- Backend on `127.0.0.1:9134`
- Frontend on `127.0.0.1:9133`

2. Live endpoint checks:
- `GET /health` -> `200`
- Frontend root page -> `200`
- `GET /api/connectors/types` -> `200`

3. API lifecycle execution path verified:
- `POST /api/runs/execute?rows=20&seed=42&min_patients=20&release_profile=pre_production`
- Result: return_code `0`, lifecycle status `PASS`

4. Mission-critical API surface validated:
- mapping workbench (`/api/mappings/workbench*`)
- ERD (`/api/schema-graph/{domain}/erd`)
- quality widgets (`/api/quality/kpi-widgets`)
- lifecycle snapshots (`/api/lifecycle/snapshots*`)

## Data and emulator checks

1. Mock source dataset:
- source tables present and populated for lifecycle rehearsal

2. Mock target_contract dataset:
- all 38 target tables present
- row counts satisfy current minimum thresholds

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

3. Release gate report:
- `reports/release_gate_report.json`
- `pre_production`: PASS
- `cutover_ready`: profile exists and should be used with final governance thresholds

## UX readiness observations

Implemented now:
1. SaaS auth baseline (login/register/approval + tenant context guard)
1. theme modes (light/dark/system) with improved readability fixes
2. mappings workbench high-volume operations (pagination, bulk actions)
3. ERD improved auto-layout with relationship list IDs and filters
4. quality tab KPI widgets, trends, and issue explorer

Residual UX backlog:
1. richer ERD interaction (manual drag/pin/minimap)
2. deeper run/audit timeline visualizations

## Security and operational due diligence findings

### High/Critical findings

1. Frontend dependency vulnerability risk
- keep Next.js and transitive dependencies patched
- run `npm audit` in release workflow

2. Open CORS policy in local mode
- `allow_origins=["*"]` is local-only
- production requires strict origin allow-list and auth

### Medium findings

3. ODBC/JDBC connectors are experimental
- production needs credential vault, query governance, and telemetry

4. Run execution currently subprocess-based
- production should use managed async queue/executor with durable state

## Mission-critical go-live checklist (remaining)

1. Security:
- fine-grained RBAC hardening and federated auth (OIDC/SAML)
- strict CORS/headers/rate limits
- secrets vault integration

2. Connectivity:
- production-grade ODBC/JDBC adapters
- integration tests against representative source/target DBs

3. Governance:
- finalize policy override sign-off
- lock `cutover_ready` thresholds and approval process

4. Operations:
- managed service/container deployment
- centralized logging/alerting and immutable audit trail
- DR and rollback runbook hardening

## Verdict

Engineering due diligence status: **PASS for pre-production simulation**  
Production due diligence status: **CONDITIONAL** pending hardening actions above.

