# Enterprise User Management and RBAC Design (v0.2.5 Baseline)

Date: 2026-02-28
Status: Approved baseline with Phase 1 and Phase 2 core controls implemented
Product: OpenLI DMM (NHS PAS Data Migration)
Scope: Identity, user management, authorization, and admin UX for enterprise multi-tenant control plane

## 1. Purpose

Define a production-grade user management and authorization design for mission-critical NHS migration programs, starting from the current v0.2.5 implementation and closing remaining enterprise gaps.

## 2. Design Principles

1. Authentication and authorization are separated.
2. Tenant isolation is enforced at API and data access layers.
3. Authorization remains platform-controlled even when SSO is enabled.
4. All identity and access changes are auditable.
5. Operational safety is preferred over convenience for privileged actions.

## 3. Current State (Implemented in v0.2.5)

## 3.1 Identity and tenancy baseline

1. PostgreSQL-backed users, organizations, memberships, registration requests, and role-permission mapping are in place.
2. Tenant hierarchy exists: `organization -> workspace -> project`.
3. Login and self-registration with approval workflow are implemented.
4. JWT/bearer token flow with permission checks is implemented at API layer.
5. Runtime state and audit events are persisted in PostgreSQL.

## 3.2 Current role and permission baseline

Roles (seeded):
1. `super_admin`
2. `org_admin`
3. `org_dm_engineer`
4. `org_data_architect`
5. `org_dq_lead`
6. `org_clinical_reviewer`
7. `org_release_manager`

Permissions (baseline examples):
1. `org.manage`
2. `workspace.manage`
3. `project.manage`
4. `project.design`
5. `project.execute`
6. `project.quality`
7. `registration.review`

## 3.3 Current functional gap

1. Admin UI does not provide a full user directory and user lifecycle actions.
2. Roles page is static and does not support role CRUD or permission matrix management.
3. APIs for full user lifecycle operations are incomplete (status changes, role reassignment, membership management).
4. Role governance and separation-of-duties controls are not yet modeled.
5. SSO federation is not yet implemented.

## 4. Target Enterprise Authorization Model

## 4.1 Core model

1. Tenant/resource hierarchy:
- `Organization` (tenant boundary)
- `Workspace` (program/site/domain partition)
- `Project` (delivery execution unit)
- `Resource` (mappings, runs, connectors, quality, settings, audit)

2. Identity and access entities:
- `User`
- `OrganizationMembership` (user-to-org relation)
- `RoleDefinition`
- `PermissionDefinition`
- `RolePermission`
- `UserRoleAssignment` (via membership role)

3. Authorization evaluation:
- Check actor identity.
- Resolve tenant context.
- Resolve effective permissions from assigned role(s).
- Apply resource-scope guard and policy constraints.

## 4.2 Permission model shape

Permission naming convention:
- `<resource>.<action>`
- Examples: `users.read`, `users.update`, `roles.assign`, `audit.read`, `project.execute`

Permission scope:
1. platform scope (super admin only)
2. org scope
3. workspace/project scope (future extension)

## 4.3 Recommended role architecture

1. Keep existing business roles for migration operations.
2. Introduce governance roles if required:
- `org_security_admin`
- `org_auditor`
- `org_support_operator`
3. Protect built-in system roles from deletion.
4. Allow custom org roles for customer-specific governance, but under policy constraints.

## 4.4 Role lifecycle controls

1. Role creation/edit/deprecate is auditable.
2. No direct deletion of in-use roles; deprecate first.
3. Role updates require conflict checks against SoD policy.
4. Critical role assignment (for example `org_admin`) requires elevated approval option (phase 2+).

## 5. Enterprise User Management Model

## 5.1 User lifecycle states

Recommended state model:
1. `PENDING_APPROVAL`
2. `ACTIVE`
3. `SUSPENDED`
4. `LOCKED`
5. `DISABLED`

## 5.2 User lifecycle operations

Super admin / org admin capabilities:
1. list users with filters (org, role, status, last activity)
2. approve/reject registration
3. activate/suspend/disable user
4. change user role
5. move user between orgs (or add multi-org membership)
6. force sign-out/session revoke
7. password reset initiation (local-auth mode)

## 5.3 Organization membership model

1. User can have membership in one or more orgs.
2. One primary role per membership in phase 1.
3. Optional multi-role per org in phase 2 with precedence rules.
4. Membership status must be explicit and auditable.

