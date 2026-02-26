"use client";

import { useEffect, useState } from "react";
import { apiGet } from "../../lib/api";
import DataTable from "../../components/DataTable";
import SectionTabs from "../../components/SectionTabs";

export default function MappingsPage() {
  const [summary, setSummary] = useState<any>({});
  const [rows, setRows] = useState<any[]>([]);
  const [targetTable, setTargetTable] = useState("");
  const [mappingClass, setMappingClass] = useState("");
  const [view, setView] = useState<"summary" | "rows">("summary");
  const [loading, setLoading] = useState(false);

  async function loadAll() {
    const payload = await apiGet<{ summary: any; rows: any[] }>("/api/mappings/contract");
    setSummary(payload.summary || {});
    setRows(payload.rows || []);
  }

  async function loadFiltered() {
    setLoading(true);
    const query = new URLSearchParams();
    if (targetTable) query.set("target_table", targetTable);
    if (mappingClass) query.set("mapping_class", mappingClass);
    query.set("limit", "5000");
    const payload = await apiGet<{ rows: any[] }>(`/api/mappings/contract/query?${query.toString()}`);
    setRows(payload.rows || []);
    setLoading(false);
  }

  useEffect(() => {
    loadAll().catch(() => undefined);
  }, []);

  const mappingClasses = Object.keys(summary.mapping_class_counts || {});
  const tableOptions = Array.from(new Set((rows || []).map((r) => r.target_table).filter(Boolean))).sort();

  return (
    <main className="grid">
      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Mapping Contract Explorer</h3>
        <div className="muted">Field-level mapping governance with filterable dynamic rendering for large NHS estates.</div>
        <SectionTabs
          tabs={[
            { id: "summary", label: "Summary" },
            { id: "rows", label: "Field Rows" },
          ]}
          active={view}
          onChange={(id) => setView(id as "summary" | "rows")}
        />
      </section>

      {view === "summary" ? (
        <section className="card">
          <h3>Mapping Class Summary</h3>
          <DataTable
            columns={["class", "count"]}
            rows={Object.entries(summary.mapping_class_counts || {}).map(([k, v]) => ({ class: k, count: String(v) }))}
          />
        </section>
      ) : null}

      {view === "rows" ? (
        <section className="card" style={{ gridColumn: "1 / -1" }}>
          <h3>Contract Rows</h3>
          <div className="controls">
            <label>
              Target table
              <select value={targetTable} onChange={(e) => setTargetTable(e.target.value)}>
                <option value="">All</option>
                {tableOptions.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Mapping class
              <select value={mappingClass} onChange={(e) => setMappingClass(e.target.value)}>
                <option value="">All</option>
                {mappingClasses.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Actions
              <button type="button" className="primary" onClick={() => loadFiltered().catch(() => undefined)} disabled={loading}>
                {loading ? "Filtering..." : "Apply Filter"}
              </button>
            </label>
          </div>
          <DataTable
            columns={
              rows.length
                ? ["target_table", "target_field", "mapping_class", "primary_source_table", "primary_source_field", "transformation_rule"]
                : ["target_table"]
            }
            rows={rows.slice(0, 1000)}
            emptyLabel="No mapping rows."
          />
          <div className="muted">Showing up to 1000 rows in UI.</div>
        </section>
      ) : null}

      <section className="card">
        <h3>Mapping Class Summary</h3>
        <div className="muted">Total rows loaded: {rows.length}</div>
        <div className="muted">Distinct classes: {mappingClasses.length}</div>
        <div className="muted">Use Field Rows tab for deep filter/query workflow.</div>
      </section>
    </main>
  );
}
