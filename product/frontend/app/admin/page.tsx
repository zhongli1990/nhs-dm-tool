"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import DataTable from "../../components/DataTable";
import { apiGet, apiPostJson } from "../../lib/api";

type OrgRow = { id: string; name: string; slug: string; status: string };
type WsRow = { id: string; org_id: string; name: string; slug: string; status: string };
type ProjRow = { id: string; workspace_id: string; name: string; slug: string; status: string };

export default function AdminPage() {
  const [orgs, setOrgs] = useState<OrgRow[]>([]);
  const [workspaces, setWorkspaces] = useState<WsRow[]>([]);
  const [projects, setProjects] = useState<ProjRow[]>([]);
  const [requests, setRequests] = useState<any[]>([]);
  const [orgId, setOrgId] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");
  const [newOrg, setNewOrg] = useState("");
  const [newWs, setNewWs] = useState("");
  const [newProject, setNewProject] = useState("");
  const [message, setMessage] = useState("");

  const selectedOrg = useMemo(() => orgs.find((o) => o.id === orgId), [orgId, orgs]);

  async function load() {
    const orgPayload = await apiGet<{ rows: OrgRow[] }>("/api/orgs");
    const orgRows = orgPayload.rows || [];
    setOrgs(orgRows);
    const nextOrg = orgId || orgRows[0]?.id || "";
    setOrgId(nextOrg);
    if (nextOrg) {
      const wsPayload = await apiGet<{ rows: WsRow[] }>(`/api/orgs/${nextOrg}/workspaces`);
      const wsRows = wsPayload.rows || [];
      setWorkspaces(wsRows);
      const nextWs = workspaceId || wsRows[0]?.id || "";
      setWorkspaceId(nextWs);
      if (nextWs) {
        const projPayload = await apiGet<{ rows: ProjRow[] }>(`/api/workspaces/${nextWs}/projects`);
        setProjects(projPayload.rows || []);
      } else {
        setProjects([]);
      }
    } else {
      setWorkspaces([]);
      setProjects([]);
    }
    const reqPayload = await apiGet<{ rows: any[] }>("/api/registration-requests?status=PENDING_APPROVAL");
    setRequests(reqPayload.rows || []);
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  async function createOrg(e: FormEvent) {
    e.preventDefault();
    if (!newOrg.trim()) return;
    await apiPostJson("/api/orgs", { name: newOrg.trim() });
    setNewOrg("");
    setMessage("Organization created.");
    await load();
  }

  async function createWorkspace(e: FormEvent) {
    e.preventDefault();
    if (!orgId || !newWs.trim()) return;
    await apiPostJson(`/api/orgs/${orgId}/workspaces`, { name: newWs.trim() });
    setNewWs("");
    setMessage("Workspace created.");
    await load();
  }

  async function createProject(e: FormEvent) {
    e.preventDefault();
    if (!workspaceId || !newProject.trim()) return;
    await apiPostJson(`/api/workspaces/${workspaceId}/projects`, { name: newProject.trim() });
    setNewProject("");
    setMessage("Project created.");
    await load();
  }

  async function approveRequest(requestId: string) {
    await apiPostJson(`/api/registration-requests/${requestId}/approve`, { role: "org_dm_engineer" });
    setMessage("Registration approved.");
    await load();
  }

  async function rejectRequest(requestId: string) {
    await apiPostJson(`/api/registration-requests/${requestId}/reject`, { reason: "rejected by administrator" });
    setMessage("Registration rejected.");
    await load();
  }

  return (
    <main className="grid" style={{ gridTemplateColumns: "1fr" }}>
      <section className="card">
        <h3>OpenLI DMM Admin Console</h3>
        <div className="muted">Manage organizations, workspaces, projects, and registration approvals.</div>
        {message ? <p className="status-pass">{message}</p> : null}
      </section>

      <section className="card">
        <h4>Organizations</h4>
        <form onSubmit={createOrg} className="controls">
          <label>
            New organization
            <input value={newOrg} onChange={(e) => setNewOrg(e.target.value)} />
          </label>
          <label style={{ alignSelf: "end" }}>
            <button className="primary">Create organization</button>
          </label>
        </form>
        <DataTable columns={["id", "name", "slug", "status"]} rows={orgs as any[]} />
      </section>

      <section className="card">
        <h4>Workspaces and Projects</h4>
        <div className="controls">
          <label>
            Organization
            <select value={orgId} onChange={(e) => setOrgId(e.target.value)}>
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Workspace
            <select value={workspaceId} onChange={(e) => setWorkspaceId(e.target.value)}>
              {workspaces.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </label>
          <label style={{ alignSelf: "end" }}>
            <button onClick={() => load()} type="button">
              Refresh
            </button>
          </label>
        </div>
        <div className="controls">
          <form onSubmit={createWorkspace}>
            <label>
              New workspace in {selectedOrg?.name || "org"}
              <input value={newWs} onChange={(e) => setNewWs(e.target.value)} />
            </label>
            <button className="primary" style={{ marginTop: 8 }}>
              Create workspace
            </button>
          </form>
          <form onSubmit={createProject}>
            <label>
              New project in workspace
              <input value={newProject} onChange={(e) => setNewProject(e.target.value)} />
            </label>
            <button className="primary" style={{ marginTop: 8 }}>
              Create project
            </button>
          </form>
        </div>
        <div className="grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
          <section className="card">
            <h5>Workspaces</h5>
            <DataTable columns={["id", "org_id", "name", "slug", "status"]} rows={workspaces as any[]} />
          </section>
          <section className="card">
            <h5>Projects</h5>
            <DataTable columns={["id", "workspace_id", "name", "slug", "status"]} rows={projects as any[]} />
          </section>
        </div>
      </section>

      <section className="card">
        <h4>Registration Requests (Pending Approval)</h4>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Request</th>
                <th>Username</th>
                <th>Email</th>
                <th>Org</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id}>
                  <td>{r.id}</td>
                  <td>{r.username}</td>
                  <td>{r.email}</td>
                  <td>{r.requested_org_id}</td>
                  <td>{r.created_at_utc}</td>
                  <td style={{ display: "flex", gap: 6 }}>
                    <button className="primary" onClick={() => approveRequest(r.id)}>
                      Approve
                    </button>
                    <button onClick={() => rejectRequest(r.id)}>Reject</button>
                  </td>
                </tr>
              ))}
              {requests.length === 0 ? (
                <tr>
                  <td colSpan={6} className="muted">
                    No pending requests.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
