# QVH PAS Migration E2E Dry Run Lifecycle

Date: 2026-02-28  
Scope: `c:\Zhong\Windsurf\data_migration`

## Objective

Document the complete data migration lifecycle dry run from scratch for QVH PAS migration:
- requirements extraction
- schema profiling
- semantic mapping
- mapping contract
- ETL execution
- quality gates
- UI/API operational control-plane parity

## SaaS role alignment for this lifecycle

1. Super Admin:
- platform oversight and cross-tenant governance
2. QVH Org Admin:
- onboarding and tenant/project administration
3. QVH delivery roles:
- DM Engineer: execution
- Data Architect: mapping governance
- DQ Lead + Clinical Reviewer: quality/safety assurance
- Release Manager: final gate decision

## Lifecycle prerequisites

1. Requirement specs present in `requirement_spec/`.
2. Python environment available for pipeline scripts.
3. Working folders available:
- `schemas/`
- `mock_data/source/`
- `mock_data/target/`
- `mock_data/target_contract/`
- `reports/`

## End-to-end command sequence

Run from `c:\Zhong\Windsurf\data_migration`:

```powershell
python .\pipeline\extract_specs.py
python .\pipeline\generate_all_mock_data.py --rows 20 --seed 42
python .\pipeline\analyze_semantic_mapping.py
python .\pipeline\build_mapping_contract.py
python .\pipeline\run_contract_migration.py --source-dir mock_data/source --output-dir mock_data/target_contract --contract-file reports/mapping_contract.csv --target-catalog-file schemas/target_schema_catalog.csv --crosswalk-dir schemas/crosswalks --impute-mode pre_production
python .\pipeline\run_enterprise_pipeline.py --min-patients 20
python .\pipeline\run_release_gates.py --profile pre_production
```

## Dry run execution evidence

### Step 1: Requirements to schema catalogs
- Script: `extract_specs.py`
- Status: PASS
- Outputs:
  - `schemas/source_schema_catalog.csv`
  - `schemas/target_schema_catalog.csv`
  - `schemas/schema_catalog_summary.json`
- Result:
  - Source: 417 tables, 5,387 fields
  - Target: 38 tables, 880 fields
  - Target parse confidence avg: 0.819

### Step 2: Mock data generation (patient-coherent)
- Script: `generate_all_mock_data.py --rows 20 --seed 42`
- Status: PASS
- Outputs:
  - `mock_data/source/*.csv`
  - `mock_data/target/*.csv`
- Result:
  - 20-patient coherent data generated
  - Source includes PATDATA (131 cols), ADMITDISCH (69 cols), HWSAPP (90 cols), AEA (69 cols), plus additional tables

### Step 3: Semantic mapping analysis
- Script: `analyze_semantic_mapping.py`
- Status: PASS
- Outputs:
  - `reports/semantic_mapping_matrix.csv`
  - `reports/semantic_mapping_summary.json`
  - `analysis/source_target_semantic_mapping.md`

### Step 4: Strict mapping contract build
- Script: `build_mapping_contract.py`
- Status: PASS
- Outputs:
  - `reports/mapping_contract.csv`
  - `reports/mapping_contract_summary.json`
  - `analysis/mapping_contract.md`
- Result (class counts):
  - DIRECT_SOURCE: 258
  - LOOKUP_TRANSLATION: 207
  - DERIVED: 153
  - SURROGATE_ETL: 143
  - REFERENCE_MASTER_FEED: 104
  - OUT_OF_SCOPE: 54

### Step 5: Contract-driven ETL execution
- Script: `run_contract_migration.py`
- Status: PASS
- Outputs:
  - `mock_data/target_contract/*.csv`
  - `reports/contract_migration_report.json`
  - `reports/contract_migration_table_stats.csv`
  - `reports/contract_migration_issues.csv`
- Result:
  - Tables written: 38
  - Total rows written: 760
  - Overall column population ratio: 0.6784
  - Issue counts: 0 ERROR, 5 WARN
  - Crosswalk rejects: 0 (`reports/contract_migration_rejects.csv`)

### Step 6: Enterprise quality gate
- Script: `run_enterprise_pipeline.py --min-patients 20`
- Status: PASS
- Outputs:
  - `reports/enterprise_pipeline_report.json`
  - `reports/enterprise_pipeline_issues.csv`
- Result: 0 ERROR, 0 WARN

### Step 7: Release gates
- Script: `run_release_gates.py --profile pre_production`
- Status: PASS
- Outputs:
  - `reports/release_gate_report.json`

## Complete DM lifecycle (operating model)

1. Ingest and validate source/target requirement specs.
2. Generate authoritative schema catalogs and parse confidence summary.
3. Generate coherent source/target test data at required cohort size.
4. Perform semantic mapping analysis and gap surfacing.
5. Build signed mapping contract classification.
6. Execute contract-driven transformation and target staging outputs.
7. Run enterprise quality gates and release gates.
8. Produce audit artifacts and governance pack for sign-off.
9. Execute release-gate assessment and determine cutover readiness.

## Current implementation maturity

Implemented:
- full catalog extraction and profiling
- coherent 20+ patient mock generation
- semantic mapping matrix and strict mapping contract
- contract-driven ETL with crosswalk rejects
- enterprise quality and release gate profiles
- full-stack control plane with lifecycle parity
- mappings workbench with pagination and bulk actions
- ERD visual explorer with inferred relationships and density control
- quality command centre (Dashboard, KPI Widgets, Issue Explorer)
- enterprise user lifecycle and RBAC operations (users directory, role matrix, session reset)
- documents module for lifecycle/deployment/design artifact browsing and controlled download/upload

Pending hardening:
- federated SSO integration (OIDC/SAML) with managed identity providers
- async job orchestration with durable run state
- deeper connector hardening for ODBC/JDBC
- final cutover-ready governance sign-off

## UI-first lifecycle execution sequence

1. `Connectors`: configure source/target profile and preview metadata.
2. `Onboarding`: confirm organization/workspace/project context for the programme.
3. `Schemas`: verify catalog completeness.
4. `ERD`: validate key relationship chains and cardinality inferences.
5. `Mappings`: review Contract Rows and execute Edit/Approve workflow.
6. `Lifecycle`: run step-by-step or rerun from selected stage.
7. `Runs`: verify run outcome and gate status.
8. `Quality`: review KPI widgets and issue triage outputs.
9. `Documents`: review lifecycle runbooks/deployment guides/design records.
10. `Settings`: verify runtime defaults and version history for governance traceability.

## Versioning and evidence alignment

1. Manifest source of truth: `services/version_manifest.json`.
2. API version endpoint: `GET /api/meta/version`.
3. Release notes location: `docs/release-notes/`.

## Sign-off artifacts for governance board

- `schemas/schema_catalog_summary.json`
- `reports/semantic_mapping_summary.json`
- `reports/mapping_contract_summary.json`
- `reports/contract_migration_report.json`
- `reports/enterprise_pipeline_report.json`
- `reports/release_gate_report.json`
- `reports/enterprise_pipeline_issues.csv`
- `reports/contract_migration_rejects.csv`
