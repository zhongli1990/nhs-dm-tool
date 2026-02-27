"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPostJson } from "../../lib/api";

type Org = { id: string; name: string };
type Workspace = { id: string; name: string };

export default function OnboardingPage() {
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [orgId, setOrgId] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [projectName, setProjectName] = useState("");
  const [message, setMessage] = useState("");

  async function loadOrgs() {
    const payload = await apiGet<{ rows: Org[] }>("/api/orgs");
    const rows = payload.rows || [];
    setOrgs(rows);
    const next = orgId || rows[0]?.id || "";
    setOrgId(next);
    if (next) {
      const ws = await apiGet<{ rows: Workspace[] }>(`/api/orgs/${next}/workspaces`);
      setWorkspaces(ws.rows || []);
      setWorkspaceId((cur) => cur || ws.rows?.[0]?.id || "");
    }
  }

  useEffect(() => {
    loadOrgs().catch(() => undefined);
  }, []);

  async function createWorkspace() {
    if (!orgId || !workspaceName.trim()) return;
    await apiPostJson(`/api/orgs/${orgId}/workspaces`, { name: workspaceName.trim() });
    setWorkspaceName("");
    setMessage("Workspace created.");
    await loadOrgs();
  }

  async function createProject() {
    if (!workspaceId || !projectName.trim()) return;
    await apiPostJson(`/api/workspaces/${workspaceId}/projects`, { name: projectName.trim() });
    setProjectName("");
    setMessage("Project created.");
  }

  return (
    <main className="grid" style={{ gridTemplateColumns: "1fr" }}>
      <section className="card">
        <h3>Enterprise Onboarding</h3>
        <div className="muted">SaaS onboarding workflow for organization, workspace, project and connector setup.</div>
        {message ? <p className="status-pass">{message}</p> : null}
      </section>

      <section className="card">
        <h4>Step 1. Tenant Context</h4>
        <div className="controls">
          <label>
            Organization
            <select
              value={orgId}
              onChange={async (e) => {
                const next = e.target.value;
                setOrgId(next);
                const ws = await apiGet<{ rows: Workspace[] }>(`/api/orgs/${next}/workspaces`);
                setWorkspaces(ws.rows || []);
                setWorkspaceId(ws.rows?.[0]?.id || "");
              }}
            >
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            New workspace name
            <input value={workspaceName} onChange={(e) => setWorkspaceName(e.target.value)} placeholder="e.g. PAS EPR Programme" />
          </label>
          <label style={{ alignSelf: "end" }}>
            <button className="primary" onClick={createWorkspace}>
              Create workspace
            </button>
          </label>
        </div>
      </section>

      <section className="card">
        <h4>Step 2. Project Setup</h4>
        <div className="controls">
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
          <label>
            New project name
            <input value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="e.g. QVH PAS18.4 migration" />
          </label>
          <label style={{ alignSelf: "end" }}>
            <button className="primary" onClick={createProject}>
              Create project
            </button>
          </label>
        </div>
      </section>

      <section className="card">
        <h4>Step 3. Connector and Lifecycle</h4>
        <div className="muted">Continue in Connectors, Mappings, Quality, and Lifecycle tabs to complete onboarding and controlled migration execution.</div>
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          <a className="topbar-meta" href="/connectors">Go to Connectors</a>
          <a className="topbar-meta" href="/lifecycle">Go to Lifecycle</a>
          <a className="topbar-meta" href="/quality">Go to Quality</a>
        </div>
      </section>
    </main>
  );
}
