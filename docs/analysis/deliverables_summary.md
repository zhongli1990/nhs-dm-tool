# QVH PAS Migration Deliverables Summary

Date: 2026-02-27  
Program: NHS QVH PAS to PAS 18.4 migration control-plane and pipeline stack.

## 1. Delivered capability summary

1. End-to-end migration lifecycle pipeline:
   - spec extraction
   - schema profiling
   - semantic mapping
   - mapping contract
   - contract ETL
   - enterprise quality
   - release gates
2. Scalable coherent mock data generation:
   - all 38 target tables
   - expanded source/reference table set
   - configurable patient row count
3. Full-stack product shell:
   - FastAPI backend
   - Next.js frontend
   - API endpoints for schema/mapping/run/quality/connectors
4. Connector framework:
   - CSV real connector
   - Cache/IRIS emulator connector
   - PostgreSQL emulator connector
   - ODBC/JDBC experimental introspection connectors
   - JSON dummy connector
5. Priority feature uplift (1-5) implemented:
   - mapping workbench + approval workflow
   - ODBC/JDBC introspection path
   - ERD relationship APIs + UI
   - quality trends history and dashboard
   - selective rerun-from-step + snapshot restore
6. UX hardening for enterprise operations:
   - workbench JSON recovery and resilient API read path
   - server-side pagination for workbench editing (default 200/page)
   - contract rows pagination with configurable page size
   - ERD force-layout density controls and ID in relationship list
   - dark/light visibility fixes for controls and logs
7. SaaS uplift and operator UX expansion:
   - login/register with approval workflow
   - tenant context hierarchy (`org -> workspace -> project`)
   - compact top-bar `Context` popover
   - onboarding page (`/onboarding`)
   - settings page (`/settings`)

## 2. Code structure

## 2.1 Root

1. [README.md](c:/Zhong/Windsurf/data_migration/README.md)
2. `requirement_spec/`
3. `schemas/`
4. `mock_data/`
5. `reports/`
6. `analysis/`
7. `pipeline/`
8. `product/`

## 2.2 Pipeline layer

1. [extract_specs.py](c:/Zhong/Windsurf/data_migration/pipeline/extract_specs.py)
2. [generate_all_mock_data.py](c:/Zhong/Windsurf/data_migration/pipeline/generate_all_mock_data.py)
3. [analyze_semantic_mapping.py](c:/Zhong/Windsurf/data_migration/pipeline/analyze_semantic_mapping.py)
4. [build_mapping_contract.py](c:/Zhong/Windsurf/data_migration/pipeline/build_mapping_contract.py)
5. [run_contract_migration.py](c:/Zhong/Windsurf/data_migration/pipeline/run_contract_migration.py)
6. [run_enterprise_pipeline.py](c:/Zhong/Windsurf/data_migration/pipeline/run_enterprise_pipeline.py)
7. [run_release_gates.py](c:/Zhong/Windsurf/data_migration/pipeline/run_release_gates.py)
8. [run_product_lifecycle.py](c:/Zhong/Windsurf/data_migration/pipeline/run_product_lifecycle.py)
9. `pipeline/enterprise/` modules:
   - checks
   - validators
   - crosswalks
   - transform plugins
   - contract ETL models/IO

## 2.3 Product layer

1. [product/README.md](c:/Zhong/Windsurf/data_migration/product/README.md)
2. Backend:
   - [main.py](c:/Zhong/Windsurf/data_migration/product/backend/app/main.py)
   - `connectors/*.py`
   - `services/*.py`
3. Frontend:
   - [app/page.tsx](c:/Zhong/Windsurf/data_migration/product/frontend/app/page.tsx)
   - `app/schemas/page.tsx`
   - `app/erd/page.tsx`
   - `app/mappings/page.tsx`
   - `app/quality/page.tsx`
   - `app/lifecycle/page.tsx`
   - `app/runs/page.tsx`
   - `app/connectors/page.tsx`
   - `app/users/page.tsx`
4. Runtime scripts:
   - [run_fullstack.ps1](c:/Zhong/Windsurf/data_migration/product/scripts/run_fullstack.ps1)
   - [run_backend.ps1](c:/Zhong/Windsurf/data_migration/product/scripts/run_backend.ps1)
   - [run_frontend.ps1](c:/Zhong/Windsurf/data_migration/product/scripts/run_frontend.ps1)

## 3. E2E design

## 3.1 Data flow

1. Parse source/target specs into catalogs.
2. Generate/ingest source extracts.
3. Build semantic mapping matrix.
4. Build strict mapping contract.
5. Transform source to target_contract via contract ETL.
6. Enforce quality checks and release gate policy.
7. Publish operational artifacts to API/UI.

## 3.2 Governance model

