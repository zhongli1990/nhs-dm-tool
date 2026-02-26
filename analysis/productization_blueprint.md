# NHS PAS Migration Productization Blueprint

Date: 2026-02-25

## Product objective

Evolve this migration workspace into a reusable NHS migration product:
- enterprise-grade migration engine
- auditable governance and release controls
- full-stack UI control plane for DM engineers and stakeholders
- pluggable data connectors (CSV now, ODBC/JDBC next)

## Product architecture

1. Migration core (`pipeline/`)
- Schema extraction, semantic mapping, contract generation
- Contract-driven ETL with domain plugins and crosswalks
- Enterprise DQ checks and release gates

2. Control-plane backend (`product/backend/`)
- FastAPI endpoints for schemas, mappings, runs, rejects
- Connector plugin registry:
  - CSV connector active
  - PostgreSQL emulator active (target)
  - Cache/IRIS emulator active (source)
  - JSON dummy connector active
  - ODBC connector adapter stub
  - JDBC connector adapter stub

3. Control-plane frontend (`product/frontend/`)
- Next.js app router UI
- Dynamic rendering from generated artifacts
- Views:
  - Dashboard
  - Schemas
  - Mappings
  - Runs/Gates
  - Connectors

API specification:
- `analysis/api_surface_spec.md`
User operating model:
- `analysis/mission_critical_user_model.md`

## Connector strategy

Current:
- CSV connector (`CsvFolderConnector`) for source/target artifacts.

Planned:
1. ODBC plugin
- Read-only DSN enforcement
- information_schema introspection
- paginated sample pulls
- timeout + retry + query governor

2. JDBC plugin
- Driver-managed secure connection
- schema catalog discovery
- sampled extract endpoints

3. Shared connector controls
- secret vault integration
- connector health checks
- connector-level audit logs

## Enterprise readiness controls

1. Strict crosswalk translation with reject file
2. Domain plugins for high-risk tables (`PMI`, `ADT`, `OPD`)
3. Release-gate profiles:
- `development`
- `pre_production`
- `cutover_ready`
4. Resolution policy overrides for unresolved business-critical fields:
- `pipeline/mapping_resolution_policy.json`

## Implementation scope delivered

1. API backend scaffold in `product/backend/app/main.py`
2. Connector framework in `product/backend/app/connectors/`
3. Next.js control-plane scaffold in `product/frontend/app/`
4. Lifecycle orchestration command:
- `python pipeline/run_product_lifecycle.py --rows 20 --seed 42 --min-patients 20 --release-profile pre_production`

Current outcome:
- pre-production profile: PASS
- cutover-ready profile: intentionally stricter for final governance readiness

## Recommended next iteration

1. Enable ODBC connector with read-only policies and query limits.
2. Add role-based access control in backend/API.
3. Add API-triggered pipeline job queue (async runs + run state tracking).
4. Add table-level reconciliation UI:
- source count vs target count
- null-rate
- reject-rate
- FK chain completeness
