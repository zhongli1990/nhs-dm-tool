# Release Notes v0.0.2

Date: 2026-02-26

## Summary

v0.0.2 upgrades the product from report-viewing UI to a lifecycle-operational control plane with dynamic, API-driven workflow execution.

## Major Changes

1. Lifecycle orchestration APIs in backend:
   - `GET /api/lifecycle/steps`
   - `POST /api/lifecycle/steps/{step_id}/execute`
   - `POST /api/lifecycle/execute-from/{step_id}`
   - `GET /api/lifecycle/snapshots`
   - `POST /api/lifecycle/snapshots/{snapshot_id}/restore`
2. New lifecycle UI console:
   - run all stages in order
   - run individual stages
   - parameter controls (`rows`, `seed`, `min_patients`, `release_profile`)
   - execution log tails and per-step status
3. UI/UX uplift for mission-critical operations:
   - sidebar navigation by workflow domain
   - tabbed operational views for heavy data tasks
   - reusable table/tabs components for large datasets
4. Dynamic rendering enhancements:
   - schema explorer with table filtering and field drill-down
   - ERD relationship explorer (`/erd`)
   - mapping explorer with filtered contract queries
   - runs console with gate/reject tabs and parameterized execution
   - connector console with discovery and preview drill-down
   - quality command centre with tabbed KPI widget views
5. Mission-critical feature uplift (1-5):
   - mapping workbench and approval states
   - ODBC/JDBC experimental introspection path
   - ERD and relationship APIs
   - quality trends and KPI governance config
   - selective rerun and snapshot restore
6. Documentation refresh:
   - lifecycle, deployment and user guides updated for UI-first execution model
   - requirement markdowns updated with implementation alignment notes

## Operational Notes

1. Full stack runtime remains:
   - backend: `8099`
   - frontend: `3133`
2. UI and CLI are synchronized by shared backend pipeline commands and shared report artifacts.
3. Includes refreshed mock/report artifacts from latest lifecycle runs.
4. Quality APIs now include:
   - `/api/quality/trends`
   - `/api/quality/trends/seed`
   - `/api/quality/kpis`
   - `/api/quality/kpi-widgets`
