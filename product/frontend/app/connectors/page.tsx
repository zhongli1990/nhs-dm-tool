"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { apiGet } from "../../lib/api";
import DataTable from "../../components/DataTable";

type ConnectorType = { id: string; label: string; mode: string; direction: string };

export default function ConnectorsPage() {
  const [connectorTypes, setConnectorTypes] = useState<ConnectorType[]>([]);
  const [templates, setTemplates] = useState<Record<string, any>>({});
  const [connectorType, setConnectorType] = useState("cache_iris_emulator");
  const [direction, setDirection] = useState("source");
  const [connectionString, setConnectionString] = useState("");
  const [schemaName, setSchemaName] = useState("INQUIRE");
  const [result, setResult] = useState<any>(null);
  const [selectedTable, setSelectedTable] = useState("");
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const selectedType = useMemo(() => connectorTypes.find((t) => t.id === connectorType), [connectorType, connectorTypes]);

  useEffect(() => {
    async function loadMeta() {
      try {
        const [typesPayload, templatePayload] = await Promise.all([
          apiGet<{ types: ConnectorType[] }>("/api/connectors/types"),
          apiGet<Record<string, any>>("/api/connectors/templates"),
        ]);
        setConnectorTypes(typesPayload.types || []);
        setTemplates(templatePayload || {});
      } catch {
        setConnectorTypes([
          { id: "cache_iris_emulator", label: "Cache/IRIS Emulator (Source)", mode: "emulator", direction: "source" },
          { id: "postgres_emulator", label: "PostgreSQL Emulator (Target)", mode: "emulator", direction: "target" },
          { id: "csv", label: "CSV Folder (Real)", mode: "real", direction: "source_or_target" },
          { id: "json_dummy", label: "JSON Dummy", mode: "dummy", direction: "source_or_target" },
          { id: "odbc", label: "ODBC (Stub)", mode: "stub", direction: "source_or_target" },
          { id: "jdbc", label: "JDBC (Stub)", mode: "stub", direction: "source_or_target" },
        ]);
      }
    }
    loadMeta();
  }, []);

  useEffect(() => {
    const templateKey = Object.keys(templates).find((k) => (templates[k]?.connector_type || "") === connectorType);
    if (!templateKey) return;
    const tpl = templates[templateKey];
    setConnectionString(tpl.connection_string || "");
    setSchemaName(tpl.schema_name || "");
    setDirection(tpl.direction || "source");
  }, [connectorType, templates]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("dmm_access_token") : "";
      const res = await fetch(`${process.env.NEXT_PUBLIC_DM_API_BASE || "http://localhost:9134"}/api/connectors/explore`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          connector_type: connectorType,
          connection_string: connectionString,
          schema_name: schemaName,
          direction,
          options: {},
        }),
      });
      const payload = await res.json();
      if (!res.ok) throw new Error(payload?.detail || "Connector exploration failed");
      setResult(payload);
      const first = (payload.tables || [])[0] || "";
      setSelectedTable(first);
    } catch (ex: any) {
      setError(ex?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  const preview = selectedTable ? result?.previews?.[selectedTable] : null;
  const previewRows = preview?.sample_rows || [];
  const previewColumns = preview?.columns || [];

  return (
    <main className="grid">
      <section className="card">
        <h3>Connector Configuration</h3>
        <div className="muted">Configure source and target connector profiles for NHS migration runs.</div>
        <form onSubmit={onSubmit}>
          <div className="controls">
            <label>
              Connector type
              <select value={connectorType} onChange={(e) => setConnectorType(e.target.value)}>
                {connectorTypes.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Direction
              <select value={direction} onChange={(e) => setDirection(e.target.value)}>
                <option value="source">source</option>
                <option value="target">target</option>
              </select>
            </label>
            <label>
              Connection string / folder path
              <input value={connectionString} onChange={(e) => setConnectionString(e.target.value)} />
            </label>
            <label>
              Schema name
              <input value={schemaName} onChange={(e) => setSchemaName(e.target.value)} />
            </label>
            <label>
              Actions
              <button type="submit" className="primary" disabled={loading}>
                {loading ? "Testing..." : "Test & Explore"}
              </button>
            </label>
          </div>
        </form>
        <div className="muted" style={{ marginTop: 8 }}>
          Mode: <span className="pill">{selectedType?.mode || "-"}</span> | Recommended: <span className="pill">{selectedType?.direction || "-"}</span>
        </div>
        {error ? <div className="status-fail" style={{ marginTop: 8 }}>{error}</div> : null}
      </section>

      <section className="card">
        <h3>Discovered Tables</h3>
        <div className="muted">Table count: {result?.table_count ?? 0}</div>
        <div className="controls">
          <label>
            Selected table
            <select value={selectedTable} onChange={(e) => setSelectedTable(e.target.value)} disabled={!result?.tables?.length}>
              {(result?.tables || []).map((t: string) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
        </div>
        <DataTable
          columns={["table", "columns", "sample_rows"]}
          rows={Object.entries(result?.previews || {}).slice(0, 300).map(([t, p]: any) => ({
            table: t,
            columns: (p?.columns || []).length,
            sample_rows: (p?.sample_rows || []).length,
          }))}
          emptyLabel="Run connector exploration to load tables."
        />
      </section>

      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Selected Table Preview: {selectedTable || "-"}</h3>
        <DataTable columns={previewColumns.length ? previewColumns.map((c: any) => c.field_name || c.name || String(c)) : ["field_name"]} rows={previewRows} emptyLabel="No preview rows." />
      </section>
    </main>
  );
}

