# Release Notes v0.0.5

Date: 2026-02-26

## Summary

v0.0.5 focuses on runtime stability and operator UX quality for enterprise data migration operations.

## Key updates

1. Mapping workbench stability and scale
- Fixed workbench loading failure caused by corrupted `mapping_workbench.json` trailing content.
- Added JSON recovery/salvage fallback in backend workbench read path.
- Added server-side pagination to workbench API (`offset`, `limit`) for enterprise-safe rendering.
- Upgraded `Edit & Approve` UI with:
  - page size control (default 200)
  - page up/down navigation
  - total/page indicators
  - row `ID` column

2. Contract rows UX uplift
- Added configurable pagination to `Contract Rows` tab (default 200/page).
- Added page up/down navigation and row `ID` column.

3. Dark/Light rendering hardening
- Fixed control and tab visibility in dark mode across key pages.
- Fixed log panel contrast in dark mode.

4. ERD capability and usability
- Added/confirmed relationship cardinality metadata in backend edge payload.
- Improved ERD filtering behavior:
  - token-based table-name matching
  - neighbor expansion for context
- Improved ERD auto-layout:
  - force-distributed placement
  - stronger anti-overlap spacing
  - configurable density (`compact`, `normal`, `sparse`)
- Added `ID` column to ERD relationship list.

5. Lifecycle table UX
- Reordered lifecycle columns for operations visibility:
  - `name | description | status | action | command`

## Runtime verification

- Backend health: `200` on `http://127.0.0.1:3134/health`
- Frontend health: `200` on `http://127.0.0.1:9133`
- Key pages validated after rebuild/restart:
  - `/erd`
  - `/mappings`
  - `/lifecycle`
