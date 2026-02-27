# OpenLI DMM Release Notes v0.2.0

Date: 2026-02-27

## Major SaaS Upgrade

1. Multi-tenant SaaS baseline implemented:
- tenant hierarchy: `organization -> workspace -> project`
- auth flow: login/register/approval
- RBAC baseline roles for super admin, org admin, and org users

2. Enterprise UI uplift:
- compact top-bar context selector (popover)
- new onboarding page: `/onboarding`
- new settings page: `/settings`
- standalone professional login/register pages

3. Mission-critical lifecycle continuity:
- all prior lifecycle pages preserved and verified
- schema, ERD, mappings, quality, connectors, lifecycle, runs, users, admin all load under auth context

4. Reliability hardening:
- strict auth route guards and middleware validation
- CORS preflight handling fixed for authenticated flows
- runtime standardized to frontend `9133`, backend `9134`

## Pending Roadmap Features

1. Fine-grained RBAC matrix by role and action domain.
2. Workspace/project-scoped role assignment policies.
3. SSO federation (OIDC/SAML) for enterprise identity.
4. Secrets vault integration for connector credentials.
5. ODBC/JDBC production hardening (read-only enforcement, query governance, telemetry).
6. Async orchestration engine with run queue, cancellation, retries, and worker scaling.
7. Immutable audit-event stream with evidence pack export.
8. Advanced ERD interaction (pin/drag, minimap, path tracing, lineage overlays).
9. Table-level reconciliation dashboard (counts, null-rate, FK chain completeness, reject-rate).
10. AI-assisted mapping suggestions with explainability and governance controls.
11. Tenant policy packs and licensing/billing hooks.