1. Mapping classes enforce explicit semantics:
   - DIRECT_SOURCE
   - DERIVED
   - LOOKUP_TRANSLATION
   - SURROGATE_ETL
   - REFERENCE_MASTER_FEED
   - OUT_OF_SCOPE
2. Crosswalk rejects are explicit outputs, not hidden coercions.
3. Gate profiles separate engineering readiness vs cutover readiness.

## 4. Current runtime topology

1. Backend API host/port: `127.0.0.1:9134`
2. Frontend host/port: `127.0.0.1:9133`
3. Frontend uses backend API base:
   - `NEXT_PUBLIC_DM_API_BASE=http://127.0.0.1:9134`

## 4.1 UI lifecycle uplift (v0.2.0)

1. Sidebar-based workflow navigation for mission-critical operations.
2. Lifecycle orchestration page with parameter controls and stage execution.
3. Runs console with release profile controls and gate/reject tabs.
4. Dynamic schema and mapping explorers with filtering and drill-down.
5. Connector console with discovery, preview and operational setup flow.
6. Quality command centre with tabbed views:
   - Dashboard
   - KPI Widgets
   - Issue Explorer
7. KPI widget controls:
   - weeks window
   - auto-refresh
   - manual refresh
   - demo trend seeding
8. Mappings workbench controls:
   - server-side paged edit/approve table
   - page size + page up/down
   - row ID for operator reference
9. ERD controls:
   - searchable table selector
   - layout density control (`compact`, `normal`, `sparse`)
   - relationship list row ID and cardinality labels
10. SaaS controls:
   - auth-first protected routes
   - tenant-aware context switching in compact popover
   - onboarding and settings flows

## 4.2 Feature uplift status matrix

1. Mapping workbench and approvals: Implemented (MVP)
- APIs: `/api/mappings/workbench*`
- status model: `DRAFT`, `IN_REVIEW`, `APPROVED`, `REJECTED`

2. ODBC/JDBC introspection: Implemented (experimental)
- adapters support list/describe/sample where drivers are available
- production hardening pending secret vault + auth + query governance

3. ERD and relationship graph: Implemented (MVP)
- APIs: `/api/schema-graph/{domain}/relationships`, `/api/schema-graph/{domain}/erd`
- UI route: `/erd`

4. Quality trends and KPI dashboard: Implemented (MVP+)
- trend history file + APIs
- tabbed quality UI with sparkline widget scorecards

5. Selective rerun and snapshot restore: Implemented (MVP)
- APIs:
  - `/api/lifecycle/execute-from/{step_id}`
  - `/api/lifecycle/snapshots`
  - `/api/lifecycle/snapshots/{snapshot_id}/restore`

## 5. Document index

## 5.1 Core analysis docs

1. [schema_analysis.md](c:/Zhong/Windsurf/data_migration/analysis/schema_analysis.md)
2. [source_schema_profile.md](c:/Zhong/Windsurf/data_migration/analysis/source_schema_profile.md)
3. [target_schema_profile.md](c:/Zhong/Windsurf/data_migration/analysis/target_schema_profile.md)
4. [gap_register.md](c:/Zhong/Windsurf/data_migration/analysis/gap_register.md)
5. [source_target_semantic_mapping.md](c:/Zhong/Windsurf/data_migration/analysis/source_target_semantic_mapping.md)
6. [mapping_contract.md](c:/Zhong/Windsurf/data_migration/analysis/mapping_contract.md)
7. [mapping_reestablished.md](c:/Zhong/Windsurf/data_migration/analysis/mapping_reestablished.md)
8. [mapping_rework_findings.md](c:/Zhong/Windsurf/data_migration/analysis/mapping_rework_findings.md)

## 5.2 Product and operations docs

1. [productization_blueprint.md](c:/Zhong/Windsurf/data_migration/analysis/productization_blueprint.md)
2. [mission_critical_user_model.md](c:/Zhong/Windsurf/data_migration/analysis/mission_critical_user_model.md)
3. [api_surface_spec.md](c:/Zhong/Windsurf/data_migration/analysis/api_surface_spec.md)
4. [connector_stub_spec.md](c:/Zhong/Windsurf/data_migration/analysis/connector_stub_spec.md)
5. [fullstack_runtime_strategy.md](c:/Zhong/Windsurf/data_migration/analysis/fullstack_runtime_strategy.md)
6. [qvh_pas_migration_e2e_lifecycle.md](c:/Zhong/Windsurf/data_migration/analysis/qvh_pas_migration_e2e_lifecycle.md)
7. [due_diligence_fullstack_e2e.md](c:/Zhong/Windsurf/data_migration/analysis/due_diligence_fullstack_e2e.md)

## 5.3 New runbooks

1. [deployment_guide.md](c:/Zhong/Windsurf/data_migration/analysis/deployment_guide.md)
2. [enterprise_user_guide.md](c:/Zhong/Windsurf/data_migration/analysis/enterprise_user_guide.md)

