# QVH PAS Migration E2E Dry Run Lifecycle

Date: 2026-02-25  
Scope: `c:\Zhong\Windsurf\data_migration`

## Objective

Document the complete data migration lifecycle dry run from scratch for QVH PAS migration:
- requirements extraction
- schema profiling
- semantic mapping
- mapping contract
- ETL execution
- quality gates

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
  - `mock_data/source/*.csv` (priority + reference expansion)
  - `mock_data/target/*.csv` (all 38 LOAD tables)
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
- Result:
  - Target fields assessed: 919
  - Source fields assessed: 5,387

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
  - Issue counts: 0 ERROR, 5 WARN (reference-base unresolved tables)
  - Crosswalk rejects: 0 (`reports/contract_migration_rejects.csv`)

### Step 6: Enterprise quality gate
- Script: `run_enterprise_pipeline.py --min-patients 20`
- Status: PASS
- Outputs:
  - `reports/enterprise_pipeline_report.json`
  - `reports/enterprise_pipeline_issues.csv`
- Result:
  - 0 ERROR
  - 0 WARN

### Step 7: Release gates
- Script: `run_release_gates.py`
- Status: PASS with `pre_production` profile
- Outputs:
  - `reports/release_gate_report.json`
- Gate dimensions:
  - total errors
  - total warnings
  - unresolved mappings
  - crosswalk rejects
  - population ratio
  - target table count written
- Current failed gates:
  - none for `pre_production` profile
  - `cutover_ready` remains stricter and requires final governance/cutover thresholds

## Complete DM lifecycle (operating model)

1. Ingest and validate source/target requirement specs.
2. Generate authoritative schema catalogs and parse confidence summary.
3. Generate coherent source/target test data at required cohort size.
4. Perform semantic mapping analysis and gap surfacing.
5. Build signed mapping contract classification.
6. Execute contract-driven transformation and target staging outputs.
7. Run enterprise quality gates:
- source presence and row thresholds
- NHS checksum validity
- source/target referential integrity
- unresolved mapping governance checks
8. Produce audit artifacts and governance pack for sign-off.
9. Execute release-gate assessment and determine cutover readiness.

## Current implementation maturity

Implemented:
- Full catalog extraction
- Scalable patient-coherent mock generation
- Semantic mapping matrix
- Strict mapping contract
- Contract-driven ETL baseline runner
- Crosswalk translation engine with reject-file output
- Domain transformation plugins (`PMI`, `ADT`, `OPD`)
- Enterprise validation pipeline and issue reporting
- Threshold-based release gates

Pending hardening:
- Expand crosswalk coverage for all LOOKUP_TRANSLATION code domains
- Domain plugins for archive denormalization and complex derivations
- Row-splitting and advanced multi-source joins for selected targets
- Final cutover-ready gate thresholds and clinical governance sign-off

## Feature roadmap

### Phase 1: Mapping governance closure (short-term)
1. Resolve 25 unresolved business fields.
2. Confirm approved code sets with PAS vendor and NHS governance.
3. Finalize non-phantom OUT_OF_SCOPE dispositions.

### Phase 2: Transformation hardening (mid-term)
1. Implement deterministic crosswalk modules:
- sex, ethnicity, marital, religion
- admission/discharge/source/destination
- RTT status and outcomes
2. Implement table-specific derivation plugins for:
- `LOAD_ADT_ARCHIVE`
- `LOAD_OPD_ARCHIVE`
- `LOAD_DETENTION_ARCHIVE`
- `LOAD_CPA_ARCHIVE`

### Phase 3: Production readiness (pre-cutover)
1. Add reconciliation packs:
- source-to-target row parity
- mandatory completion rates
- FK-chain completeness percentages
2. Add release gates with hard fail thresholds.
3. Execute rehearsal cutovers and replay tests.

## Sign-off artifacts for governance board

- `schemas/schema_catalog_summary.json`
- `reports/semantic_mapping_summary.json`
- `reports/mapping_contract_summary.json`
- `reports/contract_migration_report.json`
- `reports/enterprise_pipeline_report.json`
- `reports/enterprise_pipeline_issues.csv`

## Product control-plane uplift

Implemented full-stack control-plane components:
1. Backend API (`product/backend/app/main.py`) with schema/mapping/run/connector endpoints.
2. Connector modes:
- `cache_iris_emulator` (source)
- `postgres_emulator` (target)
- `csv` (real file connector)
- `json_dummy` (dummy)
- `odbc` and `jdbc` (structured stubs)
3. Next.js UI pages for operations:
- dashboard
- schemas
- mappings
- lifecycle (stage-by-stage orchestration, run-all, parameter controls)
- runs
- connectors (dynamic configure/test/explore)
- users (mission-critical role ownership)

## UI-first lifecycle execution sequence

1. `Connectors`:
   - configure source and target connection profiles
   - run discovery and table preview
2. `Schemas`:
   - verify vendor schema ingestion and field profiles
3. `Mappings`:
   - validate mapping classes and filtered field-level contract rows
4. `Lifecycle`:
   - run stages in order:
     - extract specs
     - generate mock/source fixtures
     - semantic mapping
     - mapping contract
     - contract migration
     - enterprise quality
     - release gates
5. `Runs`:
   - confirm final status
   - review gate checks and reject sets
   - capture run evidence for governance.