## 6. Admin UI Design Requirements

## 6.1 Admin Console structure

Tabs in `/admin`:
1. `Users`
2. `Registration Requests`
3. `Roles & Permissions`
4. `Organizations`
5. `Workspaces/Projects`
6. `Audit`

## 6.2 Users tab required capabilities

1. paged table with search and filters
2. columns: user, email, org(s), role, status, created, last login
3. row actions: view profile, change role, suspend/activate, remove membership
4. bulk actions for high-volume admin tasks

## 6.3 Roles tab required capabilities

1. role list with type (`system` or `custom`) and status
2. role detail panel with permission matrix
3. create role from template or clone existing role
4. edit role permissions with validation before save
5. assign role to user membership
6. prevent UI overflow and cell clipping issues through fixed layout + truncation + detail drawer

## 7. SSO and Enterprise Identity Compatibility

This model supports Google, AD, Azure AD (Entra), and other enterprise IdPs by design.

## 7.1 Integration pattern

1. IdP handles authentication (OIDC/SAML).
2. OpenLI DMM handles authorization (RBAC).
3. IdP identity is mapped to internal user and org membership records.

## 7.2 Additional schema for federation

1. `identity_providers`
- provider name, issuer, protocol, client metadata, org binding rules
2. `user_identities`
- `user_id`, `provider_id`, `subject`, `email`, sync metadata
3. optional `group_role_mappings`
- provider group/claim -> internal role assignment rules

## 7.3 Provisioning model

1. JIT provisioning for first login with policy checks.
2. SCIM provisioning/deprovisioning for managed enterprise rollout.
3. Break-glass local super admin account retained for recovery.

## 8. API Requirements (Target)

User management:
1. `GET /api/admin/users`
2. `PATCH /api/admin/users/{user_id}/status`
3. `PATCH /api/admin/users/{user_id}/memberships/{org_id}/role`
4. `POST /api/admin/users/{user_id}/memberships`
5. `DELETE /api/admin/users/{user_id}/memberships/{org_id}`

Role management:
1. `GET /api/admin/roles`
2. `POST /api/admin/roles`
3. `PATCH /api/admin/roles/{role}`
4. `DELETE /api/admin/roles/{role}` (deprecate/protected semantics)
5. `GET /api/admin/roles/{role}/permissions`
6. `PUT /api/admin/roles/{role}/permissions`

SSO management (future phase):
1. `GET/POST /api/admin/identity-providers`
2. `POST /api/auth/sso/{provider}/callback`
3. `GET /api/admin/group-role-mappings`

## 9. Security and Compliance Requirements

1. Immutable audit events for all identity and RBAC mutations.
2. No cross-org queries for org-scoped admins.
3. Least privilege defaults for all new roles.
4. Secret handling and key rotation for SSO/OIDC client secrets.
5. Session revocation support for high-risk incidents.

## 10. Non-Functional Requirements

1. Pagination on all admin list APIs.
2. Optimized indexes for user/role/membership lookup.
3. Deterministic authorization decisions with explicit deny responses.
4. Backward-compatible local-auth mode for non-SSO deployments.

## 11. Acceptance Criteria

1. Super admin can list all users across orgs and edit role/status safely.
2. Org admin can manage only in-org users.
3. Role and permission changes are persisted and reflected immediately in auth checks.
4. Every identity and RBAC change produces an audit event with actor and before/after state.
5. UI tables remain readable under long values and high row counts.

## 12. Out-of-Scope for Immediate Phase

1. full ABAC policy engine
2. delegated admin approval workflows for every role change
3. advanced IAM analytics and anomaly detection

## 13. Implementation Progress (v0.2.5)

Implemented:
1. Registration approval workflow and user directory integration.
2. User lifecycle actions (activate, suspend, disable, lockout controls).
3. Role catalog and permission matrix management baseline.
4. Audit events for identity/RBAC mutations.
5. Admin and Users pages aligned to enterprise operational workflows.

Pending:
1. Full SSO federation implementation (OIDC/SAML callbacks and provider governance).
2. Segregation-of-duties policy automation for sensitive role changes.
3. SCIM-based provisioning/deprovisioning.

## 14. References

1. `docs/analysis/saas_multitenancy_rbac_design.md`
2. `docs/analysis/saas_product_uplift_requirements.md`
3. `docs/analysis/enterprise_user_guide.md`
