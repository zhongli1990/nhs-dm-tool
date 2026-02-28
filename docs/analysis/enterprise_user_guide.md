# Enterprise User Guide: QVH PAS Migration Control Plane

Date: 2026-02-28  
Audience: NHS migration program teams running mission-critical PAS/EPR migrations.

## 1. Product vision for users

This control plane is designed to let operational users run the full migration lifecycle safely, with the same outcomes as engineering CLI execution.

Core outcomes:
1. governed and auditable lifecycle operations
2. clinically safe data-quality-first migration execution
3. dynamic handling of varied PAS/EPR schema models
4. high-volume workflows (paging, filtering, bulk actions)

## 2. Who uses this system

## 2.1 Primary users

1. Migration Delivery Lead
2. Data Mapping Analyst
3. ETL Engineer
4. Data Quality Lead
5. Clinical Safety/Assurance Reviewer
6. Cutover Manager

## 2.2 SaaS role tiers and tenant scope

1. Super Admin:
   - platform-wide access across all organizations, workspaces, and projects
   - manages global governance controls, approvals, and platform operations
2. Customer Org Admin (for example, QVH admin):
   - full access inside own organization only
   - manages organization users, workspaces, projects, and approval workflows
3. Customer Org Users (phase-1 broad in-org access):
   - operational roles such as DM engineer, architect, DQ lead, clinical reviewer, release manager
   - execute and govern lifecycle tasks in own org context only

## 2.3 Ownership by stage

1. Discovery and profiling: Mapping Analyst
2. Contract design and ETL build: ETL Engineer + Mapping Analyst
3. Quality and safety checks: Data Quality Lead + Clinical Safety
4. Release decision: Cutover Manager + Delivery Lead

## 2.4 Acute Trust real-world operating example

Example: an acute Trust running a major PAS to EPR migration programme:
1. Org Admin creates workspace `EPR Programme` and projects:
   - `Patient Administration Migration`
   - `Outpatients Migration`
   - `Inpatient/ADT Migration`
2. Data Architect validates schema onboarding and mapping contract coverage.
3. DM Engineers execute lifecycle rehearsals using `pre_production` profile.
4. DQ Lead and Clinical Reviewer assess KPI/issue evidence and mapping approvals.
5. Release Manager runs final readiness checks and decides promotion or rollback.
6. Super Admin oversees cross-Trust governance and audit traceability.

## 3. What the platform does

1. Profiles source and target schemas from requirement specs.
2. Builds semantic mapping and strict mapping contract.
3. Generates coherent mock source/target data cohorts.
4. Runs contract-driven ETL with crosswalk rejects.
5. Applies enterprise quality and release gates.
6. Exposes operational APIs and UI for governance and execution.

## 4. System pages and purpose

1. `/` Dashboard:
   - migration health snapshot (schema, ETL, quality, gates).
2. `/login` and `/register`:
   - secure sign-in and approval-driven onboarding request flow.
3. `/onboarding`:
   - enterprise setup for organization/workspace/project lifecycle context.
4. `/settings`:
   - runtime defaults and environment connectivity checks.
5. `/schemas`:
   - source/target table and column views.
6. `/erd`:
   - interactive relationship graph with table search and density control.
7. `/mappings`:
   - contract review plus edit/approve workbench.
8. `/lifecycle`:
   - stage-by-stage execution, rerun from selected step, snapshot restore.
9. `/runs`:
   - run execution and gate/reject evidence review.
10. `/quality`:
   - Dashboard, KPI Widgets, Issue Explorer.
11. `/connectors`:
   - connector type selection/configuration and schema discovery.
12. `/users`:
   - mission-critical role ownership model.
13. `/admin`:
   - enterprise user lifecycle, registration approvals, and role-permission operations.
14. `/documents`:
   - controlled document browsing/upload/download and markdown rendering.

## 5. UI operation model

1. Sidebar navigation groups:
   - Overview
   - Design
   - Execution
   - Ops
2. Top bar context operations:
   - compact `Context` popover for org/workspace/project switching
   - quick links for onboarding and settings
3. Dynamic rendering:
   - tables, columns, mapping rows, ERD links, and gate checks are API-driven.
4. Enterprise-scale controls:
   - server-side pagination in mappings views
   - bulk status/field actions in edit/approve workbench
   - searchable filters for schema and ERD exploration

## 6. Step-by-step lifecycle execution

## 6.1 Stage A: Pre-run controls

