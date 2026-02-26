"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../../lib/api";
import DataTable from "../../components/DataTable";
import SectionTabs from "../../components/SectionTabs";

const API_BASE = process.env.NEXT_PUBLIC_DM_API_BASE || "http://localhost:8099";

export default function MappingsPage() {
  const [summary, setSummary] = useState<any>({});
  const [rows, setRows] = useState<any[]>([]);
  const [workbench, setWorkbench] = useState<any[]>([]);
  const [view, setView] = useState<"summary" | "rows" | "workbench">("summary");
  const [targetTable, setTargetTable] = useState("");
  const [mappingClass, setMappingClass] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  async function loadContract() {
    const payload = await apiGet<{ summary: any; rows: any[] }>("/api/mappings/contract");
    setSummary(payload.summary || {});
    setRows(payload.rows || []);
  }

  async function loadFilteredRows() {
    setLoading(true);
    const q = new URLSearchParams();
    if (targetTable) q.set("target_table", targetTable);
    if (mappingClass) q.set("mapping_class", mappingClass);
    q.set("limit", "5000");
    const payload = await apiGet<{ rows: any[] }>(`/api/mappings/contract/query?${q.toString()}`);
    setRows(payload.rows || []);
    setLoading(false);
  }

  async function loadWorkbench() {
    const q = new URLSearchParams();
    if (targetTable) q.set("target_table", targetTable);
    if (mappingClass) q.set("mapping_class", mappingClass);
    if (statusFilter) q.set("status", statusFilter);
    q.set("limit", "10000");
    const payload = await apiGet<{ rows: any[] }>(`/api/mappings/workbench?${q.toString()}`);
    setWorkbench(payload.rows || []);
  }

  useEffect(() => {
    loadContract().catch(() => undefined);
    loadWorkbench().catch(() => undefined);
  }, []);

  const mappingClasses = Object.keys(summary.mapping_class_counts || {});
  const tableOptions = useMemo(() => Array.from(new Set(workbench.map((r) => r.target_table).filter(Boolean))).sort(), [workbench]);

  async function updateRow(workbenchId: string, patch: any) {
    setMessage("");
    const res = await fetch(`${API_BASE}/api/mappings/workbench/upsert`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workbench_id: workbenchId, updated_by: "ui_editor", ...patch }),
    });
    if (!res.ok) {
      const p = await res.json().catch(() => ({}));
      throw new Error(p?.detail || "update failed");
    }
    await loadWorkbench();
    setMessage(`Updated ${workbenchId}`);
  }

  async function transitionRow(workbenchId: string, status: string) {
    setMessage("");
    const res = await fetch(`${API_BASE}/api/mappings/workbench/transition`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workbench_id: workbenchId, status, updated_by: "ui_approver" }),
    });
    if (!res.ok) {
      const p = await res.json().catch(() => ({}));
      throw new Error(p?.detail || "transition failed");
    }
    await loadWorkbench();
    setMessage(`Status changed to ${status} for ${workbenchId}`);
  }

  return (
    <main className="grid">
      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Mapping Contract Workbench</h3>
        <div className="muted">Edit, review and approve mapping rows with lifecycle-governed status transitions.</div>
        <SectionTabs
          tabs={[
            { id: "summary", label: "Summary" },
            { id: "rows", label: "Contract Rows" },
            { id: "workbench", label: "Edit & Approve" },
          ]}
          active={view}
          onChange={(id) => setView(id as "summary" | "rows" | "workbench")}
        />
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
            Workbench status
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All</option>
              <option value="DRAFT">DRAFT</option>
              <option value="IN_REVIEW">IN_REVIEW</option>
              <option value="APPROVED">APPROVED</option>
              <option value="REJECTED">REJECTED</option>
            </select>
          </label>
          <label>
            Actions
            <button className="primary" type="button" onClick={() => Promise.all([loadFilteredRows(), loadWorkbench()]).catch(() => undefined)} disabled={loading}>
              {loading ? "Loading..." : "Apply Filter"}
            </button>
          </label>
        </div>
        {message ? <div className="status-pass" style={{ marginTop: 8 }}>{message}</div> : null}
      </section>

      {view === "summary" ? (
        <section className="card">
          <h3>Mapping Class Summary</h3>
          <DataTable columns={["class", "count"]} rows={Object.entries(summary.mapping_class_counts || {}).map(([k, v]) => ({ class: k, count: String(v) }))} />
        </section>
      ) : null}

      {view === "rows" ? (
        <section className="card" style={{ gridColumn: "1 / -1" }}>
          <h3>Contract Rows</h3>
          <DataTable
            columns={rows.length ? ["target_table", "target_field", "mapping_class", "primary_source_table", "primary_source_field", "transformation_rule"] : ["target_table"]}
            rows={rows.slice(0, 1200)}
            emptyLabel="No mapping rows."
          />
          <div className="muted">Showing up to 1200 rows in UI.</div>
        </section>
      ) : null}

      {view === "workbench" ? (
        <section className="card" style={{ gridColumn: "1 / -1" }}>
          <h3>Edit and Approve Workbench</h3>
          <DataTable
            columns={[
              "workbench_id",
              "mapping_class",
              "primary_source_table",
              "primary_source_field",
              "transformation_rule",
              "status",
              "actions",
            ]}
            rows={workbench.slice(0, 500).map((r) => ({
              workbench_id: r.workbench_id,
              mapping_class: (
                <input
                  defaultValue={r.mapping_class || ""}
                  onBlur={(e) => updateRow(r.workbench_id, { mapping_class: e.target.value }).catch((ex) => setMessage(ex.message))}
                />
              ),
              primary_source_table: (
                <input
                  defaultValue={r.primary_source_table || ""}
                  onBlur={(e) => updateRow(r.workbench_id, { primary_source_table: e.target.value }).catch((ex) => setMessage(ex.message))}
                />
              ),
              primary_source_field: (
                <input
                  defaultValue={r.primary_source_field || ""}
                  onBlur={(e) => updateRow(r.workbench_id, { primary_source_field: e.target.value }).catch((ex) => setMessage(ex.message))}
                />
              ),
              transformation_rule: (
                <input
                  defaultValue={r.transformation_rule || ""}
                  onBlur={(e) => updateRow(r.workbench_id, { transformation_rule: e.target.value }).catch((ex) => setMessage(ex.message))}
                />
              ),
              status: <span className="pill">{r.status}</span>,
              actions: (
                <div style={{ display: "flex", gap: 6 }}>
                  <button type="button" onClick={() => transitionRow(r.workbench_id, "IN_REVIEW").catch((ex) => setMessage(ex.message))}>
                    Review
                  </button>
                  <button type="button" onClick={() => transitionRow(r.workbench_id, "APPROVED").catch((ex) => setMessage(ex.message))}>
                    Approve
                  </button>
                  <button type="button" onClick={() => transitionRow(r.workbench_id, "REJECTED").catch((ex) => setMessage(ex.message))}>
                    Reject
                  </button>
                </div>
              ),
            }))}
            emptyLabel="No workbench rows."
          />
          <div className="muted">Showing up to 500 editable rows.</div>
        </section>
      ) : null}
    </main>
  );
}
