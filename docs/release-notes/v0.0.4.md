# Release Notes v0.0.4

Date: 2026-02-26

## Summary

v0.0.4 delivers mission-critical feature uplift and documentation closure across mapping governance, ERD, quality command centre, lifecycle control, and connector evolution.

## Functional changes

1. Mapping workbench and approvals
- Added mapping workbench APIs and persisted workbench model.
- Added status workflow support (`DRAFT`, `IN_REVIEW`, `APPROVED`, `REJECTED`).
- Added frontend editing and transition controls in mappings UI.

2. Connector uplift
- Upgraded ODBC/JDBC from placeholder-only behavior to experimental introspection mode.
- Registry and connector APIs now support metadata and sampling paths with connector options.

3. ERD and relationship graph
- Added ERD APIs with corrected route namespace:
  - `/api/schema-graph/{domain}/relationships`
  - `/api/schema-graph/{domain}/erd`
- Added ERD page in frontend with graph and relationship list.

4. Lifecycle rerun and snapshot controls
- Added rerun-from-step execution API.
- Added snapshot list and restore APIs.
- Added lifecycle UI controls for run-from-step and snapshot operations.

5. Quality command centre uplift
- Added quality KPI config APIs and persisted KPI governance config.
- Added quality KPI widget API with source runtime profile and migration gate KPI streams.
- Added trend seeding API for meaningful rehearsal rendering.
- Upgraded `/quality` page to tabbed operations:
  - Dashboard
  - KPI Widgets
  - Issue Explorer
- Added weeks window selector, auto-refresh selector, manual refresh, and demo trend seed controls.

## Documentation closure

Updated roadmap, design, deployment, API surface, user guide, deliverables summary, lifecycle, due diligence, and release documentation to align with implemented state for this release.

## Runtime

- Backend: `8099`
- Frontend: `3133`
- Services verified running with quality and ERD endpoints returning successful responses.
