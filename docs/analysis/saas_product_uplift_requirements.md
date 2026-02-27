# OpenLI DMM SaaS Uplift Requirements

Date: 2026-02-27
Status: Approved and phase-1 implemented (v0.2.0 baseline)
Product: OpenLI DMM (Data Migration Manager)
Scope: `data_migration` product uplift from single-workspace control plane to multi-tenant NHS enterprise SaaS.

## 1. Business objective

Transform the current mission-critical migration control plane into a sellable SaaS product for major NHS Trusts, supporting multi-organization onboarding, workspace-based scaling, governed lifecycle execution, and tenant-safe operations.

## 2. User tiers and access model

## 2.1 Tier 1: Super Admin

Purpose:
- platform-wide operational control.

Required access:
1. all organizations and all projects.
2. global configuration, tenant provisioning, feature flags, system health, audit views.
3. user lifecycle across all tenants.

## 2.2 Tier 2: Customer Org Admin

Purpose:
- manage a single NHS Trust organization (example: QVH).

Required access:
1. manage own organization users and roles.
2. create/manage own migration projects.
3. configure source/target onboarding and lifecycle settings for own org only.
4. full lifecycle execution and approval workflows within own org.

## 2.3 Tier 3: Customer Org DM Users (profiled roles)

Purpose:
- analysts, engineers, managers in customer organization.

Initial required access (phase 1 RBAC placeholder):
1. full access within own organization tenant scope.
2. no access to other organizations.

Initial profiled roles (same permission set in phase 1, refined later):
1. org_dm_engineer
2. org_data_architect
3. org_dq_lead
4. org_clinical_reviewer
5. org_release_manager

Future refinement:
1. tighten permission boundaries per profiled role.

## 3. Core product requirements

1. Multi-tenant isolation
- strict organization boundary on data and actions.
- org-scoped filtering enforced on all backend APIs and data access.

2. Authentication and session management
- login UI and backend token/session validation.
- persistent user identity and organization context.

3. Authorization (RBAC)
- role-to-permission model with policy enforcement.
- API-level authorization checks (not UI-only).

4. Organization onboarding
- org creation, settings, default policies, connector profiles.
- workspace-level and project-level source/target onboarding per org.

5. Workspace and project model
- tenant hierarchy: `Organization -> Workspaces -> Projects`.
- one organization can own many workspaces.
- one workspace can own one or many projects.
- each project owns schemas, mappings, runs, reports, snapshots.
- lifecycle execution context must include organization, workspace, and project identifiers.

Extensibility statement:
1. this model is suitable for large NHS trusts:
- workspace-level segmentation by division/site/programme/vendor
- project-level delivery isolation under each workspace
- future extension to portfolio/programme objects if required

6. GenAI-assisted mapping and contracts (product requirement)
- AI-assisted mapping suggestions within org project scope.
- review/approve controls before any execution use.

7. Registration and onboarding approval flow
1. add `Register` action on login page.
2. registration creates `PENDING_APPROVAL` account request.
3. super admin and org admin approval workflow for activation.
4. approved users can sign in and access assigned org/workspace scope.

8. Branding uplift
- product brand visible as `OpenLI DMM` in app shell (top bar/sidebar).

## 4. Data model requirements

Minimum entities:
1. users
2. organizations
3. organization_memberships
4. workspaces
5. workspace_memberships (phase 2 optional)
6. projects
7. project_memberships (phase 2 optional)
8. roles
9. permissions
10. registration_requests
11. audit_events
12. sessions/tokens

Core relationships:
1. user can belong to multiple organizations.
2. organization has many workspaces.
3. workspace has many projects.
4. role assignment at organization scope initially; workspace/project scope in phase 2.

## 5. Security and compliance requirements

1. tenant isolation controls:
- deny cross-tenant read/write by default.

2. authentication hardening:
- password policy and optional SSO/OIDC integration path.

3. authorization hardening:
- enforce least privilege and role checks on all state-changing APIs.

4. auditability:
- immutable audit events for login, role changes, approvals, lifecycle executions, connector changes.

5. mission-critical safety:
- release gates and approval checkpoints remain mandatory per project.

## 6. UX requirements

1. login page and authenticated app shell.
2. organization switcher (for users in multiple orgs).
3. workspace switcher within current org.
4. project switcher within current workspace.
4. user management screens (org admin and super admin views).
5. role assignment workflow.
6. register page with request status (`PENDING_APPROVAL`, `APPROVED`, `REJECTED`).
7. preserve current lifecycle pages and controls under org/workspace/project context.

## 7. API requirements (high level)

Required new API families:
1. auth: login, logout, refresh, current user.
2. registration: create request, review request, approve/reject request.
2. organizations: list/create/update, membership management.
3. workspaces: org-scoped workspace management.
4. users: org-scoped user management.
4. RBAC: roles, permissions, assignments.
5. projects: CRUD and context selection.

All existing APIs must become context-aware:
1. schema/mappings/lifecycle/runs/quality/connectors endpoints must enforce org + workspace + project scope.

## 8. Phased delivery plan

Phase 1 (foundation, implemented in v0.2.0):
1. authentication + registration approval flow.
2. super admin/org admin/org profiled-user roles.
3. organization, workspace, and project context model.
3. RBAC placeholders with full access inside own org for customer users.
4. OpenLI DMM branding in UI shell.
5. compact context-switch UX in top bar and dedicated onboarding/settings pages.

Phase 2 (governance depth, pending):
1. fine-grained role matrix for DM user subtypes.
2. workspace and project-level role assignments.
3. expanded audit and policy controls.

Phase 3 (enterprise scale, pending):
1. SSO integration and enterprise identity federation.
2. advanced tenant billing/licensing hooks.
3. policy packs per NHS trust.

## 9. Acceptance criteria for approval

1. clear user-tier boundaries and access semantics are agreed.
2. tenancy model is approved (`org -> workspaces -> projects`).
3. RBAC phase strategy is approved (placeholder then refine).
4. security and audit baseline is accepted for implementation start.
5. current product roadmap/docs point to this approved requirement set.

## 10. Out of scope for this approval doc

1. full UI pixel-level mockups.
2. final DB engine choice and migrations scripts.
3. detailed GenAI model/provider architecture.

These are covered in the technical design document referenced below.

Related design:
- `analysis/saas_multitenancy_rbac_design.md`

