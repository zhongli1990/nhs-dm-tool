"use client";

import { useEffect, useState } from "react";
import { API_BASE, apiGet } from "../../lib/api";

export default function SettingsPage() {
  const [profile, setProfile] = useState("pre_production");
  const [rowsPerPage, setRowsPerPage] = useState("200");
  const [apiBase, setApiBase] = useState(API_BASE);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const p = localStorage.getItem("dmm_release_profile");
    const r = localStorage.getItem("dmm_rows_per_page");
    if (p) setProfile(p);
    if (r) setRowsPerPage(r);
  }, []);

  async function saveSettings() {
    localStorage.setItem("dmm_release_profile", profile);
    localStorage.setItem("dmm_rows_per_page", rowsPerPage);
    setMessage("Settings saved for this browser session.");
  }

  async function testApi() {
    try {
      await apiGet("/health");
      setMessage("Backend connectivity check passed.");
    } catch {
      setMessage("Backend connectivity failed.");
    }
  }

  return (
    <main className="grid" style={{ gridTemplateColumns: "1fr" }}>
      <section className="card">
        <h3>Application Settings</h3>
        <div className="muted">Enterprise runtime settings and local operator preferences.</div>
        {message ? <p className="status-pass">{message}</p> : null}
      </section>

      <section className="card">
        <h4>Runtime Defaults</h4>
        <div className="controls">
          <label>
            Backend API base
            <input value={apiBase} onChange={(e) => setApiBase(e.target.value)} disabled />
          </label>
          <label>
            Default release profile
            <select value={profile} onChange={(e) => setProfile(e.target.value)}>
              <option value="development">development</option>
              <option value="pre_production">pre_production</option>
              <option value="cutover_ready">cutover_ready</option>
            </select>
          </label>
          <label>
            Default rows per page
            <select value={rowsPerPage} onChange={(e) => setRowsPerPage(e.target.value)}>
              <option value="100">100</option>
              <option value="200">200</option>
              <option value="500">500</option>
            </select>
          </label>
        </div>
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          <button className="primary" onClick={saveSettings}>Save settings</button>
          <button onClick={testApi}>Test backend connectivity</button>
        </div>
      </section>

      <section className="card">
        <h4>Operational Guidance</h4>
        <div className="muted">
          Use Onboarding for tenant/project setup, Connectors for source/target connection profiles,
          Mappings for contract governance, and Lifecycle for controlled run execution.
        </div>
      </section>
    </main>
  );
}
