"use client";

import { useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPatchJson, apiPostJson, apiPutJson, buildApiUrl, getTokenFromBrowser } from "../../lib/api";

type Me = { sub: string; role: string; org_id?: string };
type OrgRow = { id: string; name: string; slug: string };
type RoleRow = { role: string; permission_count: number; permissions: string[] };
type Membership = { org_id: string; org_name: string; role: string; status: string };
type RegistrationRow = {
  id: string;
  username: string;
  email: string;
  requested_org_id: string;
  created_at_utc: string;
};
type UserRow = {
  id: string;
  username: string;
  email: string;
  display_name: string;
  status: string;
  is_super_admin: boolean;
  last_login_at_utc?: string;
  failed_login_count?: number;
  locked_until_utc?: string;
  session_revoked_at_utc?: string;
  created_at_utc: string;
  memberships: Membership[];
};

type AuditRow = {
  id: number;
  created_at_utc: string;
  event_type: string;
  outcome: string;
  actor_user_id: string;
  actor_role: string;
  actor_org_id: string;
  target_type: string;
  target_id: string;
  details: Record<string, unknown>;
};

const PAGE_SIZE = 20;
const SYSTEM_ROLES = new Set([
  "super_admin",
  "org_admin",
  "org_dm_engineer",
  "org_data_architect",
  "org_dq_lead",
  "org_clinical_reviewer",
  "org_release_manager",
]);

