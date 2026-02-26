# Enterprise Onboarding and Data Quality Roadmap

Date: 2026-02-26

## Objective

Define the product roadmap for onboarding any NHS PAS/EPR estate (different schemas/vendors) and add a high-clarity data quality experience with KPI cards and trend charts.

## Current implementation status (v0.0.5)

Implemented now:
1. Mapping workbench approval model and bulk workflow controls.
2. ERD visual explorer with inferred relationships and cardinality labels.
3. Quality command centre with KPI widgets, trend controls, and KPI config persistence.
4. Lifecycle rerun-from-step and snapshot restore controls.
5. ODBC/JDBC experimental introspection path.
6. Enterprise-scale pagination patterns in mappings workflows.

In-progress/pending hardening:
1. Full production security controls (RBAC/SSO, secret vault, audit hardening).
2. Rich ERD interaction (zoom/pan/minimap/drag pinning).
3. Production-grade async execution engine for long-running jobs.

## A. Enterprise PAS/EPR onboarding model

## A1. Onboarding phases

1. Program setup
- register migration programme, trust/site scope, source and target systems
- assign role owners (DM engineer, architect, clinical lead, release manager)

2. Connector onboarding
- source connector: CSV/ODBC/JDBC/IRIS profile
- target connector: CSV/ODBC/JDBC/Postgres profile
- run connector health and read-only policy checks

3. Schema introspection
- extract tables, columns, inferred types, key metadata and constraints
- snapshot schema version and hash for traceability
- auto-publish to schema catalog APIs

4. Mapping bootstrap
- generate initial semantic matches
- classify fields into mapping contract classes
- surface unresolved fields and required crosswalk domains

5. Governance workflow
- review/approve mapping contract by role
- enforce clinical sign-off for safety-critical domains
- version and lock approved contract for run candidate

6. Execution rehearsal
- run lifecycle stages with target profile
- inspect quality/gates/rejects
- capture evidence pack and release decision

## A2. Dynamic schema handling requirements

1. Vendor-agnostic metadata model
- source system id, schema name, table name, column name, data type, nullable, default, key hints

2. Introspection adapters
- ODBC metadata extraction (`information_schema`, driver metadata)
- JDBC metadata extraction
- file-based schema inference for CSV/JSON

3. UI dynamic rendering
- no hardcoded table/field lists
- search/filter/paginate large catalogs
- table drill-down with constraints and lineage hints

## A3. Visual schema ERD roadmap

1. ERD explorer page (`/schemas` sub-view or dedicated `/erd`)
- render entity cards for tables
- draw relationships from FK metadata
- support source and target schema views

2. ERD interaction features
- zoom/pan/minimap for large estates
- filter by domain, schema, table prefix, specialty
- click entity to open field metadata and mapping links
- highlight upstream/downstream lineage paths

3. ERD metadata requirements
- table primary keys, foreign keys, unique keys
- optional inferred relationships where explicit constraints are absent
- relationship confidence flags (`declared`, `inferred`)

4. Governance utility
- quickly detect missing FK chains and orphan structures
- improve mapping review and DQ triage by relationship context

## B. Data quality tab roadmap (visual analytics)

## B1. Proposed UI tab

Add a dedicated `/quality` page with three sub-tabs:

1. `Dashboard`
- release gate status and mission-critical KPI cards
- top failing tables bars for fast triage
- operational summary aligned to run outputs

2. `KPI Widgets`
- KPI scorecard table with:
  - KPI name
  - 12-week sparkline
  - this-week value
  - threshold percentage bar
- split views:
  - source runtime profile KPIs
  - migration gate KPIs
- user controls:
  - weeks window selector
  - auto-refresh interval selector
  - manual refresh button
  - demo trend seed button for rehearsal rendering

3. `Issue Explorer`
- filterable issue table by severity, domain, table, field, owner
- direct links to mapping rows and lifecycle steps
- export CSV for governance meetings

## B2. KPI definitions (initial)

1. `DQ_ERROR_COUNT`: total enterprise ERROR issues
2. `DQ_WARN_COUNT`: total enterprise WARN issues
3. `CROSSWALK_REJECTS`: total translation rejects
4. `POPULATION_RATIO`: populated target values / total target values
5. `TABLES_WRITTEN`: number of target tables materialized
6. `FK_COMPLETENESS`: valid child-parent references / expected references
7. `UNRESOLVED_MAPPING`: unresolved required mapping items

## B2.1 Source runtime profile KPIs (operational scorecard)

1. `DUPLICATE_NHS_NUMBERS`
2. `INCOMPLETE_NHS_NUMBERS`
3. `INVALID_NHS_NUMBERS`
4. `INCOMPLETE_POSTCODES`
5. `INVALID_POSTCODES`
6. `INCOMPLETE_CURRENT_GP`
7. `INCOMPLETE_GP_PRACTICE`
8. `INCOMPLETE_DATE_OF_BIRTH`
9. `INCOMPLETE_ETHNIC_CATEGORY`
10. `UNOUTCOMED_APPOINTMENTS_HISTORICAL`
11. `ADDRESS_POSTCODE_LENGTH_BREACH`

