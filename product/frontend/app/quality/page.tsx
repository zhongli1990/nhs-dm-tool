"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../../lib/api";
import DataTable from "../../components/DataTable";

type KpiConfig = {
  id: string;
  label: string;
  threshold: number;
  direction: "max" | "min";
  enabled: boolean;
  format?: "int" | "pct";
};

type KpiValue = {
  id: string;
  label: string;
  value: number;
  threshold: number;
  direction: "max" | "min";
  enabled: boolean;
  format?: "int" | "pct";
};

const STORAGE_KEY = "dm_quality_kpi_config_v1";

const DEFAULT_KPIS: KpiConfig[] = [
  { id: "error_count", label: "DQ Errors", threshold: 0, direction: "max", enabled: true, format: "int" },
  { id: "warning_count", label: "DQ Warnings", threshold: 20, direction: "max", enabled: true, format: "int" },
  { id: "crosswalk_rejects", label: "Crosswalk Rejects", threshold: 0, direction: "max", enabled: true, format: "int" },
  { id: "population_ratio", label: "Population Ratio", threshold: 0.55, direction: "min", enabled: true, format: "pct" },
  { id: "tables_written", label: "Tables Written", threshold: 38, direction: "min", enabled: true, format: "int" },
  { id: "unresolved_mapping", label: "Unresolved Mapping", threshold: 10, direction: "max", enabled: true, format: "int" },
];

function fmtValue(value: number, format: "int" | "pct" = "int") {
  if (format === "pct") return `${(value * 100).toFixed(2)}%`;
  return String(Math.round(value));
}

function passFail(value: number, threshold: number, direction: "max" | "min") {
  return direction === "max" ? value <= threshold : value >= threshold;
}

