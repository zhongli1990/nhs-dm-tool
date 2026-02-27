# Schema Analysis (Re-run Using Actual Specs)

Date: 2026-02-25  
Scope: `c:\Zhong\Windsurf\data_migration\requirement_spec`

## Specification Inputs

1. `Source PAS - Data Dictionary V83 INQuire DD PC83.xlsx`
2. `Source PAS - PAS_PC60_DataDictionary.docx`
3. `Target PAS - PAS 18.4 Data Migration Technical Guide - FOR REF ONLY NOT TO BE USED.pdf`

## Source Schema Findings

- Extracted from Excel dictionary `Columns` sheet.
- Total source fields: `5,387`
- Total source tables: `417`
- Largest source tables by column count include:
  - `PATDATA` (131 fields)
  - `OPA` (107)
  - `CURRENTPREADMISSIONS` (100)
  - `PREADMISSION` (94)
  - `ADMITDISCH` (69)

Source catalog output:
- `schemas/source_schema_catalog.csv`

## Target Schema Findings

- Extracted from migration technical guide PDF.
- Total target fields (parsed): `880`
- Total target load tables: `38`
- Key target load domains detected:
  - Core: `LOAD_PMI`, `LOAD_ADT_ADMISSIONS`, `LOAD_ADT_EPISODES`, `LOAD_ADT_WARDSTAYS`
  - Scheduling: `LOAD_OPD_APPOINTMENTS`, `LOAD_OPDWAITLIST`, `LOAD_IWL`, `LOAD_IWL_TCIS`
  - Governance/Support: `LOAD_STAFF`, `LOAD_USERS`, `LOAD_SITES`
  - Mental Health/Archive: `LOAD_MH_*`, `LOAD_*_ARCHIVE`

Target catalog output:
- `schemas/target_schema_catalog.csv`

## Parse Quality

- Average target parse confidence is generated into `schemas/schema_catalog_summary.json`.
- PDF text extraction introduces line-join artifacts on some fields (e.g. suffixes merged with comments), so field-level parse confidence is tracked.
- Low-confidence target fields are explicitly added to gap report for follow-up.

## Pipeline Coverage (Current)

Current implementation state (2026-02-25):
1. Source schema extraction for all 417 source tables.
2. Target schema extraction for all 38 `LOAD_` tables.
3. Scalable mock generation for all 38 target tables and expanded source set.
4. Semantic source-to-target mapping analysis across catalogs.
5. Strict mapping contract classification for all target fields.
6. Contract-driven ETL run materializing all 38 target tables.
7. Enterprise quality gate with integrity and unresolved-mapping checks.

Operational status:
- Contract migration run status: `PASS`
- Enterprise quality run status: `PASS` (0 errors, warnings pending mapping governance decisions)
