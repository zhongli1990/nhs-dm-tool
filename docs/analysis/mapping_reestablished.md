# Re-established Source-to-Target Mapping (Semantic Re-check)

Date: 2026-02-25
Scope: `c:\Zhong\Windsurf\data_migration`

## Direct answer: why only 13 source tables were generated

The 13 source tables were not intended to represent the full source estate.
They are the **priority transactional extract set** identified in `source_schema_profile.md` for core migration flows.

- Full source schema: 417 tables / 5,387 fields
- Priority transactional tables: 13
- Target load tables: 38

So, no, the other source tables are not automatically "irrelevant". Many are lookup/reference/configuration/history tables that may still be required to fully satisfy coded fields, reference entities, and archive denormalisation.

## What was re-checked

1. Full field-level semantic matching was run between:
   - source catalog (`schemas/source_schema_catalog.csv`)
   - target fields actually generated in `mock_data/target/*.csv`
2. Mapping confidence and gap categories were separated into:
   - Mapped business fields
   - Surrogate/technical fields
   - Reference/master-data fields
   - PDF parse artefacts
   - Unmapped business fields requiring explicit mapping decisions

Outputs:
- `reports/semantic_mapping_matrix.csv`
- `reports/semantic_mapping_summary.json`
- `reports/mapping_gap_recheck.json`

## Re-established mapping intent by domain

- `LOAD_PMI*` family:
  - Primary sources: `PATDATA`, `ADTLADDCOR`
  - Needs additional lookup/code tables for full code-type fidelity (nationality, language, religion, etc.)
- RTT/Referral:
  - Primary sources: `OPREFERRAL`, `WLCURRENT`, `WLENTRY`, `WLACTIVITY`
- OPD:
  - Primary sources: `OPA`, `OPREFERRAL`, plus WL linkage tables
- Community:
  - Primary sources: `CPSGREFERRAL`, `HWSAPP`
- IWL:
  - Primary sources: `WLCURRENT`, `WLENTRY`, `WLACTIVITY`
- ADT:
  - Primary sources: `ADMITDISCH`, `FCEEXT`, plus WL chain fields
- Mental Health:
  - Primary sources: `SMREPISODE` (+ community context where applicable)
- Archives:
  - Primarily denormalised composites from multiple transactional + lookup/reference sources; not expected from a single source table

## What looks genuinely missing vs not missing

### Not missing (expected by design)

- Surrogate chain fields such as `record_number`, `load*_record_number`, `*_recno_*`
  - These are ETL-generated keys, not source columns.
- Reference tables (`LOAD_STAFF`, `LOAD_USERS`, `LOAD_SITES`, parts of `LOAD_IWL_PROFILES`)
  - These are setup/master data feeds, often outside patient transaction extracts.
- PDF artefact fields (`must`, `indicates`, `ged`, `ge_date`, etc.)
  - Not real business target fields; should be removed from contractual schema.

### Potentially missing business mappings (need explicit decisions)

High-impact unresolved areas still include:
- Rich PMI enrichment fields in `LOAD_PMI`:
  - `where_heard_of_service`, `extra_info_1..10`, some death/cause fields, contact permission flags
- Archive denormalised fields in:
  - `LOAD_ADT_ARCHIVE`, `LOAD_OPD_ARCHIVE`, `LOAD_DETENTION_ARCHIVE`, `LOAD_CPA_ARCHIVE`
- Certain OPD/IWL workflow attributes:
  - e.g. `walkin_flag`, `appointment_priority/purpose`, some deferral outcome/comment fields

These are not necessarily absent in source estate; many likely require joining non-priority source tables or reference datasets rather than direct 1:1 field copy.

## Current recommendation

1. Keep the 13 priority source tables for baseline transactional coverage.
2. Add a second extraction layer for:
   - code/lookup tables required for PAS code-type mapping
   - staff/site/reference masters
   - archive denormalisation support tables
3. Freeze a formal mapping contract with per-field mapping type:
   - `DIRECT_SOURCE`
   - `DERIVED`
   - `LOOKUP_TRANSLATION`
   - `SURROGATE_ETL`
   - `REFERENCE_MASTER_FEED`
   - `OUT_OF_SCOPE`
