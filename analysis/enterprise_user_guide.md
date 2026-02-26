# Enterprise User Guide: QVH PAS Migration Control Plane

Date: 2026-02-25  
Audience: NHS migration program teams running mission-critical PAS/EPR migrations.

## 1. Who uses this system

## 1.1 Primary users

1. Migration Delivery Lead
2. Data Mapping Analyst
3. ETL Engineer
4. Data Quality Lead
5. Clinical Safety/Assurance Reviewer
6. Cutover Manager

## 1.2 Ownership by stage

1. Discovery and profiling: Mapping Analyst
2. Contract design and ETL build: ETL Engineer + Mapping Analyst
3. Quality and safety checks: Data Quality Lead + Clinical Safety
4. Release decision: Cutover Manager + Delivery Lead

## 2. What the platform does

1. Profiles source and target schemas from requirement specs.
2. Builds semantic mapping and strict mapping contract.
3. Generates coherent mock source/target data cohorts.
4. Runs contract-driven ETL with crosswalk rejects.
5. Applies enterprise quality and release gates.
6. Exposes operational APIs and UI for governance and execution.

## 3. System pages and purpose

1. `/` Dashboard:
   - migration health snapshot (schema, ETL, quality, gates).
2. `/schemas`:
   - source/target table and column views.
3. `/mappings`:
   - mapping contract inspection and class filtering.
4. `/runs`:
   - run execution and report review.
5. `/connectors`:
   - connector type selection/config and schema discovery.
6. `/users`:
   - mission-critical role ownership model.

## 3.1 UI operation model (uplifted)

1. Sidebar navigation groups:
   - Overview
   - Design
   - Execution
   - Ops
2. Tabbed workflows for heavy data tasks:
   - schemas: source/target tabs + table drill-down
   - mappings: summary vs field-row tabs with filters
   - runs: overview vs gate checks vs rejects
3. Dynamic rendering:
   - tables, columns, mapping rows and gate checks are API-driven, not hardcoded.

## 4. Step-by-step lifecycle execution (real-world pattern)

## 4.1 Stage A: Pre-run controls

1. Confirm requirement specs exist in `requirement_spec/`.
2. Confirm release profile target:
   - development
   - pre_production
   - cutover_ready
3. Confirm patient cohort size and acceptance thresholds.

## 4.2 Stage B: Build artifacts

From project root:

```powershell
python .\pipeline\extract_specs.py
python .\pipeline\generate_all_mock_data.py --rows 20 --seed 42
python .\pipeline\analyze_semantic_mapping.py
python .\pipeline\build_mapping_contract.py
```

Operator checks:

1. `schemas/schema_catalog_summary.json` generated.
2. `reports/mapping_contract.csv` generated.
3. No extraction/parser failures.

## 4.3 Stage C: Execute migration

```powershell
python .\pipeline\run_contract_migration.py --source-dir mock_data/source --output-dir mock_data/target_contract --contract-file reports/mapping_contract.csv --target-catalog-file schemas/target_schema_catalog.csv --crosswalk-dir schemas/crosswalks --impute-mode pre_production
```

Operator checks:

1. 38 target tables written to `mock_data/target_contract/`.
2. `reports/contract_migration_report.json` status PASS.
3. Reject count reviewed (`reports/contract_migration_rejects.csv`).

## 4.4 Stage D: Quality and release gates

```powershell
python .\pipeline\run_enterprise_pipeline.py --min-patients 20
python .\pipeline\run_release_gates.py --profile pre_production
```

Operator checks:

1. `enterprise_pipeline_report.json` has no blockers.
2. `release_gate_report.json` is PASS for selected profile.
3. If `cutover_ready` is used, governance thresholds must pass.

## 4.5 Stage E: Full one-command run (for controlled repeatability)

```powershell
python .\pipeline\run_product_lifecycle.py --rows 20 --seed 42 --min-patients 20 --release-profile pre_production
```

Operator checks:

1. `reports/product_lifecycle_run.json` status PASS.
2. Every step return code is `0`.

## 5. Running with the full stack UI

## 5.1 Start platform

```powershell
powershell -ExecutionPolicy Bypass -File c:\Zhong\Windsurf\data_migration\product\scripts\run_fullstack.ps1 -BackendPort 8099 -FrontendPort 3133
```

Open:

1. UI: `http://127.0.0.1:3133`
2. API docs: `http://127.0.0.1:8099/docs`

## 5.2 Typical operator workflow in UI

1. `/schemas`: validate source/target catalog shape.
2. `/connectors`: verify source/target connector visibility and preview.
3. `/mappings`: review key classes:
   - DIRECT_SOURCE
   - LOOKUP_TRANSLATION
   - DERIVED
   - SURROGATE_ETL
   - REFERENCE_MASTER_FEED
   - OUT_OF_SCOPE
4. `/lifecycle`: run step-by-step lifecycle stages or run-all with controlled parameters.
5. `/runs`: trigger full lifecycle, inspect outputs, gates, and rejects.
6. `/runs` + `/mappings`: investigate warnings/rejects and loop to resolution.

## 6. Connector operation model

1. Real connector:
   - `csv`
2. Emulators:
   - `cache_iris_emulator` (source)
   - `postgres_emulator` (target)
3. Placeholders/stubs:
   - `odbc`
   - `jdbc`
   - `json_dummy`

Usage policy for enterprise runs:

1. Treat emulators as validation aids, not production data source of record.
2. Use CSV imports/exports as controlled integration method in current build.
3. Keep ODBC/JDBC in design mode until security controls are complete.

## 7. Decision gates and escalation rules

1. Any FAIL in release gates blocks cutover.
2. Any unresolved mandatory mapping blocks promotion.
3. Any crosswalk reject in safety-critical domains requires triage.
4. Any referential integrity break in patient chain blocks promotion.

## 8. Incident and rollback playbook

1. Stop services.
2. Freeze current reports and mapping contract as evidence.
3. Re-run previous known-good lifecycle seed/profile.
4. Compare:
   - mapping contract diff
   - reject/issue deltas
   - gate outputs
5. Only resume after root-cause and mitigation approval.

## 9. Evidence package for governance board

1. `reports/product_lifecycle_run.json`
2. `reports/contract_migration_report.json`
3. `reports/enterprise_pipeline_report.json`
4. `reports/release_gate_report.json`
5. `reports/contract_migration_issues.csv`
6. `reports/enterprise_pipeline_issues.csv`
7. `reports/contract_migration_rejects.csv`
8. `reports/mapping_contract.csv`

## 10. Operational best practices for heavy DM programs

1. Use fixed seed and cohort for rehearsal comparability.
2. Lock mapping contract version per release candidate.
3. Maintain domain owners for each high-risk target table family:
   - PMI
   - ADT
   - OPD
   - IWL
   - MH/CPA/Detention
4. Enforce strict sign-off sequence:
   - technical QA
   - data quality
   - clinical safety
   - governance board.
