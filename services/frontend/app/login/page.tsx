"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { API_BASE } from "../../lib/api";
import ThemeModeSwitch from "../../components/ThemeModeSwitch";
import { APP_VERSION } from "../../lib/version";

export default function LoginPage() {
  const [usernameOrEmail, setUsernameOrEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [debug, setDebug] = useState<string[]>([]);

  function pushDebug(message: string) {
    const ts = new Date().toISOString();
    const line = `[${ts}] ${message}`;
    setDebug((prev) => [...prev.slice(-8), line]);
    console.info("[login-debug]", line);
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setDebug([]);
    try {
      pushDebug(`POST ${API_BASE}/api/auth/login`);
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username_or_email: usernameOrEmail, password }),
      });
      pushDebug(`login status=${res.status}`);
      const payload = await res.json();
      if (!res.ok) throw new Error(payload?.detail || "Login failed");
      const token = String(payload.access_token || "");
      if (!token) {
        throw new Error("Login response missing access token");
      }
      localStorage.setItem("dmm_access_token", token);
      localStorage.setItem("dmm_user", JSON.stringify(payload.user || {}));
      pushDebug(`token stored in localStorage, length=${token.length}`);
      document.cookie = `dmm_access_token=${encodeURIComponent(token)}; Max-Age=43200; Path=/; SameSite=Lax`;
      const cookieSet = document.cookie.includes("dmm_access_token=");
      pushDebug(`cookie set=${cookieSet}`);

      const meRes = await fetch(`${API_BASE}/api/auth/me`, {
        cache: "no-store",
        headers: { Authorization: `Bearer ${token}` },
      });
      pushDebug(`auth/me status=${meRes.status}`);
      if (!meRes.ok) {
        const text = await meRes.text();
        throw new Error(`Session verification failed (${meRes.status}): ${text}`);
      }

      pushDebug("redirecting to /");
      window.location.assign("/");
    } catch (ex: any) {
      const msg = ex?.message || "Login failed";
      pushDebug(`error=${msg}`);
      setError(msg);
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
            <h1 className="auth-brand-title">OpenLI DMM</h1>
            <div className="auth-brand-copy">
              Mission-critical Data Migration Manager for NHS PAS/EPR programmes.
              <br />
              <br />
              Secure sign-in gives access to your organization, workspace, and project lifecycle operations.
            </div>
          </section>
          <section className="auth-form-card">
            <h2>Sign In</h2>
            <div className="muted">Use your approved enterprise account credentials.</div>
            <form onSubmit={onSubmit} style={{ marginTop: 12 }}>
              <div className="controls">
                <label>
                  Username or email
                  <input autoComplete="username" value={usernameOrEmail} onChange={(e) => setUsernameOrEmail(e.target.value)} />
                </label>
                <label>
                  Password
                  <input autoComplete="current-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
                </label>
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 10, alignItems: "center" }}>
                <button className="primary" disabled={busy}>
                  {busy ? "Signing in..." : "Sign in"}
                </button>
                <Link href="/register" className="topbar-meta">
                  Register
                </Link>
              </div>
              {error ? (
                <p className="status-fail" style={{ marginTop: 10 }}>
                  {error}
                </p>
              ) : null}
              {debug.length > 0 ? (
                <div className="log" style={{ marginTop: 10, maxHeight: 140 }}>
                  {debug.join("\n")}
                </div>
              ) : null}
              <div className="muted" style={{ marginTop: 10 }}>Version {APP_VERSION}</div>
            </form>
          </section>
        </div>
      </section>
    </main>
  );
}
