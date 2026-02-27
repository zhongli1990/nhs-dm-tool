"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPostJson, getTokenFromBrowser } from "../lib/api";

type OrgRow = { id: string; name: string };
type WsRow = { id: string; name: string };
type ProjRow = { id: string; name: string };

export default function AuthToolbar() {
  const [user, setUser] = useState<any>(null);
  const [orgs, setOrgs] = useState<OrgRow[]>([]);
  const [workspaces, setWorkspaces] = useState<WsRow[]>([]);
  const [projects, setProjects] = useState<ProjRow[]>([]);
  const [orgId, setOrgId] = useState("");
  const [workspaceId, setWorkspaceId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [contextOpen, setContextOpen] = useState(false);
  const [contextMessage, setContextMessage] = useState("");
  const hasToken = typeof window !== "undefined" && !!getTokenFromBrowser();

  async function reloadMe() {
    try {
      const me = await apiGet<{ user: any }>("/api/auth/me");
      const next = me.user || null;
      setUser(next);
      setOrgId(next?.org_id || "");
      setWorkspaceId(next?.workspace_id || "");
      setProjectId(next?.project_id || "");
    } catch {
      setUser(null);
    }
  }

  useEffect(() => {
    if (!hasToken) return;
    reloadMe().catch(() => undefined);
  }, [hasToken]);

  useEffect(() => {
    if (!user) return;
    apiGet<{ rows: OrgRow[] }>("/api/orgs")
      .then((r) => setOrgs(r.rows || []))
      .catch(() => setOrgs([]));
  }, [user]);

  useEffect(() => {
    if (!orgId || !user) return;
    apiGet<{ rows: WsRow[] }>(`/api/orgs/${orgId}/workspaces`)
      .then((r) => setWorkspaces(r.rows || []))
      .catch(() => setWorkspaces([]));
  }, [orgId, user]);

  useEffect(() => {
    if (!workspaceId || !user) return;
    apiGet<{ rows: ProjRow[] }>(`/api/workspaces/${workspaceId}/projects`)
      .then((r) => setProjects(r.rows || []))
      .catch(() => setProjects([]));
  }, [workspaceId, user]);

  async function applyContext() {
    setContextMessage("");
    try {
      const payload = await apiPostJson<{ access_token: string; user: any }>("/api/auth/switch-context", {
        org_id: orgId,
        workspace_id: workspaceId,
        project_id: projectId,
      });
      localStorage.setItem("dmm_access_token", payload.access_token);
      localStorage.setItem("dmm_user", JSON.stringify(payload.user || {}));
      document.cookie = `dmm_access_token=${encodeURIComponent(payload.access_token)}; Max-Age=43200; Path=/; SameSite=Lax`;
      setUser(payload.user || user);
      setContextOpen(false);
      window.location.reload();
    } catch {
      setContextMessage("Failed to apply context");
    }
  }

  function logout() {
    localStorage.removeItem("dmm_access_token");
    localStorage.removeItem("dmm_user");
    document.cookie = "dmm_access_token=; Max-Age=0; path=/";
    setUser(null);
    window.location.href = "/login";
  }

  const role = useMemo(() => (user?.role ? String(user.role) : ""), [user]);

  if (!user) {
    return (
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <Link href="/login" className="topbar-meta">
          Login
        </Link>
        <Link href="/register" className="topbar-meta">
          Register
        </Link>
      </div>
    );
  }

  return (
    <div className="toolbar-wrap">
      <span className="topbar-meta">{user.display_name || user.username || "User"}</span>
      <span className="topbar-meta">{role}</span>
      <button onClick={() => setContextOpen((v) => !v)} className="topbar-meta-btn">
        Context
      </button>
      <Link href="/onboarding" className="topbar-meta">
        Onboarding
      </Link>
      <Link href="/settings" className="topbar-meta">
        Settings
      </Link>
      <button onClick={logout} className="topbar-meta-btn">
        Logout
      </button>

      {contextOpen ? (
        <div className="context-popover card">
          <div className="muted">Organization</div>
          <select value={orgId} onChange={(e) => setOrgId(e.target.value)}>
            {(orgs || []).map((o) => (
              <option key={o.id} value={o.id}>
                {o.name}
              </option>
            ))}
          </select>
          <div className="muted" style={{ marginTop: 8 }}>Workspace</div>
          <select value={workspaceId} onChange={(e) => setWorkspaceId(e.target.value)}>
            {(workspaces || []).map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
          <div className="muted" style={{ marginTop: 8 }}>Project</div>
          <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
            {(projects || []).map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <button className="primary" onClick={applyContext}>
              Apply
            </button>
            <button onClick={() => setContextOpen(false)}>Close</button>
          </div>
          {contextMessage ? <div className="status-fail" style={{ marginTop: 8 }}>{contextMessage}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
