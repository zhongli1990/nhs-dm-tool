"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { buildApiUrl } from "../../lib/api";
import ThemeModeSwitch from "../../components/ThemeModeSwitch";
import { APP_VERSION } from "../../lib/version";

type OrgRow = { id: string; name: string };

export default function RegisterPage() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [requestedOrgId, setRequestedOrgId] = useState("");
  const [orgs, setOrgs] = useState<OrgRow[]>([]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [version, setVersion] = useState(APP_VERSION);

  useEffect(() => {
    fetch(buildApiUrl("/api/auth/orgs"))
      .then((r) => r.json())
      .then((p) => {
        const rows = (p?.rows || []) as OrgRow[];
        setOrgs(rows);
        if (rows.length > 0) setRequestedOrgId(rows[0].id);
      })
      .catch(() => setOrgs([]));

    fetch(buildApiUrl("/api/meta/version"))
      .then((r) => r.json())
      .then((p) => {
        const v = String(p?.current_version || "").trim();
        if (v) setVersion(v);
      })
      .catch(() => undefined);
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const res = await fetch(buildApiUrl("/api/auth/register"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          email,
          display_name: displayName || username,
          password,
          requested_org_id: requestedOrgId,
        }),
      });
      const payload = await res.json();
      if (!res.ok) throw new Error(payload?.detail || "Registration failed");
      setMessage("Registration submitted. Waiting for super admin or org admin approval.");
    } catch (ex: any) {
      setError(ex?.message || "Registration failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-root">
      <section className="auth-content">
        <div className="auth-toolbar">
          <ThemeModeSwitch />
        </div>
        <div className="auth-panel">
          <section className="auth-brand">
            <h1 className="auth-brand-title">Request Access</h1>
            <div className="auth-brand-copy">
              Submit a registration request for your NHS organization.
              <br />
              <br />
              Super Admin or Org Admin approval is required before sign-in.
            </div>
          </section>
          <section className="auth-form-card">
            <h2>Register</h2>
            <div className="muted">Create OpenLI DMM account request for approval.</div>
            <form onSubmit={onSubmit} style={{ marginTop: 12 }}>
              <div className="controls">
                <label>
                  Username
                  <input value={username} onChange={(e) => setUsername(e.target.value)} required />
                </label>
                <label>
                  Email
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                </label>
                <label>
                  Display name
                  <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
                </label>
                <label>
                  Password
                  <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                </label>
                <label>
                  Requested organization
                  <select value={requestedOrgId} onChange={(e) => setRequestedOrgId(e.target.value)} required>
                    {orgs.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 10, alignItems: "center" }}>
                <button className="primary" disabled={busy}>
                  {busy ? "Submitting..." : "Submit registration"}
                </button>
                <Link href="/login" className="topbar-meta">
                  Back to login
                </Link>
              </div>
              {message ? (
                <p className="status-pass" style={{ marginTop: 10 }}>
                  {message}
                </p>
              ) : null}
              {error ? (
                <p className="status-fail" style={{ marginTop: 10 }}>
                  {error}
                </p>
              ) : null}
              <div className="muted" style={{ marginTop: 10 }}>Version {version}</div>
            </form>
          </section>
        </div>
      </section>
    </main>
  );
}
