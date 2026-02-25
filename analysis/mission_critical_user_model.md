# Mission-Critical User Model and Lifecycle Ownership

Date: 2026-02-25

## Primary user groups

1. DM Engineer
- configures connectors
- runs migration pipelines
- triages rejects and quality issues

2. Data Architect
- governs source-target schema alignment
- approves mapping classes and policy overrides

3. Clinical Informatics Lead
- validates clinical coding and safety-critical transformations
- approves code crosswalk logic for clinical fields

4. DBA / Platform Engineer
- manages data-access security and connector runtime controls
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

## UI support expectations

The control plane should allow each role to:
- view only relevant lifecycle status and evidence
- execute approved actions with audit traces
- export decision artifacts for governance meetings
