"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPostJson } from "../../lib/api";
import DataTable from "../../components/DataTable";
import SectionTabs from "../../components/SectionTabs";

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
  const [contractPage, setContractPage] = useState(1);
  const [contractPageSize, setContractPageSize] = useState(200);
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [bulkStatus, setBulkStatus] = useState("IN_REVIEW");
  const [bulkField, setBulkField] = useState("mapping_class");
  const [bulkValue, setBulkValue] = useState("");
  const [bulkBusy, setBulkBusy] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(200);
  const [totalWorkbenchRows, setTotalWorkbenchRows] = useState(0);

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
    q.set("offset", String((page - 1) * pageSize));
    q.set("limit", String(pageSize));
    const payload = await apiGet<{ rows: any[]; row_count: number }>(`/api/mappings/workbench?${q.toString()}`);
    setWorkbench(payload.rows || []);
    setTotalWorkbenchRows(Number(payload.row_count || 0));
    setSelected({});
  }

  async function applyFilters() {
    setPage(1);
    setContractPage(1);
    setLoading(true);
    try {
      await loadFilteredRows();
      const q = new URLSearchParams();
      if (targetTable) q.set("target_table", targetTable);
      if (mappingClass) q.set("mapping_class", mappingClass);
      if (statusFilter) q.set("status", statusFilter);
      q.set("offset", "0");
      q.set("limit", String(pageSize));
      const payload = await apiGet<{ rows: any[]; row_count: number }>(`/api/mappings/workbench?${q.toString()}`);
      setWorkbench(payload.rows || []);
      setTotalWorkbenchRows(Number(payload.row_count || 0));
      setSelected({});
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadContract().catch(() => undefined);
    loadWorkbench().catch(() => undefined);
  }, []);

  useEffect(() => {
    loadWorkbench().catch(() => undefined);
  }, [page, pageSize]);

  const mappingClasses = Object.keys(summary.mapping_class_counts || {});
  const tableOptions = useMemo(() => {
    const wb = workbench.map((r) => r.target_table).filter(Boolean);
    const contractTables = rows.map((r) => r.target_table).filter(Boolean);
    return Array.from(new Set([...wb, ...contractTables])).sort();
  }, [workbench, rows]);
  const visibleWorkbench = useMemo(() => workbench, [workbench]);
  const selectedIds = useMemo(() => Object.keys(selected).filter((k) => selected[k]), [selected]);
  const allVisibleSelected = useMemo(() => visibleWorkbench.length > 0 && visibleWorkbench.every((r) => selected[r.workbench_id]), [visibleWorkbench, selected]);
  const totalPages = useMemo(() => Math.max(1, Math.ceil(totalWorkbenchRows / Math.max(pageSize, 1))), [totalWorkbenchRows, pageSize]);
  const totalContractPages = useMemo(() => Math.max(1, Math.ceil(rows.length / Math.max(contractPageSize, 1))), [rows.length, contractPageSize]);
  const contractRowsPage = useMemo(() => {
    const start = (contractPage - 1) * contractPageSize;
    return rows.slice(start, start + contractPageSize);
  }, [rows, contractPage, contractPageSize]);

  async function updateRow(workbenchId: string, patch: any) {
    setMessage("");
    await apiPostJson("/api/mappings/workbench/upsert", {
      workbench_id: workbenchId,
      updated_by: "ui_editor",
      ...patch,
    });
    await loadWorkbench();
    setMessage(`Updated ${workbenchId}`);
  }

  async function transitionRow(workbenchId: string, status: string) {
    setMessage("");
    await apiPostJson("/api/mappings/workbench/transition", {
      workbench_id: workbenchId,
      status,
      updated_by: "ui_approver",
    });
    await loadWorkbench();
    setMessage(`Status changed to ${status} for ${workbenchId}`);
  }

  async function runBulkTransition() {
    if (!selectedIds.length) {
      setMessage("Select rows first.");
      return;
    }
    setBulkBusy(true);
    setMessage("");
    try {
      await Promise.all(
        selectedIds.map((id) =>
          apiPostJson("/api/mappings/workbench/transition", {
            workbench_id: id,
            status: bulkStatus,
            updated_by: "ui_approver_bulk",
          })
        )
      );
      await loadWorkbench();
      setMessage(`Updated ${selectedIds.length} row(s) to ${bulkStatus}.`);
    } catch (ex: any) {
      setMessage(ex?.message || "Bulk status update failed.");
    } finally {
      setBulkBusy(false);
    }
  }

  async function runBulkFieldUpdate() {
    if (!selectedIds.length) {
      setMessage("Select rows first.");
      return;
    }
    setBulkBusy(true);
    setMessage("");
    try {
      const patch: Record<string, string> = { [bulkField]: bulkValue };
      await Promise.all(
        selectedIds.map((id) =>
          apiPostJson("/api/mappings/workbench/upsert", {
            workbench_id: id,
            updated_by: "ui_editor_bulk",
            ...patch,
          })
        )
      );
      await loadWorkbench();
      setMessage(`Updated ${selectedIds.length} row(s): ${bulkField}.`);
    } catch (ex: any) {
      setMessage(ex?.message || "Bulk field update failed.");
    } finally {
      setBulkBusy(false);
    }
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
            <input
              value={targetTable}
              onChange={(e) => setTargetTable(e.target.value)}
              list="target-table-options"
              placeholder="All / type keyword or pick table"
            />
            <datalist id="target-table-options">
              {tableOptions.map((t) => (
                <option key={t} value={t} />
              ))}
            </datalist>
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
            <button className="primary" type="button" onClick={() => applyFilters().catch(() => undefined)} disabled={loading}>
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
          <div className="controls">
            <label>
              Page size
              <select value={contractPageSize} onChange={(e) => { setContractPage(1); setContractPageSize(Number(e.target.value)); }}>
                <option value={100}>100</option>
                <option value={200}>200</option>
                <option value={500}>500</option>
                <option value={1000}>1000</option>
              </select>
            </label>
            <label>
              Navigation
              <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                <button type="button" disabled={contractPage <= 1} onClick={() => setContractPage((p) => Math.max(1, p - 1))}>
                  Page up
                </button>
                <button type="button" disabled={contractPage >= totalContractPages} onClick={() => setContractPage((p) => Math.min(totalContractPages, p + 1))}>
                  Page down
                </button>
              </div>
            </label>
          </div>
          <DataTable
            columns={rows.length ? ["id", "target_table", "target_field", "mapping_class", "primary_source_table", "primary_source_field", "transformation_rule"] : ["target_table"]}
            rows={contractRowsPage.map((r, idx) => ({
              id: String((contractPage - 1) * contractPageSize + idx + 1),
              ...r,
            }))}
            emptyLabel="No mapping rows."
          />
          <div className="muted">Page {contractPage} / {totalContractPages} | Total {rows.length} contract rows.</div>
        </section>
      ) : null}

      {view === "workbench" ? (
        <section className="card" style={{ gridColumn: "1 / -1" }}>
          <h3>Edit and Approve Workbench</h3>
          <div className="controls">
            <label>
              Bulk status
              <select value={bulkStatus} onChange={(e) => setBulkStatus(e.target.value)}>
                <option value="DRAFT">DRAFT</option>
                <option value="IN_REVIEW">IN_REVIEW</option>
                <option value="APPROVED">APPROVED</option>
                <option value="REJECTED">REJECTED</option>
              </select>
            </label>
            <label>
              Bulk field
              <select value={bulkField} onChange={(e) => setBulkField(e.target.value)}>
                <option value="mapping_class">mapping_class</option>
                <option value="primary_source_table">primary_source_table</option>
                <option value="primary_source_field">primary_source_field</option>
                <option value="transformation_rule">transformation_rule</option>
              </select>
            </label>
            <label>
              Bulk value
              <input value={bulkValue} onChange={(e) => setBulkValue(e.target.value)} placeholder="Value to set on selected rows" />
            </label>
            <label>
              Bulk actions
              <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                <button type="button" className="primary" disabled={bulkBusy || !selectedIds.length} onClick={() => runBulkTransition().catch(() => undefined)}>
                  Set status ({selectedIds.length})
                </button>
                <button type="button" disabled={bulkBusy || !selectedIds.length} onClick={() => runBulkFieldUpdate().catch(() => undefined)}>
                  Apply field ({selectedIds.length})
                </button>
              </div>
            </label>
            <label>
              Page size
              <select value={pageSize} onChange={(e) => { setPage(1); setPageSize(Number(e.target.value)); }}>
                <option value={100}>100</option>
                <option value={200}>200</option>
                <option value={500}>500</option>
                <option value={1000}>1000</option>
              </select>
            </label>
          </div>
          <DataTable
            columns={[
              "id",
              "select",
              "workbench_id",
              "mapping_class",
              "primary_source_table",
              "primary_source_field",
              "transformation_rule",
              "status",
              "actions",
            ]}
            rows={visibleWorkbench.map((r, idx) => ({
              id: String((page - 1) * pageSize + idx + 1),
              select: (
                <input
                  type="checkbox"
                  checked={!!selected[r.workbench_id]}
                  onChange={(e) => setSelected((prev) => ({ ...prev, [r.workbench_id]: e.target.checked }))}
                />
              ),
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
          <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
            <button
              type="button"
              onClick={() =>
                setSelected((prev) => {
                  if (allVisibleSelected) return {};
                  const next: Record<string, boolean> = { ...prev };
                  for (const r of visibleWorkbench) next[r.workbench_id] = true;
                  return next;
                })
              }
            >
              {allVisibleSelected ? "Clear visible selection" : "Select all visible"}
            </button>
            <button type="button" onClick={() => setSelected({})}>
              Clear all
            </button>
            <button type="button" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
              Page up
            </button>
            <button type="button" disabled={page >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>
              Page down
            </button>
            <span className="muted" style={{ alignSelf: "center" }}>
              Page {page} / {totalPages} | Total {totalWorkbenchRows}
            </span>
          </div>
          <div className="muted">Server-side pagination enabled for enterprise-scale workbench editing. Avoid unlimited full-table rendering for performance and stability.</div>
        </section>
      ) : null}
    </main>
  );
}