1. Confirm requirement specs exist in `requirement_spec/`.
2. Confirm release profile target:
   - development
   - pre_production
   - cutover_ready
3. Confirm patient cohort size and acceptance thresholds.

## 6.2 Stage B: Build artifacts

From project root:

```powershell
python .\pipeline\extract_specs.py
python .\pipeline\generate_all_mock_data.py --rows 20 --seed 42
python .\pipeline\analyze_semantic_mapping.py
python .\pipeline\build_mapping_contract.py
```

## 6.3 Stage C: Execute migration

```powershell
python .\pipeline\run_contract_migration.py --source-dir mock_data/source --output-dir mock_data/target_contract --contract-file reports/mapping_contract.csv --target-catalog-file schemas/target_schema_catalog.csv --crosswalk-dir schemas/crosswalks --impute-mode pre_production
```

## 6.4 Stage D: Quality and release gates

```powershell
python .\pipeline\run_enterprise_pipeline.py --min-patients 20
python .\pipeline\run_release_gates.py --profile pre_production
```

## 6.5 Stage E: Full one-command run

```powershell
python .\pipeline\run_product_lifecycle.py --rows 20 --seed 42 --min-patients 20 --release-profile pre_production
```

## 7. Running from full stack UI

## 7.1 Start platform

```powershell
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\run_fullstack.ps1 -BackendPort 9134 -FrontendPort 9133
```

Open:
1. UI: `http://127.0.0.1:9133`
2. API docs: `http://127.0.0.1:9134/docs`

## 7.2 Typical operator workflow in UI

1. `/connectors`: verify source/target connector config and preview.
2. `/onboarding`: ensure org/workspace/project are set for the current migration programme.
3. `/schemas`: validate source/target catalogs and key tables.
4. `/erd`: inspect inferred FK chains and table relationship coverage.
5. `/mappings`:
   - review Contract Rows with filters and pagination
   - perform bulk edit/status changes in Edit and Approve tab
6. `/lifecycle`: run stage-by-stage or rerun from selected step.
7. `/runs`: check return code, gate status, rejects and reports.
8. `/quality`:
   - monitor dashboard KPIs
   - tune widget window/refresh
   - triage issues in Issue Explorer
9. `/users`: review user directory, role assignments, and account lifecycle state.
10. `/admin`: process approvals, role updates, and audit-backed privileged actions.
11. `/documents`: browse lifecycle/deployment/design docs and download controlled artifacts.
12. `/settings`: validate runtime defaults and API connectivity.

## 8. Connector operation model

1. Real connector:
   - `csv`
2. Emulators:
   - `cache_iris_emulator` (source)
   - `postgres_emulator` (target)
3. Experimental placeholders:
   - `odbc`
   - `jdbc`
   - `json_dummy`

Policy:
1. Use emulators for rehearsal and development only.
2. Use CSV as controlled integration path in current build.
3. Keep ODBC/JDBC non-production until security controls are complete.

## 9. Decision gates and escalation rules

1. Any FAIL in release gates blocks cutover.
2. Any unresolved mandatory mapping blocks promotion.
3. Any crosswalk reject in safety-critical domains requires triage.
4. Any referential integrity break in patient chain blocks promotion.

## 10. Incident and rollback playbook

1. Stop services.
2. Freeze current reports and mapping contract as evidence.
3. Restore prior lifecycle snapshot or rerun known-good profile/seed.
4. Compare mapping contract deltas, reject deltas, and gate deltas.
5. Resume only after root-cause and mitigation approval.

## 11. Evidence package for governance board

1. `reports/product_lifecycle_run.json`
2. `reports/contract_migration_report.json`
3. `reports/enterprise_pipeline_report.json`
4. `reports/release_gate_report.json`
5. `reports/contract_migration_issues.csv`
6. `reports/enterprise_pipeline_issues.csv`
7. `reports/contract_migration_rejects.csv`
8. `reports/mapping_contract.csv`

## 13. Version governance and release traceability

1. Product version source of truth is `services/version_manifest.json`.
2. Login/register/top-bar/settings version labels are API-driven from `GET /api/meta/version`.
3. Release notes are maintained under `docs/release-notes/` and must align with manifest history.

## 12. Best practices for heavy migration programs

1. Use fixed seed and cohort for rehearsal comparability.
2. Lock mapping contract version per release candidate.
3. Maintain domain owners for high-risk table families (PMI, ADT, OPD, IWL, MH).
4. Enforce sign-off sequence: technical QA -> DQ -> clinical safety -> governance board.