## B2.2 KPI research and governance method

1. Define KPI domains:
- patient identity
- demographics
- pathway integrity
- coding quality
- referential integrity
- transformation quality

2. For each KPI define:
- formula and denominator
- source of truth table(s)/field(s)
- threshold by environment (`development`, `pre_production`, `cutover_ready`)
- severity and release gate impact
- accountable owner role

3. Validate with SME panel:
- DM delivery lead
- data quality lead
- PAS analyst
- clinical safety reviewer

4. Operate in quarterly KPI review cycle:
- retire low-value KPIs
- introduce new risk indicators
- recalibrate thresholds after rehearsals/cutovers

## B3. Visual design direction (NHS style)

1. Clean NHS-blue palette with accessible contrast
2. KPI cards for executive summary
3. Sparkline/trend components for run history and KPI widget rows
4. Severity color system:
- pass (green)
- warn (amber)
- fail (red)
5. Dense but readable tables for high-volume issue triage

## C. Mapping edit/approval roadmap

## C1. Contract editor requirements

1. Field-level edit for source field, transform rule, crosswalk id
2. Validation before save (mandatory metadata and syntax checks)
3. Draft/review/approved workflow states
4. Full audit history (who changed what, when, why)

## C2. Approval workflow

1. Architect approval for structural mapping
2. Clinical lead approval for clinical code transformations
3. Release manager approval for production candidate lock

## D. Lifecycle rerun/undo roadmap

## D1. Selective rerun

1. Run one step
2. Run subset from selected step onward
3. Run full lifecycle with profile parameters

## D2. Undo/rollback (planned)

1. Artifact snapshot per run
2. Rollback to prior approved snapshot
3. Optional target-side compensation scripts for reversible staging

## E. Priority implementation plan

1. Phase 1 (near-term)
- `/quality` tab with KPI cards + issue table
- run history endpoint for trend datasets
- pagination for schema/mapping explorers

2. Phase 2
- mapping contract editor + approval states
- role-based permissions for edit/approve/execute actions

3. Phase 3
- full connector introspection for ODBC/JDBC
- snapshot rollback controls and release audit pack generation

## F. Are these normal enterprise DM requirements?

Yes. These are standard expectations for enterprise-grade NHS migration products:

1. dynamic schema onboarding
2. governed mapping authoring/approval
3. staged lifecycle orchestration with reruns
4. quality analytics and trend reporting
5. auditability and release-gate evidence

## G. NHS enterprise feature roadmap (essential + appealing)

## G1. Essential enterprise features (must-have)

1. Dynamic schema onboarding across PAS/EPR vendors
- auto-introspect tables, columns, types, constraints, indexes
- schema versioning and drift detection

2. Governed mapping contract lifecycle
- draft/review/approved states
- field-level edit + validation rules
- full audit trail and change history

3. Controlled execution orchestration
- step-level run, run-all, rerun-from-step
- parameterized profiles (`development`, `pre_production`, `cutover_ready`)
- deterministic run replay with seed/version lock

4. Data quality and safety controls
- KPI dashboard (errors, warnings, rejects, completeness, FK integrity)
- reject queues with triage workflow
- mandatory clinical-domain checks

5. Release and cutover governance
- gate-based promotion controls
- signed evidence pack export
- cutover rehearsal runbooks and rollback checkpoints

6. Security and compliance baseline
- RBAC/ABAC permissions
- SSO integration (NHS identity patterns)
- encryption, secrets vault, immutable audit logs

7. Visual schema ERD and lineage
- interactive ERD for source and target catalogs
- PK/FK and inferred relationship overlays
- relationship-driven drill-down for mapping and quality triage

## G2. Highly appealing differentiators (customer value)

1. Visual data quality command center
- trend graphs, anomaly alerts, domain heatmaps
- trust/site/specialty-level drill-down

2. Intelligent mapping accelerator
- AI-assisted mapping suggestions with confidence and explainability
- policy-aware recommendations for crosswalks

3. Clinical safety workspace
- specialty-specific rule packs (RTT, ADT, OPD, MH/CPA)
- impact previews before approval

4. Multi-programme portfolio view
- compare migration readiness across trusts/vendors
- benchmark KPIs and risk scores

5. Connector marketplace model
- reusable certified adapters (PAS, EPR, LIS, RIS, data warehouse)
- connector health SLA monitoring

## G3. Prioritized release plan

1. v0.1 foundation
- dynamic onboarding, governed mapping editor, run orchestration, DQ KPIs, base ERD viewer

2. v0.2 governance
- approvals, RBAC, evidence packs, cutover rehearsal and rollback snapshots, ERD lineage overlays

3. v0.3 optimization
- AI mapping assist, advanced DQ analytics, portfolio-level control plane
