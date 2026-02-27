# Enterprise Migration Pipeline Design (Start Point)

Date: 2026-02-25

## Purpose

This design establishes an executable, contract-driven migration pipeline for PAS V83 -> PAS 18.4 target LOAD tables, with auditable controls for data quality and mapping completeness.

## Pipeline components

1. `pipeline/generate_all_mock_data.py`
- Produces coherent source and target mock datasets at configurable patient volume.

2. `pipeline/build_mapping_contract.py`
- Produces field-level mapping contract with strict classes:
  - `DIRECT_SOURCE`
  - `DERIVED`
  - `LOOKUP_TRANSLATION`
  - `SURROGATE_ETL`
  - `REFERENCE_MASTER_FEED`
  - `OUT_OF_SCOPE`

3. `pipeline/run_contract_migration.py`
- Executes migration from source CSVs using the contract as the transformation plan.
- Writes all target tables to `mock_data/target_contract`.
- Emits detailed run report and table-level coverage metrics.
- Applies domain plugins (`PMI`, `ADT`, `OPD`) for high-risk field enrichment.
- Applies strict code crosswalk translation for `LOOKUP_TRANSLATION` fields and writes reject files.

4. `pipeline/run_enterprise_pipeline.py`
- Performs quality gates:
  - source volume and mandatory source presence
  - NHS checksum validity
  - core referential integrity checks
  - unresolved mapping contract warnings

5. `pipeline/run_release_gates.py`
- Enforces cutover thresholds (errors, warnings, unresolved mappings, crosswalk rejects, population ratio, tables written).
- Produces `reports/release_gate_report.json`.

## Design principles for mission-critical migration

1. Contract-first execution:
- Mapping contract is the single execution reference for target field behavior.
- Explicit override policy supports governed closure of unresolved business fields.

2. Reproducibility:
- Deterministic mock generation via explicit seed and row count.

3. Traceability:
- All runs emit machine-readable reports in `reports/`.

4. Safety-oriented defaults:
- Out-of-scope and unresolved fields are explicitly surfaced in issues.
- Surrogate key generation is deterministic and auditable.
- Pre-production imputation mode is explicit and profile-driven (not silent).

## Current known limits

1. `LOOKUP_TRANSLATION` coverage is partial and must be expanded to full approved NHS/PAS code sets.
2. Some archive fields are marked derived and require finalized multi-table synthesis rules.
3. Policy-overridden fields require formal SME sign-off before cutover profile.
4. Cutover-ready release gates remain stricter than pre-production and should remain so.

## Next implementation steps

1. Extend crosswalk coverage beyond baseline sets in `schemas/crosswalks/`.
2. Add table-specific transformation plugins for high-risk tables:
- `LOAD_PMI*`
- `LOAD_ADT_*`
- `LOAD_OPD_*`
- `LOAD_IWL*`
- `LOAD_MH_*`
3. Add reconciliation outputs:
- source-to-target row balance by domain
- mandatory field completion rates
- referential chain completeness percentages
4. Add release gate script that fails deployment when critical thresholds are breached.
