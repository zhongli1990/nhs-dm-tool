# Control Plane API Surface (Frontend Use Cases)

Date: 2026-02-26

Backend: `product/backend/app/main.py`

## Purpose

Provide enterprise-grade API coverage for DM engineer and stakeholder UI workflows:
- schema exploration
- ERD relationship visualization
- mapping inspection and approval workflows
- run execution and monitoring
- quality/reject triage
- release gate profile visibility
- connector exploration

## Endpoints

### Health
- `GET /health`

### Schema explorer
- `GET /api/schema/source`
- `GET /api/schema/target`
- `GET /api/schema/source/{table_name}`
- `GET /api/schema/target/{table_name}`

### ERD / relationship graph
- `GET /api/schema-graph/{domain}/relationships`
- `GET /api/schema-graph/{domain}/erd?table_filter=`

### Mapping explorer and workbench
- `GET /api/mappings/contract`
- `GET /api/mappings/contract/query?target_table=&mapping_class=&limit=`
- `GET /api/mappings/workbench?target_table=&status=&mapping_class=&offset=&limit=`
- `POST /api/mappings/workbench/upsert`
- `POST /api/mappings/workbench/transition`

### Runs and lifecycle orchestration
- `GET /api/runs/latest`
- `GET /api/runs/history`
- `POST /api/runs/execute?rows=&seed=&min_patients=&release_profile=`
- `GET /api/lifecycle/steps?rows=&seed=&min_patients=&release_profile=`
- `POST /api/lifecycle/steps/{step_id}/execute?rows=&seed=&min_patients=&release_profile=`
- `POST /api/lifecycle/execute-from/{step_id}?rows=&seed=&min_patients=&release_profile=`
- `GET /api/lifecycle/snapshots?limit=`
- `POST /api/lifecycle/snapshots/{snapshot_id}/restore`

### Quality and rejects
- `GET /api/quality/issues?kind=enterprise|contract|crosswalk_reject`
- `GET /api/rejects/crosswalk`
- `GET /api/quality/trends?limit=`
- `POST /api/quality/trends/seed?weeks=&replace=`
- `GET /api/quality/kpis`
- `POST /api/quality/kpis`
- `GET /api/quality/kpi-widgets?weeks=`

### Release gates
- `GET /api/gates/profiles`

### Connectors
- `POST /api/connectors/explore`
- `GET /api/connectors/templates`
- `GET /api/connectors/types`
- `GET /api/connectors/default/csv-source`
- `GET /api/connectors/default/csv-target-contract`

## Connector plugin readiness

CSV:
- active and usable in this build.

PostgreSQL emulator:
- active emulator over target CSV artifacts.

Cache/IRIS emulator:
- active emulator over source CSV artifacts.

JSON dummy:
- active placeholder connector for JSON integration flows.

ODBC/JDBC:
- experimental introspection adapters.
- intended for metadata discovery and sample reads before full production hardening.

## UX/API parity notes

1. Mappings pages use server-side pagination via workbench `offset` and `limit`.
2. Contract row filtering and mapping-class filtering are API-driven.
3. Lifecycle UI actions call the same backend command orchestration used for CLI artifacts.
4. ERD filters rely on `table_filter` query to render focused subgraphs.

## Security and operational notes

1. Current build is local/sandbox-oriented; production must add:
- RBAC
- secret vault integration
- API auth and audit logging

2. Execute-run endpoints currently shell pipeline commands:
- acceptable for internal engineering/pre-production simulation
- should migrate to controlled async job executor before production.
