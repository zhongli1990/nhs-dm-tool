# OpenLI DMM Multi-Tenancy, Auth, and RBAC Technical Design 

Date: 2026-02-27
Status: Approved; phase-1 implemented in v0.2.0, phase-2/3 pending
Product: OpenLI DMM

## 1. Design goals

1. Preserve current migration lifecycle capabilities.
2. Add secure multi-tenant SaaS controls for NHS enterprises.
3. Enforce role-based access at API and data layers.
4. Keep implementation incremental with minimal disruption.
5. Scale tenancy for large trusts with explicit workspace segmentation.

## 2. Architecture overview

Current:
- Next.js frontend + FastAPI backend over file artifacts.

Target uplift:
1. Identity and access layer
- login/session/token handling.
- role and permission enforcement middleware.

2. Multi-tenant domain layer
- organization, workspace, and project context attached to requests.

3. Scoped resource layer
- all lifecycle artifacts stored and queried by `org_id` + `workspace_id` + `project_id`.

4. Audit layer
- append-only events for authentication, role changes, run actions, approvals.

## 3. Tenancy model

Chosen model:
- organization as top-level tenant.
- workspace under organization.
- project under workspace.

Context invariants:
1. every request has `actor_user_id`.
2. every project-scoped request has `org_id`, `workspace_id`, and `project_id`.
3. backend validates workspace belongs to organization.
4. backend validates project belongs to workspace.
5. backend validates user membership in organization (and workspace/project when enabled).

Isolation rules:
1. Super Admin bypasses tenant filters.
2. Org roles cannot access other organizations.
3. all existing lifecycle APIs become org/workspace/project-scoped.

Scalability rationale:
1. workspace layer supports segmentation by hospital site, programme, department, or vendor migration stream.
2. projects remain execution units, allowing high-volume parallel delivery in one trust.

## 4. RBAC model

## 4.1 Roles

1. `super_admin`
2. `org_admin`
3. `org_dm_engineer`
4. `org_data_architect`
5. `org_dq_lead`
6. `org_clinical_reviewer`
7. `org_release_manager`

## 4.2 Permission groups

1. platform permissions
- manage organizations
- manage global settings
- view platform audit logs

2. org permissions
- manage org users
- manage org projects
- configure connectors and policies

3. project permissions
- view/edit mappings
- run lifecycle steps
- approve transitions
- view quality/gates/rejects

Phase-1 mapping:
1. super_admin: all permissions.
2. org_admin: all org + project permissions in own org.
3. org DM profiled roles: same broad project permissions in own org/workspaces.

Phase-2 mapping (planned):
1. tighten permissions per DM profile by function and approval authority.

## 5. Authentication design

Initial approach (phase 1):
1. username/email + password login.
2. register flow creates `PENDING_APPROVAL` request.
3. super admin or org admin approves/rejects registration.
4. token-based session (JWT or signed session token).
3. secure cookie or bearer token strategy (configurable).

Enterprise extension path (phase 3):
1. OIDC/SAML federation for NHS enterprise identity providers.

## 6. Data model design

Tables/entities:
1. `users` (`id`, `email`, `display_name`, `status`, `password_hash`, `created_at`)
2. `organizations` (`id`, `name`, `slug`, `status`, `created_at`)
3. `organization_memberships` (`user_id`, `org_id`, `role`, `status`)
4. `workspaces` (`id`, `org_id`, `name`, `slug`, `status`, `created_at`)
5. `workspace_memberships` (`user_id`, `workspace_id`, `role`, `status`)
6. `projects` (`id`, `workspace_id`, `name`, `slug`, `status`, `created_at`)
7. `project_settings` (`project_id`, `connector_config`, `gate_profile`, `options_json`)
8. `registration_requests` (`id`, `email`, `requested_org_id`, `status`, `reviewed_by`, `reviewed_at`)
9. `audit_events` (`id`, `org_id`, `workspace_id`, `project_id`, `actor_user_id`, `action`, `resource`, `payload`, `created_at`)

Artifact storage path model:
- filesystem layout by tenant context:
  - `data/orgs/{org_slug}/workspaces/{workspace_slug}/projects/{project_slug}/...`

Migration compatibility:
1. existing `reports/` and `mock_data/` retained for local single-tenant mode.
2. introduce multi-tenant storage adapter for SaaS mode.

## 7. API design changes

New endpoints (minimum):
1. `POST /api/auth/login`
2. `POST /api/auth/logout`
3. `GET /api/auth/me`
4. `POST /api/auth/register`
5. `GET /api/registration-requests`
6. `POST /api/registration-requests/{request_id}/approve`
7. `POST /api/registration-requests/{request_id}/reject`
8. `GET /api/orgs`
9. `POST /api/orgs`
10. `GET /api/orgs/{org_id}/workspaces`
11. `POST /api/orgs/{org_id}/workspaces`
12. `GET /api/orgs/{org_id}/users`
13. `POST /api/orgs/{org_id}/users`
14. `GET /api/workspaces/{workspace_id}/projects`
15. `POST /api/workspaces/{workspace_id}/projects`

Existing endpoints uplift:
1. require org/workspace/project headers or route params.
2. apply RBAC check before handler logic.
3. apply tenant filter before loading any dataset.

## 8. UI/UX design changes

1. app branding changed to `OpenLI DMM`.
2. add login and register routes and protected app routes.
3. add top-bar user menu with role and org context.
4. add organization switcher, workspace switcher, and project switcher.
5. add admin pages:
- organizations (super admin)
- org users (org admin)
- org workspaces (org admin)
- workspace projects (org admin)
- registration approvals (super admin/org admin)
6. add enterprise onboarding and settings pages:
- `/onboarding` for tenant/project setup workflow
- `/settings` for runtime defaults and connectivity checks

Current pages preserved:
- schemas, erd, mappings, lifecycle, runs, quality, connectors
- now bound to selected organization/workspace/project context.

## 9. Non-functional requirements

1. security
- role checks centralized in middleware/dependencies.
- no sensitive operations without authenticated identity.

2. audit
- all write actions emit audit events.

3. reliability
- context validation rejects orphan requests.

4. performance
- pagination remains mandatory for high-volume tables.

5. backward compatibility
- local developer mode can run with a default bootstrap org/workspace/project.

## 10. Delivery plan and gates

Gate A: Design approval (completed)
1. requirement and architecture docs approved.

Gate B: Foundation implementation (completed in v0.2.0)
1. auth + tenancy models + RBAC middleware + branding.
2. register and approval workflow active.
3. smoke tests for org/workspace/project isolation.

Gate C: Lifecycle integration (completed baseline)
1. all existing operational APIs scoped by org/workspace/project.
2. UI context switchers active.

Gate D: Governance hardening (pending)
1. audit event coverage and admin management features.
2. security review and penetration checks.

## 11. Risks and mitigations

1. Risk: accidental cross-tenant data exposure.
- Mitigation: enforce context filters centrally, add isolation tests.

2. Risk: workspace/project context drift in UI state.
- Mitigation: strict context resolver and invalid-context rejection at API boundary.

3. Risk: breaking existing workflow.
- Mitigation: compatibility mode with default org/workspace/project.

4. Risk: role complexity expansion.
- Mitigation: phase 1 coarse roles, phase 2 fine-grained rollout.

## 12. Explicit assumptions for approval

1. phase 1 may use local credential auth before SSO.
2. org DM profiled roles have broad in-org access initially.
3. GenAI mapping assist uses existing mapping workflow and adds suggestion surfaces first.

Related requirement:
- `analysis/saas_product_uplift_requirements.md`

