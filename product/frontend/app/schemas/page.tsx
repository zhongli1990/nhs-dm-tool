"use client";

import { useEffect, useState } from "react";
import { apiGet } from "../../lib/api";
import SectionTabs from "../../components/SectionTabs";
import DataTable from "../../components/DataTable";

type TableProfile = { table_name: string; column_count: number };

export default function SchemasPage() {
  const [domain, setDomain] = useState<"source" | "target">("source");
  const [sourceTables, setSourceTables] = useState<TableProfile[]>([]);
  const [targetTables, setTargetTables] = useState<TableProfile[]>([]);
  const [selectedTable, setSelectedTable] = useState("");
  const [selectedFields, setSelectedFields] = useState<any[]>([]);
  const [query, setQuery] = useState("");

  useEffect(() => {
    async function load() {
      const [source, target] = await Promise.all([
        apiGet<{ tables: TableProfile[] }>("/api/schema/source"),
        apiGet<{ tables: TableProfile[] }>("/api/schema/target"),
      ]);
      setSourceTables(source.tables || []);
      setTargetTables(target.tables || []);
    }
    load().catch(() => undefined);
  }, []);

  const tables = domain === "source" ? sourceTables : targetTables;
  const filtered = tables.filter((t) => t.table_name.toLowerCase().includes(query.toLowerCase()));

  useEffect(() => {
    if (!filtered.length) {
      setSelectedTable("");
      setSelectedFields([]);
      return;
    }
    if (!selectedTable || !filtered.some((f) => f.table_name === selectedTable)) {
      setSelectedTable(filtered[0].table_name);
    }
  }, [domain, query, sourceTables.length, targetTables.length]);

  useEffect(() => {
    async function loadTableFields() {
      if (!selectedTable) return;
      const payload = await apiGet<{ fields: any[] }>(`/api/schema/${domain}/${selectedTable}`);
      setSelectedFields(payload.fields || []);
    }
    loadTableFields().catch(() => setSelectedFields([]));
  }, [domain, selectedTable]);

  return (
    <main className="grid">
      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Schema Explorer</h3>
        <div className="muted">Dynamic rendering of table and field definitions for any PAS schema loaded in backend catalogs.</div>
        <SectionTabs
          tabs={[
            { id: "source", label: "Source Catalog" },
            { id: "target", label: "Target Catalog" },
          ]}
          active={domain}
          onChange={(id) => setDomain(id as "source" | "target")}
        />
        <div className="controls">
          <label>
            Search tables
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. PATDATA, LOAD_PMI" />
          </label>
          <label>
            Table
            <select value={selectedTable} onChange={(e) => setSelectedTable(e.target.value)}>
              {filtered.map((t) => (
                <option key={t.table_name} value={t.table_name}>
                  {t.table_name} ({t.column_count})
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="card">
        <h3>{domain === "source" ? "Source" : "Target"} Table List</h3>
        <div className="muted">Count: {filtered.length}</div>
        <DataTable columns={["table_name", "column_count"]} rows={filtered as any[]} emptyLabel="No tables match filter." />
      </section>

      <section className="card">
        <h3>Field Definitions: {selectedTable || "-"}</h3>
        <DataTable
          columns={selectedFields.length ? Object.keys(selectedFields[0]) : ["field_name"]}
          rows={selectedFields}
          emptyLabel="Select a table to view fields."
        />
      </section>
    </main>
  );
}
