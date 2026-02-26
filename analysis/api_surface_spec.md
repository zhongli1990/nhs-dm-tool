# Control Plane API Surface (Frontend Use Cases)

Date: 2026-02-25

Backend: `product/backend/app/main.py`

## Purpose

Provide enterprise-grade API coverage for DM engineer and stakeholder UI workflows:
- schema exploration
- mapping inspection
- run execution and monitoring
- quality/reject triage
- release gate and profile visibility
- connector exploration

## Endpoints

### Health
- `GET /health`

### Schema explorer
- `GET /api/schema/source`
- `GET /api/schema/target`
- `GET /api/schema/source/{table_name}`
- `GET /api/schema/target/{table_name}`

### Mapping explorer
- `GET /api/mappings/contract`
- `GET /api/mappings/contract/query?target_table=&mapping_class=&limit=`

### Runs and reports
- `GET /api/runs/latest`
- `GET /api/runs/history`
- `POST /api/runs/execute?rows=&seed=&min_patients=&release_profile=`

### Quality and rejects
- `GET /api/quality/issues?kind=enterprise|contract|crosswalk_reject`
- `GET /api/rejects/crosswalk`

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

ODBC:
- adapter stub implemented with detailed placeholder contract for:
  - connection string
  - schema selection
  - table listing
  - table description
  - row sampling

JDBC:
- adapter stub implemented with same contract shape as ODBC.

## Security and operational notes

1. Current build is local/sandbox-oriented; production must add:
- RBAC
- secret vault integration
- API auth and audit

2. Execute-run endpoint currently shells to pipeline command:
- acceptable for internal engineering setup
- should migrate to controlled async job executor before production.
PostgreSQL emulator:
- active emulator over target CSV artifacts
- schema-qualified table naming (`public.load_*`)

Cache/IRIS emulator:
- active emulator over source CSV artifacts
- uppercase legacy-style table naming (`INQUIRE.PATDATA`)

JSON dummy:
- active placeholder for JSON payload integrations
- synthetic metadata and sample rows