export default function UsersPage() {
  const [me, setMe] = useState<Me | null>(null);
  const [orgs, setOrgs] = useState<OrgRow[]>([]);
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [pendingRequests, setPendingRequests] = useState<RegistrationRow[]>([]);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [rowCount, setRowCount] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const [orgId, setOrgId] = useState("");
  const [status, setStatus] = useState("");
  const [role, setRole] = useState("");
  const [query, setQuery] = useState("");

  const [statusDraft, setStatusDraft] = useState<Record<string, string>>({});
  const [roleDraft, setRoleDraft] = useState<Record<string, string>>({});
  const [addOrgDraft, setAddOrgDraft] = useState<Record<string, string>>({});
  const [addRoleDraft, setAddRoleDraft] = useState<Record<string, string>>({});
  const [approveRoleDraft, setApproveRoleDraft] = useState<Record<string, string>>({});

  const [newRoleName, setNewRoleName] = useState("");
  const [newRolePermissions, setNewRolePermissions] = useState("");
  const [rolePermDraft, setRolePermDraft] = useState<Record<string, string>>({});
  const [auditRows, setAuditRows] = useState<AuditRow[]>([]);
  const [auditEventType, setAuditEventType] = useState("");
  const [auditOutcome, setAuditOutcome] = useState("");
  const [auditTargetType, setAuditTargetType] = useState("");
  const [auditActorUserId, setAuditActorUserId] = useState("");

  const isSuperAdmin = me?.role === "super_admin";
  const roleOptions = useMemo(() => roles.map((r) => r.role), [roles]);

  function parsePermissionText(raw: string): string[] {
    return Array.from(
      new Set(
        raw
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean)
      )
    );
  }

  async function loadLookups() {
    const [mePayload, orgPayload] = await Promise.all([
      apiGet<{ user: Me }>("/api/auth/me"),
      apiGet<{ rows: OrgRow[] }>("/api/orgs"),
    ]);
    setMe(mePayload.user);
    setOrgs(orgPayload.rows || []);
    setOrgId(mePayload.user?.role === "super_admin" ? "" : mePayload.user?.org_id || "");
  }

  async function loadRoles() {
    const rolePayload = await apiGet<{ rows: RoleRow[] }>("/api/admin/roles");
    setRoles(rolePayload.rows || []);
  }

  async function loadPendingRequests() {
    const payload = await apiGet<{ rows: RegistrationRow[] }>("/api/registration-requests?status=PENDING_APPROVAL");
    setPendingRequests(payload.rows || []);
  }

  async function loadUsers(nextOffset = offset) {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (orgId) params.set("org_id", orgId);
      if (status) params.set("status", status);
      if (role) params.set("role", role);
      if (query.trim()) params.set("q", query.trim());
      params.set("offset", String(nextOffset));
      params.set("limit", String(PAGE_SIZE));

      const payload = await apiGet<{ row_count: number; rows: UserRow[] }>(`/api/admin/users?${params.toString()}`);
      setUsers(payload.rows || []);
      setRowCount(payload.row_count || 0);
      setOffset(nextOffset);
    } finally {
      setLoading(false);
    }
  }

  async function refreshAll(nextOffset = offset) {
    await Promise.all([loadRoles(), loadPendingRequests(), loadUsers(nextOffset), loadAuditRows()]);
  }

  async function loadAuditRows() {
    const params = new URLSearchParams();
    params.set("limit", "100");
    if (auditEventType.trim()) params.set("event_type", auditEventType.trim());
    if (auditOutcome.trim()) params.set("outcome", auditOutcome.trim());
    if (auditTargetType.trim()) params.set("target_type", auditTargetType.trim());
    if (auditActorUserId.trim()) params.set("actor_user_id", auditActorUserId.trim());
    const payload = await apiGet<{ rows: AuditRow[] }>(`/api/audit/events?${params.toString()}`);
    setAuditRows(payload.rows || []);
  }

  useEffect(() => {
    loadLookups()
      .then(() => refreshAll(0))
      .catch((ex) => setMessage(ex.message || "Failed to load user management data."));
  }, []);

  async function applyStatus(user: UserRow) {
    const nextStatus = statusDraft[user.id] || user.status;
    await apiPatchJson(`/api/admin/users/${user.id}/status`, { status: nextStatus });
    setMessage(`Updated ${user.username} status to ${nextStatus}.`);
    await loadUsers(offset);
  }

  async function applyRole(userId: string, member: Membership) {
    const key = `${userId}:${member.org_id}`;
    const nextRole = roleDraft[key] || member.role;
    await apiPatchJson(`/api/admin/users/${userId}/memberships/${member.org_id}/role`, { role: nextRole });
    setMessage(`Updated role to ${nextRole}.`);
    await refreshAll(offset);
  }

  async function removeMembership(userId: string, member: Membership) {
    await apiDelete(`/api/admin/users/${userId}/memberships/${member.org_id}`);
    setMessage(`Removed membership ${member.org_name}.`);
    await loadUsers(offset);
  }

  async function addMembership(user: UserRow) {
    const draftOrg = addOrgDraft[user.id] || (!isSuperAdmin ? me?.org_id || "" : "");
    const draftRole = addRoleDraft[user.id] || roleOptions[0] || "org_dm_engineer";
    if (!draftOrg) {
      setMessage("Select an organization before adding membership.");
      return;
    }
    await apiPostJson(`/api/admin/users/${user.id}/memberships`, { org_id: draftOrg, role: draftRole });
    setMessage(`Added/updated membership for ${user.username}.`);
    await loadUsers(offset);
  }

  async function unlockUser(user: UserRow) {
    await apiPostJson(`/api/admin/users/${user.id}/unlock`, { reason: "admin_unlock" });
    setMessage(`Unlocked ${user.username}.`);
    await loadUsers(offset);
    await loadAuditRows();
  }

  async function resetSession(user: UserRow) {
    await apiPostJson(`/api/admin/users/${user.id}/reset-session`, { reason: "admin_reset_session" });
    setMessage(`Reset active sessions for ${user.username}.`);
    await loadUsers(offset);
    await loadAuditRows();
  }

  async function approveRequest(row: RegistrationRow) {
    const nextRole = approveRoleDraft[row.id] || "org_dm_engineer";
    await apiPostJson(`/api/registration-requests/${row.id}/approve`, { role: nextRole });
    setMessage(`Approved ${row.username} as ${nextRole}.`);
    await refreshAll(offset);
  }

  async function rejectRequest(row: RegistrationRow) {
    await apiPostJson(`/api/registration-requests/${row.id}/reject`, { reason: "rejected by administrator" });
    setMessage(`Rejected ${row.username}.`);
    await refreshAll(offset);
  }

  async function createRole() {
    const roleName = newRoleName.trim();
    const permissions = parsePermissionText(newRolePermissions);
    if (!roleName || permissions.length === 0) {
      setMessage("Role name and at least one permission are required.");
      return;
    }
    await apiPostJson("/api/admin/roles", { role: roleName, permissions });
    setNewRoleName("");
    setNewRolePermissions("");
    setMessage(`Created role ${roleName}.`);
    await refreshAll(offset);
  }

  async function saveRolePermissions(roleName: string, current: string[]) {
    const raw = rolePermDraft[roleName];
    const permissions = parsePermissionText(typeof raw === "string" ? raw : current.join(", "));
    if (permissions.length === 0) {
      setMessage("At least one permission is required.");
      return;
    }
    await apiPutJson(`/api/admin/roles/${roleName}/permissions`, { permissions });
    setMessage(`Updated permissions for ${roleName}.`);
    await refreshAll(offset);
  }

  async function deleteRole(roleName: string) {
    await apiDelete(`/api/admin/roles/${roleName}`);
    setMessage(`Deleted role ${roleName}.`);
    await refreshAll(offset);
  }

  async function exportAuditCsv() {
    const params = new URLSearchParams();
    params.set("limit", "5000");
    if (auditEventType.trim()) params.set("event_type", auditEventType.trim());
    if (auditOutcome.trim()) params.set("outcome", auditOutcome.trim());
    if (auditTargetType.trim()) params.set("target_type", auditTargetType.trim());
    if (auditActorUserId.trim()) params.set("actor_user_id", auditActorUserId.trim());
    const token = getTokenFromBrowser();
    const res = await fetch(buildApiUrl(`/api/audit/events/export?${params.toString()}`), {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      throw new Error(`Audit export failed: ${res.status}`);
    }
    const blob = await res.blob();
    const href = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = href;
    a.download = "audit_events.csv";
    a.click();
    URL.revokeObjectURL(href);
  }

  const pageEnd = Math.min(offset + PAGE_SIZE, rowCount);
  const pageStart = rowCount === 0 ? 0 : offset + 1;

  return (
    <main className="grid" style={{ gridTemplateColumns: "1fr" }}>
      <section className="card">
        <h3>Enterprise User Management and RBAC</h3>
        <div className="muted">Manage approvals, user lifecycle, memberships, and role permission matrix with tenant-scoped controls.</div>
        {message ? <p className="status-pass">{message}</p> : null}
      </section>

      <section className="card">
        <h4>Audit Explorer</h4>
        <div className="controls">
          <label>
            Event Type
            <input value={auditEventType} onChange={(e) => setAuditEventType(e.target.value)} placeholder="USER_STATUS_UPDATE" />
          </label>
          <label>
            Outcome
            <select value={auditOutcome} onChange={(e) => setAuditOutcome(e.target.value)}>
              <option value="">All outcomes</option>
              <option value="SUCCESS">SUCCESS</option>
              <option value="DENIED">DENIED</option>
              <option value="ERROR">ERROR</option>
            </select>
          </label>
          <label>
            Target Type
            <input value={auditTargetType} onChange={(e) => setAuditTargetType(e.target.value)} placeholder="user, role, membership" />
          </label>
          <label>
            Actor User ID
            <input value={auditActorUserId} onChange={(e) => setAuditActorUserId(e.target.value)} placeholder="optional actor user id" />
          </label>
          <label style={{ alignSelf: "end", display: "flex", gap: 8 }}>
            <button type="button" className="primary" onClick={() => loadAuditRows()}>
              Apply filters
            </button>
            <button type="button" onClick={() => exportAuditCsv().catch((ex) => setMessage(ex.message))}>
              Export CSV
            </button>
          </label>
        </div>
        <div className="table-wrap" style={{ marginTop: 10 }}>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Event</th>
                <th>Actor</th>
                <th>Target</th>
                <th>Outcome</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {auditRows.map((a) => (
                <tr key={a.id}>
                  <td className="cell-sub">{a.created_at_utc}</td>
                  <td>{a.event_type}</td>
                  <td className="cell-sub">{a.actor_user_id || "-"}</td>
                  <td className="cell-sub">
                    {a.target_type}:{a.target_id}
                  </td>
                  <td>{a.outcome}</td>
                  <td className="cell-sub truncate">{JSON.stringify(a.details || {})}</td>
                </tr>
              ))}
              {auditRows.length === 0 ? (
                <tr>
                  <td colSpan={6} className="muted">
                    No audit events matched current filters.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <h4>Pending Registration Approvals</h4>
        <div className="table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Requested Org</th>
                <th>Requested At</th>
                <th>Assign Role</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pendingRequests.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="cell-title">{r.username}</div>
                    <div className="cell-sub truncate">{r.email}</div>
                  </td>
                  <td className="cell-sub">{r.requested_org_id}</td>
                  <td className="cell-sub">{r.created_at_utc}</td>
                  <td>
                    <select
                      value={approveRoleDraft[r.id] || "org_dm_engineer"}
                      onChange={(e) => setApproveRoleDraft((prev) => ({ ...prev, [r.id]: e.target.value }))}
                    >
                      {roleOptions.map((it) => (
                        <option key={it} value={it}>
                          {it}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td style={{ display: "flex", gap: 8 }}>
                    <button type="button" className="primary" onClick={() => approveRequest(r)}>
                      Approve
                    </button>
                    <button type="button" onClick={() => rejectRequest(r)}>
                      Reject
                    </button>
                  </td>
                </tr>
              ))}
              {pendingRequests.length === 0 ? (
                <tr>
                  <td colSpan={5} className="muted">
                    No pending requests.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <h4>Role Catalog and Permission Matrix</h4>
        <div className="controls">
          <label>
            New role key
            <input value={newRoleName} onChange={(e) => setNewRoleName(e.target.value)} placeholder="org_readonly_auditor" />
          </label>
          <label>
            Permissions (comma-separated)
            <input
              value={newRolePermissions}
              onChange={(e) => setNewRolePermissions(e.target.value)}
              placeholder="project.design, project.quality, audit.read"
            />
          </label>
          <label style={{ alignSelf: "end" }}>
            <button type="button" className="primary" onClick={() => createRole()}>
              Create role
            </button>
          </label>
        </div>
        <div className="table-wrap" style={{ marginTop: 10 }}>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Role</th>
                <th>Permission Count</th>
                <th>Permissions</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {roles.map((r) => (
                <tr key={r.role}>
                  <td>
                    <div className="cell-title">{r.role}</div>
                    <div className="cell-sub">{SYSTEM_ROLES.has(r.role) ? "system role" : "custom role"}</div>
                  </td>
                  <td>{r.permission_count}</td>
                  <td>
                    <input
                      value={typeof rolePermDraft[r.role] === "string" ? rolePermDraft[r.role] : (r.permissions || []).join(", ")}
                      onChange={(e) => setRolePermDraft((prev) => ({ ...prev, [r.role]: e.target.value }))}
                    />
                  </td>
                  <td style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    <button type="button" className="primary" onClick={() => saveRolePermissions(r.role, r.permissions || [])}>
                      Save permissions
                    </button>
                    {!SYSTEM_ROLES.has(r.role) ? (
                      <button type="button" onClick={() => deleteRole(r.role)}>
                        Delete role
                      </button>
                    ) : null}
                  </td>
                </tr>
              ))}
              {roles.length === 0 ? (
                <tr>
                  <td colSpan={4} className="muted">
                    No roles available.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <h4>User Filters</h4>
        <div className="controls">
          <label>
            Organization
            <select value={orgId} onChange={(e) => setOrgId(e.target.value)} disabled={!isSuperAdmin}>
              {isSuperAdmin ? <option value="">All organizations</option> : null}
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            User status
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">All statuses</option>
              <option value="ACTIVE">ACTIVE</option>
              <option value="SUSPENDED">SUSPENDED</option>
              <option value="LOCKED">LOCKED</option>
              <option value="DISABLED">DISABLED</option>
            </select>
          </label>
          <label>
            Membership role
            <select value={role} onChange={(e) => setRole(e.target.value)}>
              <option value="">All roles</option>
              {roleOptions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </label>
          <label>
            Search
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="username, email, display name, org" />
          </label>
          <label style={{ alignSelf: "end" }}>
            <button type="button" className="primary" onClick={() => loadUsers(0)}>
              Apply filters
            </button>
          </label>
        </div>
      </section>

      <section className="card">
        <div className="users-table-head">
          <h4>Users</h4>
          <div className="muted">
            Showing {pageStart}-{pageEnd} of {rowCount}
          </div>
        </div>
        <div className="table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Status</th>
                <th>Memberships and Roles</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>
                    <div className="cell-title">{u.display_name || u.username}</div>
                    <div className="cell-sub">{u.username}</div>
                    <div className="cell-sub truncate">{u.email}</div>
                    <div className="cell-sub">Created: {u.created_at_utc || "-"}</div>
                    <div className="cell-sub">Last login: {u.last_login_at_utc || "-"}</div>
                    <div className="cell-sub">Failed logins: {u.failed_login_count || 0}</div>
                    <div className="cell-sub">Locked until: {u.locked_until_utc || "-"}</div>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                      <select
                        value={statusDraft[u.id] || u.status}
                        onChange={(e) => setStatusDraft((prev) => ({ ...prev, [u.id]: e.target.value }))}
                      >
                        <option value="ACTIVE">ACTIVE</option>
                        <option value="SUSPENDED">SUSPENDED</option>
                        <option value="LOCKED">LOCKED</option>
                        <option value="DISABLED">DISABLED</option>
                      </select>
                      <button type="button" className="primary" onClick={() => applyStatus(u)}>
                        Update
                      </button>
                      <button type="button" onClick={() => unlockUser(u)}>
                        Unlock
                      </button>
                      <button type="button" onClick={() => resetSession(u)}>
                        Reset Session
                      </button>
                    </div>
                    {u.is_super_admin ? <div className="pill" style={{ marginTop: 8 }}>super_admin</div> : null}
                  </td>
                  <td>
                    <div className="membership-list">
                      {u.memberships.map((m) => {
                        const key = `${u.id}:${m.org_id}`;
                        const membershipRoleOptions = Array.from(new Set([...roleOptions, m.role])).filter(Boolean);
                        return (
                          <div key={key} className="membership-row">
                            <div className="membership-meta">
                              <div className="cell-title">{m.org_name || m.org_id}</div>
                              <div className="cell-sub">{m.org_id}</div>
                              <div className="cell-sub">Membership: {m.status}</div>
                            </div>
                            <div className="membership-actions">
                              <select
                                value={roleDraft[key] || m.role}
                                onChange={(e) => setRoleDraft((prev) => ({ ...prev, [key]: e.target.value }))}
                              >
                                {membershipRoleOptions.map((r) => (
                                  <option key={r} value={r}>
                                    {r}
                                  </option>
                                ))}
                              </select>
                              <button type="button" className="primary" onClick={() => applyRole(u.id, m)}>
                                Save role
                              </button>
                              <button type="button" onClick={() => removeMembership(u.id, m)}>
                                Remove membership
                              </button>
                            </div>
                          </div>
                        );
                      })}
                      <div className="membership-row">
                        <div className="membership-meta">
                          <div className="cell-title">Add membership</div>
                          <div className="cell-sub">Assign org and role for this user.</div>
                        </div>
                        <div className="membership-actions">
                          <select
                            value={addOrgDraft[u.id] || (!isSuperAdmin ? me?.org_id || "" : "")}
                            onChange={(e) => setAddOrgDraft((prev) => ({ ...prev, [u.id]: e.target.value }))}
                            disabled={!isSuperAdmin}
                          >
                            {isSuperAdmin ? <option value="">Select org</option> : null}
                            {orgs.map((o) => (
                              <option key={o.id} value={o.id}>
                                {o.name}
                              </option>
                            ))}
                          </select>
                          <select
                            value={addRoleDraft[u.id] || roleOptions[0] || "org_dm_engineer"}
                            onChange={(e) => setAddRoleDraft((prev) => ({ ...prev, [u.id]: e.target.value }))}
                          >
                            {roleOptions.map((r) => (
                              <option key={r} value={r}>
                                {r}
                              </option>
                            ))}
                          </select>
                          <button type="button" className="primary" onClick={() => addMembership(u)}>
                            Add membership
                          </button>
                        </div>
                      </div>
                      {u.memberships.length === 0 ? <div className="muted">No memberships.</div> : null}
                    </div>
                  </td>
                </tr>
              ))}
              {!loading && users.length === 0 ? (
                <tr>
                  <td colSpan={3} className="muted">
                    No users matched current filters.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
        <div className="users-pager">
          <button type="button" onClick={() => loadUsers(Math.max(0, offset - PAGE_SIZE))} disabled={offset === 0}>
            Previous
          </button>
          <button type="button" onClick={() => loadUsers(offset + PAGE_SIZE)} disabled={offset + PAGE_SIZE >= rowCount}>
            Next
          </button>
        </div>
      </section>
    </main>
  );
}
