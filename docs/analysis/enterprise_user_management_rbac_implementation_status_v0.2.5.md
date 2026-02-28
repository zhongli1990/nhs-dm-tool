# Enterprise User Management and RBAC Implementation Status (v0.2.5)

Date: 2026-02-28
Status: In production baseline for local auth deployments
Product: OpenLI DMM (NHS PAS Migration Control Plane)

## 1. Scope

This status record captures delivered capabilities for enterprise user management and RBAC as of release `0.2.5`.

## 2. Delivered in v0.2.5

1. User lifecycle
- approval-based registration workflow
- user directory visibility in admin/user operations
- account status controls (active, suspended, disabled/locked flows)
- session reset controls for administrative recovery

2. RBAC model operations
- role catalog surfaced in UI
- permission matrix display/edit baseline
- role assignment updates via admin flows
- org-scoped and platform-scoped access checks in backend APIs

3. Audit and governance
- immutable audit records for identity and RBAC mutations
- audit exploration and CSV export path for governance evidence

4. Data persistence
- PostgreSQL-backed user, membership, role, and runtime state
- migration-managed schema evolution via Alembic

5. Documentation surface
- `/documents` page for lifecycle/deployment/design markdown browsing
- RBAC-aligned upload/download controls and auditable operations

## 3. Remaining gaps

1. Enterprise federation
- OIDC/SAML provider lifecycle management
- claim/group to role mapping policy
- SCIM provisioning/deprovisioning

2. Governance hardening
- explicit segregation-of-duties policy engine
- privileged role assignment two-person approval workflow
- richer policy simulation and impact analysis

3. Operations at scale
- asynchronous admin workflows for very large tenancy estates
- expanded alerting and SIEM integration for security events

## 4. Verification checklist (v0.2.5)

1. Login/register/approval flow validated in Docker runtime.
2. User and role management actions persist in PostgreSQL.
3. `/api/meta/version` returns manifest-backed `0.2.5`.
4. Login page, register page, and top bar display `0.2.5`.
5. Core lifecycle pages (schemas, mappings, lifecycle, quality, runs) remain operational.

## 5. Next target slice

1. Phase 3 SSO foundation (OIDC-first with local break-glass fallback).
2. SoD policy checks for critical role assignments.
3. Admin-level identity provider governance UX and runbook.
