# Mapping Rework Findings (Comprehensive)

Date: 2026-02-25  
Scope: `c:\Zhong\Windsurf\data_migration`

## Objective

Re-establish a defensible source-to-target migration mapping for PAS V83 -> PAS 18.4 with emphasis on:
- semantic correctness,
- patient safety-oriented data quality controls,
- referential integrity,
- operational reproducibility.

## What was reworked

1. Rebuilt target and source profiling from provided specs and catalogs.
2. Expanded mock generation from minimal baseline to enterprise-scale capability.
3. Rechecked semantic mapping across full source estate (417 tables).
4. Produced strict mapping contract classification for every target field.
5. Added enterprise quality pipeline with auditable issue reports.

## Why 13 source tables existed initially

The 13 tables are the priority transactional set from source schema profiling:
- `PATDATA`, `ADMITDISCH`, `OPA`, `FCEEXT`, `OPREFERRAL`, `WLCURRENT`,
  `WLENTRY`, `WLACTIVITY`, `CPSGREFERRAL`, `SMREPISODE`, `AEA`, `HWSAPP`, `ADTLADDCOR`

They are not the full source universe. Full source has 417 tables.

## Source expansion completed

Mock source generation now includes additional non-13 reference/context tables required for mapping closure, including:
- `CONSWARDSTAY`, `CONSEPISODE`, `CONSEPISDIAG`, `CONSEPISPROC`, `OCCANCEL`
- `LOCATIONCODES`, `LOCN`, `WARD`, `CONSMAST`, `CONSPEC`
- `GP`, `GPHISTORY`, `POSTCODE`, `PSEUDOPCODE`
- `OPREFTKSTATUS`, `OPREFTKSTATUSMF`, `OPBOOKTYPEMF`, `IPBOOKTYPEMF`
- `WLSUSPREASONMF`, `WLREMOVALREASON`
- `CPFTEAMS`, `CPFLOCATION`, `CPFDISCHREASON`, `LEGALSTATUSDETS`, `ALLOCATEDCONTRACT`

## Strict mapping contract

Generated in:
- `reports/mapping_contract.csv`
- `reports/mapping_contract_summary.json`

Classes used:
- `DIRECT_SOURCE`
- `DERIVED`
- `LOOKUP_TRANSLATION`
- `SURROGATE_ETL`
- `REFERENCE_MASTER_FEED`
- `OUT_OF_SCOPE`

Current contract counts:
- `DIRECT_SOURCE`: 219
- `LOOKUP_TRANSLATION`: 201
- `DERIVED`: 148
- `SURROGATE_ETL`: 134
- `REFERENCE_MASTER_FEED`: 104
- `OUT_OF_SCOPE`: 79

Interpretation:
- Large part of remaining non-direct mapping is expected due to code translation, derived archive structures, and ETL key orchestration.
- `OUT_OF_SCOPE` includes parse artefacts and unresolved business decisions that need SME/default policy.

## Data quality and integrity controls introduced

Enterprise pipeline script:
- `pipeline/run_enterprise_pipeline.py`

Checks implemented:
1. Source table presence and minimum row-count checks.
2. NHS Number checksum validation on PATDATA.
3. Source date format checks (DD/MM/YYYY baseline).
4. Source referential check: ADMITDISCH -> PATDATA by MRN.
5. Mapping contract unresolved field detection.
6. Target FK containment checks:
   - PMI -> PMI sub-tables
   - RTT pathways -> periods -> events
   - OPD waitlist -> appointments
   - IWL -> ADT admissions -> ADT episodes -> ward stays

Outputs:
- `reports/enterprise_pipeline_report.json`
- `reports/enterprise_pipeline_issues.csv`

## Tooling to generate any patient volume

Generator supports row-count parameter:
- `python pipeline/generate_all_mock_data.py --rows 20 --seed 42`
- `python pipeline/generate_all_mock_data.py --rows 1000 --seed 42`

This produces deterministic, coherent records with stable key patterns and populated source+target data assets.

## High-risk areas still requiring governance sign-off

1. Fields presently classified `OUT_OF_SCOPE` (non-artefact subset):
   - requires explicit policy: default/derive/lookup/exclude.
2. Code translation catalogs:
   - NHS/PAS code-type mappings must be approved and version-controlled.
3. Archive denormalization rules:
   - requires defined lineage and derivation specs for each archive field.
4. Reference master feeds (`LOAD_STAFF`, `LOAD_USERS`, `LOAD_SITES`):
   - source ownership and refresh controls must be assigned.

## Recommended next execution phase

1. Convert remaining non-artefact `OUT_OF_SCOPE` fields into signed mapping decisions.
2. Implement executable transformation jobs per target domain using mapping contract as source of truth.
3. Add reconciliation reports:
   - row-count, key-presence, null-rate and code-mapping exception reports.
4. Establish release gates:
   - contract freeze, DQ threshold gate, replay test gate, cutover readiness gate.

## New implementation delivered

Contract-driven migration execution has now been implemented:
- `pipeline/run_contract_migration.py`
- `pipeline/enterprise/contract_etl.py`
- `pipeline/enterprise/crosswalks.py`
- `pipeline/enterprise/transform_plugins.py`
- `pipeline/run_release_gates.py`

Outputs:
- `mock_data/target_contract/*.csv`
- `reports/contract_migration_report.json`
- `reports/contract_migration_table_stats.csv`
- `reports/contract_migration_issues.csv`
- `reports/contract_migration_rejects.csv`
- `reports/release_gate_report.json`

This provides an executable ETL baseline aligned with the strict mapping contract and ready for domain-specific hardening.

## Current status after policy uplift

1. Policy overrides applied:
- `pipeline/mapping_resolution_policy.json`
- 25 unresolved business fields moved from unresolved state to governed policy mappings.

2. Pre-production completeness mode:
- `run_contract_migration.py --impute-mode pre_production`
- population ratio increased to 0.6784 in latest lifecycle run.

3. Gate outcomes:
- Enterprise quality: PASS (0 errors, 0 warnings)
- Release gate (pre-production profile): PASS

4. Productization progression:
- Backend API now supports connector selection and lifecycle execution endpoints.
- Frontend control-plane now includes dynamic connector configuration and mission-critical user workflow views.
