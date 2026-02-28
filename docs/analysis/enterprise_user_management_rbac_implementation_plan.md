# Enterprise User Management and RBAC Implementation Plan

Date: 2026-02-28
Status: Active plan (Phase 1 and selected Phase 2 controls delivered in v0.2.5)
Product: OpenLI DMM (NHS PAS Migration Control Plane)

## 1. Objective

Implement enterprise-grade user management and RBAC in controlled phases, preserving current production behavior while adding complete admin capabilities.

## 2. Delivery Strategy

1. Use additive schema/API changes first.
2. Keep existing login/register flow operational throughout.
3. Gate each phase with API and UI acceptance tests.
4. Release behind configuration flags where appropriate.

## 3. Workstreams

1. Data model and migrations
2. Backend API and authorization services
3. Frontend admin UX
4. Audit and observability
5. Security hardening
6. Documentation and release readiness

## 4. Phased Plan

## Phase 1: User Directory and Membership Operations

Goal: enable super admin and org admin to manage users beyond approval queue.

Backend tasks:
1. Add `GET /api/admin/users` with filters: `org_id`, `status`, `role`, `q`, `page`, `page_size`.
2. Add `PATCH /api/admin/users/{user_id}/status` (`ACTIVE`, `SUSPENDED`, `DISABLED`).
3. Add `PATCH /api/admin/users/{user_id}/memberships/{org_id}/role`.
4. Add `POST /api/admin/users/{user_id}/memberships` and delete membership endpoint.
5. Add authorization guards:
- super admin: global
- org admin: org-scoped only

Frontend tasks:
1. Replace static `/users` page with live user management table.
2. Add user filters, paging, and row detail drawer.
3. Add role/status edit actions with confirmation dialogs.
4. Keep registration approval actions in Admin view and cross-link to users.

Data tasks:
1. Ensure query indexes exist for user/email/status and membership role/org.
2. Add migration for any missing indexes and status constraints.

Acceptance criteria:
1. Approved users appear in user directory immediately.
2. Super admin can view all orgs/users.
3. Org admin cannot mutate other orgs.
4. Role and status updates persist and are enforced by permission checks.
5. Status: Delivered in v0.2.5 baseline.

## Phase 2: Role Catalog and Permission Matrix

Goal: convert RBAC from seed-only to managed role lifecycle.

Backend tasks:
1. Introduce role metadata table (`role_definitions`) with system/custom flag and status.
2. Implement role CRUD endpoints with protected-system-role rules.
3. Implement permission matrix read/update endpoint.
4. Add role assignment conflict checks and validation.

Frontend tasks:
1. Add `Roles & Permissions` admin tab.
2. Build permission matrix editor with clear grouping.
3. Add create/clone/deprecate role workflows.
4. Add usage view: where a role is assigned.

Acceptance criteria:
1. Super admin can create and assign custom org role.
2. System roles cannot be deleted.
3. Role updates take effect on next token refresh or re-auth.
4. Status: Core role catalog + permission matrix delivered in v0.2.5, advanced governance controls pending.

## Phase 3: SSO Federation Foundation (OIDC First)

Goal: integrate enterprise SSO while preserving local fallback.

Backend tasks:
1. Add `identity_providers` and `user_identities` tables.
2. Implement OIDC login initiation and callback endpoints.
3. Implement user-linking and JIT provisioning policy.
4. Add optional group/claim to role mapping resolver.

Frontend tasks:
1. Add SSO buttons on login page when provider enabled.
2. Add admin SSO configuration view (issuer/client metadata/status).

Security tasks:
1. Validate issuer, audience, nonce, signature.
2. Add secure secret storage strategy for client secrets.
3. Enforce replay protections and callback state checks.

Acceptance criteria:
1. User can sign in through configured OIDC provider.
2. User is mapped to correct internal org/role context.
3. Local super admin login still works when SSO is unavailable.

## Phase 4: Governance Hardening and Operational Controls

Goal: enterprise-grade governance for long-lived operations.

Tasks:
1. Session revocation and forced sign-out.
2. Optional break-glass workflow with expiry.
3. Segregation-of-duties validation rules.
4. Admin action reason codes for sensitive operations.
5. Advanced audit filtering and export.

Acceptance criteria:
1. All privileged mutations are fully auditable with before/after values.
2. Security incident playbook supports immediate access shutdown.

## 5. Proposed Schema Changes

Phase 1 additions:
1. optional additional indexes and status constraints.
2. optional `last_login_at_utc` in `users`.

Phase 2 additions:
1. `role_definitions` table.
2. expanded `role_permissions` with foreign key to role definitions.

Phase 3 additions:
1. `identity_providers` table.
2. `user_identities` table.
3. optional `group_role_mappings` table.

## 6. API Security Controls

1. Centralized permission checks in dependency layer.
2. Tenant-aware query filters mandatory for org-admin scope.
3. Write operations must require CSRF-safe and token-safe flow as applicable.
4. Sensitive endpoints require explicit audit emission.

## 7. UI/UX Quality Controls

1. Fix cell overflow with constrained widths, truncation, and expandable detail views.
2. Add empty/loading/error states for all admin tables.
3. Add optimistic updates only where rollback behavior is explicit.
4. Keep all destructive actions behind confirmation.

## 8. Testing Plan

Unit tests:
1. permission resolver and role inheritance behavior
2. tenant scoping guards
3. role update validation and protected role rules

Integration/API tests:
1. user listing and mutation endpoints per actor role
2. registration approval to user directory propagation
3. role assignment and enforcement on protected APIs

UI E2E tests:
1. super admin user management flows
2. org admin scoped management flows
3. role matrix edit and save

Regression tests:
1. login/register/approval paths remain stable
2. migration lifecycle pages unaffected by RBAC uplift

## 9. Rollout Plan

1. Release Phase 1 in a minor version with feature-complete admin user management.
2. Run smoke + regression in Docker and manual Windows deployment modes.
3. Enable Phase 2 role catalog in staging first.
4. Introduce SSO in pilot org before broad rollout.

## 10. Risks and Mitigations

1. Risk: permission regression blocks valid operations.
- Mitigation: endpoint-level permission tests + canary rollout.

2. Risk: cross-org leakage from query mistakes.
- Mitigation: centralized scoped query helpers + security tests.

3. Risk: role sprawl and governance drift.
- Mitigation: role templates, deprecation policy, approval controls.

4. Risk: SSO misconfiguration lockout.
- Mitigation: retain local super-admin break-glass path.

## 11. Definition of Done (Overall)

1. Enterprise admin can fully manage users, memberships, and roles through UI.
2. Authorization model is enforced consistently in backend.
3. Audit trail is complete for identity and access changes.
4. Documentation and runbooks are updated for Docker and non-Docker deployment paths.

## 12. Immediate Next Execution Slice

Recommended next coding slice after approval:
1. Deliver SSO foundation tables and OIDC provider management endpoints.
2. Implement IdP-to-role mapping policy and JIT provisioning controls.
3. Add SoD policy checks for high-risk role assignment flows.
