# NHS QVH PAS Data Migration Workspace

Metadata-driven migration tooling for Queen Victoria Hospital PAS migration:
- Source: PC60/V83 legacy PAS
- Target: PAS 18.4

Requirement inputs:
- `requirement_spec/Source PAS - Data Dictionary V83 INQuire DD PC83.xlsx`
- `requirement_spec/Source PAS - PAS_PC60_DataDictionary.docx`
- `requirement_spec/Target PAS - PAS 18.4 Data Migration Technical Guide - FOR REF ONLY NOT TO BE USED.pdf`

## Repository layout

- `analysis/` design documents, schema profiling, gap analysis, mapping findings
- `schemas/` extracted source/target catalogs and summary metadata
- `mock_data/source/` generated source test extracts
- `mock_data/target/` generated target fixture tables
- `mock_data/target_contract/` contract-driven ETL outputs
- `pipeline/` extract, mapping, generation, ETL, and quality gate scripts
- `reports/` machine-readable run reports and issue exports
- `product/` full-stack control plane (FastAPI backend + Next.js frontend)

## End-to-end lifecycle run

Run from the project root:

```powershell
cd c:\Zhong\Windsurf\data_migration
python .\pipeline\extract_specs.py
python .\pipeline\generate_all_mock_data.py --rows 20 --seed 42
python .\pipeline\analyze_semantic_mapping.py
python .\pipeline\build_mapping_contract.py
python .\pipeline\run_contract_migration.py --source-dir mock_data/source --output-dir mock_data/target_contract --contract-file reports/mapping_contract.csv --target-catalog-file schemas/target_schema_catalog.csv --crosswalk-dir schemas/crosswalks --impute-mode pre_production
python .\pipeline\run_enterprise_pipeline.py --min-patients 20
python .\pipeline\run_release_gates.py --profile pre_production
python .\pipeline\run_product_lifecycle.py --rows 20 --seed 42 --min-patients 20 --release-profile pre_production
```

## Current dry-run status (2026-02-25)

- Schema extraction: PASS
  - 417 source tables, 5,387 source fields
  - 38 target tables, 880 target fields
- Mock generation: PASS
  - 38 target tables with 20 rows each
  - 13 priority source tables plus expanded reference/context set
- Semantic mapping analysis: PASS
- Mapping contract build: PASS
  - 919 target fields classified
- Contract-driven ETL execution: PASS
  - 38 target tables materialized to `mock_data/target_contract`
  - crosswalk rejects: 0
  - population ratio: 0.6784
- Enterprise quality gate: PASS
  - 0 errors, 0 warnings
- Release gates:
  - pre-production profile: PASS
  - cutover-ready profile: pending governance thresholds and final clinical sign-off

## Core outputs

- Schema summary: `schemas/schema_catalog_summary.json`
- Mapping contract: `reports/mapping_contract.csv`
- Semantic matrix: `reports/semantic_mapping_matrix.csv`
- Contract ETL report: `reports/contract_migration_report.json`
- Contract ETL rejects: `reports/contract_migration_rejects.csv`
- Enterprise gate report: `reports/enterprise_pipeline_report.json`
- Release gate report: `reports/release_gate_report.json`
- Product lifecycle report: `reports/product_lifecycle_run.json`
- Lifecycle narrative and steps: `analysis/qvh_pas_migration_e2e_lifecycle.md`
- Product blueprint: `analysis/productization_blueprint.md`
- API surface: `analysis/api_surface_spec.md`
- Connector experimental spec: `analysis/connector_stub_spec.md`
- User model and lifecycle ownership: `analysis/mission_critical_user_model.md`
- Runtime strategy: `analysis/fullstack_runtime_strategy.md`
- Full-stack due diligence: `analysis/due_diligence_fullstack_e2e.md`
- Deliverables summary index: `analysis/deliverables_summary.md`
- Deployment guide: `analysis/deployment_guide.md`
- Enterprise user guide: `analysis/enterprise_user_guide.md`
- Enterprise onboarding and DQ roadmap: `analysis/enterprise_onboarding_and_dq_roadmap.md`

## Implementation notes

- `run_migration.py` is legacy baseline and retained for reference.
- Production-direction flow is contract-driven:
  - extract -> generate/profile -> semantic map -> contract classify -> contract ETL -> quality gate -> release gates.
- Crosswalk dictionaries are in `schemas/crosswalks/*.csv` and drive strict lookup translation.
- Release gate profiles are in `pipeline/release_gate_profiles.json`.
- Policy overrides for unresolved business fields are in `pipeline/mapping_resolution_policy.json`.

## Productization UI

See `product/README.md` for running:
- FastAPI backend (`product/backend`)
- Next.js dynamic UI (`product/frontend`)

UI lifecycle uplift (v0.0.2):
- step-by-step execution console at `/lifecycle`
- dynamic schema/table/field explorer
- visual schema ERD page at `/erd` (PK/FK/inferred lineage graph MVP)
- dynamic mapping contract filtering
- run controls with profile/rows/seed/min-patient parameters
- gate/reject operational review tabs
- quality command centre tabs:
  - Dashboard
  - KPI Widgets
  - Issue Explorer
- lifecycle rerun and snapshot restore controls

Connector modes currently exposed in API/UI:
- `cache_iris_emulator` (source, active)
- `postgres_emulator` (target, active)
- `csv` (real file connector, active)
- `json_dummy` (dummy placeholder, active)
- `odbc` / `jdbc` (experimental introspection connectors)
