# Runtime Data Layout Decision

## Decision

Keep `mock_data`, `pipeline`, `reports`, and `schemas` at repository root (shared project-level artifacts), not inside `services/backend`.

## Rationale

- `pipeline` is the primary producer/consumer of `mock_data`, `schemas`, and `reports`; it is not frontend code.
- Backend APIs read these artifacts and orchestrate lifecycle steps, so backend should access them via `DM_DATA_ROOT`, not own their location.
- Frontend should consume reports through backend APIs and should not require direct write access to raw migration datasets.
- This structure keeps Docker and non-Docker deployments consistent and avoids duplicating data trees.

## Access Model

- Backend: read/write `reports`, read/write `mock_data` (for generation + contract ETL), read `schemas`.
- Frontend: read-only mounted artifacts in Docker, with user interactions routed via backend APIs.
- Pipeline CLI: direct filesystem access in local/manual runs.

## Streamlined Pattern

Use a single root data contract:

- `DM_DATA_ROOT=<repo-root>`
- All runtime paths resolve from `DM_DATA_ROOT` in backend config.
- Docker mounts project-level named volumes to `/app/<folder>`.
- Manual deployment uses real filesystem paths under project root.
