"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type ConnectorType = { id: string; label: string; mode: string; direction: string };

const API_BASE = process.env.NEXT_PUBLIC_DM_API_BASE || "http://localhost:8099";

const FALLBACK_CONNECTOR_TYPES: ConnectorType[] = [
  { id: "cache_iris_emulator", label: "Cache/IRIS Emulator (Source)", mode: "emulator", direction: "source" },
  { id: "postgres_emulator", label: "PostgreSQL Emulator (Target)", mode: "emulator", direction: "target" },
  { id: "csv", label: "CSV Folder (Real)", mode: "real", direction: "source_or_target" },
  { id: "json_dummy", label: "JSON Dummy", mode: "dummy", direction: "source_or_target" },
  { id: "odbc", label: "ODBC (Stub)", mode: "stub", direction: "source_or_target" },
  { id: "jdbc", label: "JDBC (Stub)", mode: "stub", direction: "source_or_target" }
];

export default function ConnectorsPage() {
  const [connectorTypes, setConnectorTypes] = useState<ConnectorType[]>(FALLBACK_CONNECTOR_TYPES);
  const [templates, setTemplates] = useState<Record<string, any>>({});
  const [connectorType, setConnectorType] = useState("cache_iris_emulator");
  const [direction, setDirection] = useState("source");
  const [connectionString, setConnectionString] = useState("");
  const [schemaName, setSchemaName] = useState("INQUIRE");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const selectedType = useMemo(() => connectorTypes.find((t) => t.id === connectorType), [connectorType, connectorTypes]);

  useEffect(() => {
    async function loadMeta() {
      try {
        const [typesRes, templatesRes] = await Promise.all([
          fetch(`${API_BASE}/api/connectors/types`),
          fetch(`${API_BASE}/api/connectors/templates`)
        ]);
        if (typesRes.ok) {
          const typesPayload = await typesRes.json();
          if (Array.isArray(typesPayload?.types) && typesPayload.types.length > 0) {
            setConnectorTypes(typesPayload.types);
          }
        }
        if (templatesRes.ok) {
          const tplPayload = await templatesRes.json();
          setTemplates(tplPayload || {});
        }
      } catch {
        // Keep fallback defaults for local/offline UI mode.
      }
    }
    loadMeta();
  }, []);

  useEffect(() => {
    const templateKey = Object.keys(templates).find((k) => (templates[k]?.connector_type || "") === connectorType);
    if (!templateKey) return;
    const tpl = templates[templateKey];
    if (tpl.connection_string !== undefined) setConnectionString(tpl.connection_string || "");
    if (tpl.schema_name !== undefined) setSchemaName(tpl.schema_name || "");
    if (tpl.direction !== undefined) setDirection(tpl.direction || "source");
  }, [connectorType, templates]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${API_BASE}/api/connectors/explore`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          connector_type: connectorType,
          connection_string: connectionString,
          schema_name: schemaName,
          direction,
          options: {}
        })
      });
      const payload = await res.json();
      if (!res.ok) {
        throw new Error(payload?.detail || "Connector exploration failed");
      }
      setResult(payload);
    } catch (ex: any) {
      setError(ex?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid">
      <section className="card">
        <h3>Connector Configuration Console</h3>
        <div className="muted">Configure source/target connectors for migration lifecycle tasks.</div>
        <form onSubmit={onSubmit} style={{ display: "grid", gap: 10, marginTop: 12 }}>
          <label>
            Connector Type
            <select value={connectorType} onChange={(e) => setConnectorType(e.target.value)} style={{ width: "100%", padding: 8, marginTop: 4 }}>
              {connectorTypes.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Direction
            <select value={direction} onChange={(e) => setDirection(e.target.value)} style={{ width: "100%", padding: 8, marginTop: 4 }}>
              <option value="source">source</option>
              <option value="target">target</option>
            </select>
          </label>
          <label>
            Connection String / Folder Path
            <input
              value={connectionString}
              onChange={(e) => setConnectionString(e.target.value)}
              placeholder="e.g. C:\\path\\to\\csvs or emulator default"
              style={{ width: "100%", padding: 8, marginTop: 4 }}
            />
          </label>
          <label>
            Schema Name
            <input value={schemaName} onChange={(e) => setSchemaName(e.target.value)} style={{ width: "100%", padding: 8, marginTop: 4 }} />
          </label>
          <button type="submit" disabled={loading} style={{ padding: "10px 12px", borderRadius: 10, border: "1px solid #b8cdd1", background: "#e7f2ef" }}>
            {loading ? "Testing..." : "Test & Explore Connector"}
          </button>
        </form>
        <div className="muted" style={{ marginTop: 10 }}>
          Selected mode: {selectedType?.mode || "-"} | recommended direction: {selectedType?.direction || "-"}
        </div>
        {error ? <div className="status-fail" style={{ marginTop: 8 }}>{error}</div> : null}
      </section>

      <section className="card">
        <h3>Connector Preview</h3>
        {!result ? <div className="muted">Run a connector exploration to view discovered tables and sample rows.</div> : null}
        {result ? (
          <>
            <div className="muted">
              Connector: {result.connector_type} | Direction: {result.direction} | Tables: {result.table_count}
            </div>
            <table style={{ marginTop: 10 }}>
              <thead>
                <tr>
                  <th>Table</th>
                  <th>Columns</th>
                  <th>Sample Rows</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.previews || {}).slice(0, 12).map(([table, preview]: any) => (
                  <tr key={table}>
                    <td>{table}</td>
                    <td>{(preview?.columns || []).length}</td>
                    <td>{(preview?.sample_rows || []).length}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : null}
      </section>
    </main>
  );
}