export default function QualityPage() {
  const [latest, setLatest] = useState<any>({});
  const [enterpriseIssues, setEnterpriseIssues] = useState<any[]>([]);
  const [contractIssues, setContractIssues] = useState<any[]>([]);
  const [rejects, setRejects] = useState<any[]>([]);
  const [kpis, setKpis] = useState<KpiConfig[]>(DEFAULT_KPIS);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        setKpis(JSON.parse(stored));
      } catch {
        setKpis(DEFAULT_KPIS);
      }
    }
  }, []);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(kpis));
  }, [kpis]);

  useEffect(() => {
    async function load() {
      const [runs, ent, con, rej] = await Promise.all([
        apiGet<any>("/api/runs/latest"),
        apiGet<{ rows: any[] }>("/api/quality/issues?kind=enterprise"),
        apiGet<{ rows: any[] }>("/api/quality/issues?kind=contract"),
        apiGet<{ rows: any[] }>("/api/rejects/crosswalk"),
      ]);
      setLatest(runs || {});
      setEnterpriseIssues(ent.rows || []);
      setContractIssues(con.rows || []);
      setRejects(rej.rows || []);
    }
    load().catch(() => undefined);
  }, []);

  const values = useMemo<KpiValue[]>(() => {
    const quality = latest.enterprise_quality || {};
    const contract = latest.contract_migration || {};
    const release = latest.release_gates || {};
    const unresolvedCheck = (release.checks || []).find((c: any) => c.gate === "UNRESOLVED_MAPPING_THRESHOLD");
    const unresolved = Number(unresolvedCheck?.actual ?? 0);
    const map: Record<string, number> = {
      error_count: Number(quality.severity_counts?.ERROR ?? 0),
      warning_count: Number(quality.severity_counts?.WARN ?? 0) + Number(contract.issue_counts?.WARN ?? 0),
      crosswalk_rejects: Number(contract.crosswalk_reject_count ?? rejects.length ?? 0),
      population_ratio: Number(contract.overall_column_population_ratio ?? 0),
      tables_written: Number(contract.tables_written ?? 0),
      unresolved_mapping: unresolved,
    };
    return kpis.map((k) => ({
      ...k,
      value: map[k.id] ?? 0,
    }));
  }, [kpis, latest, rejects.length]);

  const enabledValues = values.filter((v) => v.enabled);

  const issueCategories = useMemo(() => {
    const combined = [...enterpriseIssues, ...contractIssues];
    const counts: Record<string, number> = {};
    for (const i of combined) {
      const cat = i.category || "UNCLASSIFIED";
      counts[cat] = (counts[cat] || 0) + 1;
    }
    return Object.entries(counts)
      .map(([category, count]) => ({ category, count }))
      .sort((a, b) => b.count - a.count);
  }, [enterpriseIssues, contractIssues]);

  const commonConcerns = useMemo(() => {
    const categories = new Set(issueCategories.map((c) => c.category));
    const concerns = [
      { concern: "Patient identity integrity (NHS/MRN)", signal: "Use enterprise identity checks", status: enterpriseIssues.length ? "Review" : "Clear" },
      { concern: "Source base unresolved tables", signal: String(contractIssues.filter((i) => i.category === "SOURCE_BASE_UNRESOLVED").length), status: categories.has("SOURCE_BASE_UNRESOLVED") ? "Attention" : "Clear" },
      { concern: "Crosswalk translation failures", signal: String(rejects.length), status: rejects.length > 0 ? "Attention" : "Clear" },
      { concern: "Mapping unresolved risk", signal: String(values.find((v) => v.id === "unresolved_mapping")?.value ?? 0), status: (values.find((v) => v.id === "unresolved_mapping")?.value ?? 0) > 0 ? "Review" : "Clear" },
      { concern: "Population completeness", signal: fmtValue(values.find((v) => v.id === "population_ratio")?.value ?? 0, "pct"), status: (values.find((v) => v.id === "population_ratio")?.value ?? 0) < 0.55 ? "Attention" : "Clear" },
    ];
    return concerns;
  }, [issueCategories, enterpriseIssues.length, contractIssues, rejects.length, values]);

  function updateKpi(id: string, patch: Partial<KpiConfig>) {
    setKpis((prev) => prev.map((k) => (k.id === id ? { ...k, ...patch } : k)));
  }

  return (
    <main className="grid">
      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Data Quality Command Centre</h3>
        <div className="muted">Configurable KPI cards and quality issue analytics for NHS PAS/EPR migrations.</div>
      </section>

      {enabledValues.map((k) => {
        const ok = passFail(k.value, k.threshold, k.direction);
        const pct = k.direction === "max" ? Math.min(100, (k.threshold === 0 ? (k.value === 0 ? 100 : 0) : (k.threshold / Math.max(k.value, 0.0001)) * 100)) : Math.min(100, (k.value / Math.max(k.threshold, 0.0001)) * 100);
        return (
          <section key={k.id} className="card">
            <div className="muted">{k.label}</div>
            <div className={`kpi ${ok ? "status-pass" : "status-fail"}`}>{fmtValue(k.value, k.format)}</div>
            <div className="muted">
              Threshold: {k.direction === "max" ? "<= " : ">= "}
              {fmtValue(k.threshold, k.format)}
            </div>
            <div className="kpi-bar">
              <div className={ok ? "kpi-fill pass" : "kpi-fill fail"} style={{ width: `${Math.max(4, pct)}%` }} />
            </div>
          </section>
        );
      })}

      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>KPI Configuration</h3>
        <div className="muted">Enable/disable KPIs and set local thresholds for operational governance.</div>
        <DataTable
          columns={["kpi", "enabled", "direction", "threshold", "current"]}
          rows={values.map((k) => ({
            kpi: k.label,
            enabled: (
              <input
                type="checkbox"
                checked={k.enabled}
                onChange={(e) => updateKpi(k.id, { enabled: e.target.checked })}
              />
            ),
            direction: (
              <select value={k.direction} onChange={(e) => updateKpi(k.id, { direction: e.target.value as "max" | "min" })}>
                <option value="max">max</option>
                <option value="min">min</option>
              </select>
            ),
            threshold: (
              <input
                type="number"
                step={k.format === "pct" ? "0.01" : "1"}
                value={k.threshold}
                onChange={(e) => updateKpi(k.id, { threshold: Number(e.target.value || 0) })}
              />
            ),
            current: fmtValue(k.value, k.format),
          }))}
          emptyLabel="No KPI definitions."
        />
      </section>

      <section className="card">
        <h3>Issue Category Graph</h3>
        <div className="muted">Contract + enterprise issue distribution.</div>
        <div style={{ marginTop: 8 }}>
          {issueCategories.length === 0 ? (
            <div className="muted">No issues reported.</div>
          ) : (
            issueCategories.slice(0, 10).map((c) => {
              const max = Math.max(...issueCategories.map((x) => x.count), 1);
              const w = (c.count / max) * 100;
              return (
                <div key={c.category} style={{ marginBottom: 8 }}>
                  <div className="muted">{c.category} ({c.count})</div>
                  <div className="kpi-bar">
                    <div className="kpi-fill warn" style={{ width: `${Math.max(6, w)}%` }} />
                  </div>
                </div>
              );
            })
          )}
        </div>
      </section>

      <section className="card">
        <h3>Common NHS PAS/EPR DQ Concerns</h3>
        <DataTable columns={["concern", "signal", "status"]} rows={commonConcerns} />
      </section>

      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Issue Explorer</h3>
        <DataTable
          columns={["severity", "category", "table_name", "field_name", "record_id", "message"]}
          rows={[...enterpriseIssues, ...contractIssues].slice(0, 1000)}
          emptyLabel="No quality issues."
        />
        <div className="muted">Showing up to 1000 issue rows.</div>
      </section>
    </main>
  );
}
