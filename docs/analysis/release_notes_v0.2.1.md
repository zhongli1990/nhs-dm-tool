# OpenLI DMM Release Notes v0.2.1

Date: 2026-02-27
Type: Patch release (`+0.0.1` from `0.2.0`)

## Highlights

1. Connectors preview UX fixed and improved:
- resolved blank preview issue caused by column key mismatch
- added on-demand `POST /api/connectors/preview` backend API
- table selection now works from dropdown and clickable table list
- discovered tables now show full list with pagination (default 10/page)

2. Versioning surfaced in UI and settings:
- top bar version badge
- version history table in Settings
- centralized version manifest (`services/version_manifest.json`)

3. Documentation alignment uplift:
- lifecycle/user model updated for SaaS role tiers
- acute Trust operating example added
- product subtitle and vision wording aligned with enterprise EPR migration lifecycle management

## Technical changes

1. Backend:
- FastAPI version bumped to `0.2.1`
- new version metadata API: `GET /api/meta/version`
- connectors preview API added

2. Frontend:
- connectors page rendering and pagination enhancements
- reusable version constant and env-configured version support
- settings page version history render

3. Runtime:
- verified ports unchanged: frontend `9133`, backend `9134`

## Validation summary

1. Frontend build: PASS
2. Backend health/API auth: PASS
3. Protected route smoke checks: PASS
4. Lifecycle execution API smoke checks: PASS

## Known pending roadmap items

1. fine-grained RBAC policy matrix
2. federated SSO (OIDC/SAML)
3. secrets vault + production connector hardening
4. async job orchestration and immutable audit stream
5. advanced ERD interactions and deep lineage tools
