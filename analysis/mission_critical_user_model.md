# Mission-Critical User Model and Lifecycle Ownership

Date: 2026-02-26

## Product vision context

The control plane supports dual operation modes:
1. UI-driven lifecycle execution for operational users.
2. CLI/API-driven execution for engineering teams.

Both modes must produce the same governed artifacts and gate decisions.

## Primary user groups

1. DM Engineer
- configures connectors
- runs migration pipelines
- triages rejects and quality issues

2. Data Architect
- governs source-target schema alignment
- reviews and approves mapping contract logic

3. Clinical Informatics Lead
- validates clinical coding and safety-critical transformations
- approves high-risk crosswalk and rule behavior

4. DBA / Platform Engineer
- manages connector/runtime controls and read-only access posture
- validates DB performance and operational reliability

5. Programme / Release Manager
- operates gate-based progression decisions
- drives pre-production and cutover governance

## Lifecycle task ownership

1. Schema extraction and profiling
- Owner: Data Architect
- Operator: DM Engineer

2. Connector configuration and source/target accessibility
- Owner: DBA / Platform Engineer
- Operator: DM Engineer

3. Mapping contract generation and closure
- Owner: Data Architect
- Co-owner: Clinical Informatics Lead

4. Pipeline execution and DQ checks
- Owner: DM Engineer
- Oversight: Clinical Informatics Lead

5. Release-gate and cutover decisions
- Owner: Programme / Release Manager
- Inputs: Architect, Clinical Lead, DBA

## UI support expectations by role

1. Mapping Analyst / Architect
- high-volume mapping review with pagination and bulk actions
- status transitions (`DRAFT`, `IN_REVIEW`, `APPROVED`, `REJECTED`)

2. DM Engineer
- run lifecycle steps, rerun-from-step, restore snapshots
- inspect contract and enterprise issues quickly

3. DQ and Clinical roles
- use quality dashboard/KPI widgets/issue explorer for sign-off evidence
- use ERD context to validate relationship integrity assumptions

4. Release Manager
- evaluate run outcomes and release profile gate results
- approve promotion only when evidence pack is complete

## Governance expectations

The control plane should allow each role to:
1. view relevant lifecycle status and evidence.
2. execute approved actions with audit traces.
3. export decision artifacts for governance boards.
4. operate consistently across UI, API, and CLI channels.
