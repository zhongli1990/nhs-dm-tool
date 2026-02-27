"use client";

import { useEffect, useMemo, useState } from "react";
import DataTable from "../../components/DataTable";
import { apiGet, apiPost, apiPostJson } from "../../lib/api";

type KpiConfig = {
  id: string;
  label: string;
  threshold: number;
  direction: "max" | "min";
  enabled: boolean;
  format?: "int" | "pct";
};

type QualityPoint = {
  ts_utc: string;
  error_count: number;
  warning_count: number;
  crosswalk_rejects: number;
  population_ratio: number;
  tables_written: number;
  unresolved_mapping: number;
  release_status: string;
};

type WidgetRow = {
  id: string;
  label: string;
  value: number;
  threshold: number;
  direction: "max" | "min";
  format: "int" | "pct";
  trend: number[];
  percentage_of_threshold: number;
  source: string;
  enabled?: boolean;
};

const TABS = ["dashboard", "kpi_widgets", "issue_explorer"] as const;
type TabKey = (typeof TABS)[number];

function fmtValue(value: number, format: "int" | "pct" = "int") {
  return format === "pct" ? `${(value * 100).toFixed(2)}%` : String(Math.round(value));
}

function passFail(value: number, threshold: number, direction: "max" | "min") {
  return direction === "max" ? value <= threshold : value >= threshold;
}

function Sparkline({ values }: { values: number[] }) {
  if (!values.length) return <span className="muted">-</span>;
  const w = 120;
  const h = 26;
  const pad = 2;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const x = (i: number) => pad + (i * (w - pad * 2)) / Math.max(values.length - 1, 1);
  const y = (v: number) => {
    const ratio = max === min ? 0.5 : (v - min) / (max - min);
    return h - pad - ratio * (h - pad * 2);
  };
  const d = values.map((v, i) => `${i === 0 ? "M" : "L"}${x(i)},${y(v)}`).join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`}>
      <path d={d} className="sparkline-path" />
    </svg>
  );
}

function Gauge({ ratio }: { ratio: number }) {
  const bounded = Math.max(0, Math.min(1.2, ratio));
  const width = `${Math.max(3, bounded * 100)}%`;
  return (
    <div className="kpi-bar">
      <div className={bounded <= 1 ? "kpi-fill pass" : "kpi-fill fail"} style={{ width }} />
    </div>
  );
}

export default function QualityPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("dashboard");
  const [latest, setLatest] = useState<any>({});
  const [enterpriseIssues, setEnterpriseIssues] = useState<any[]>([]);
  const [contractIssues, setContractIssues] = useState<any[]>([]);
  const [rejects, setRejects] = useState<any[]>([]);
  const [kpis, setKpis] = useState<KpiConfig[]>([]);
  const [trendPoints, setTrendPoints] = useState<QualityPoint[]>([]);
  const [widgetRows, setWidgetRows] = useState<WidgetRow[]>([]);
  const [weeks, setWeeks] = useState(12);
  const [refreshSec, setRefreshSec] = useState(0);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function loadAll(currentWeeks = weeks) {
    const [runs, ent, con, rej, trends, cfg, widgets] = await Promise.all([
      apiGet<any>("/api/runs/latest"),
      apiGet<{ rows: any[] }>("/api/quality/issues?kind=enterprise"),
      apiGet<{ rows: any[] }>("/api/quality/issues?kind=contract"),
      apiGet<{ rows: any[] }>("/api/rejects/crosswalk"),
      apiGet<{ points: QualityPoint[] }>(`/api/quality/trends?limit=${Math.max(20, currentWeeks * 2)}`),
      apiGet<{ rows: KpiConfig[] }>("/api/quality/kpis"),
      apiGet<{ rows: WidgetRow[] }>(`/api/quality/kpi-widgets?weeks=${currentWeeks}`),
    ]);
    setLatest(runs || {});
    setEnterpriseIssues(ent.rows || []);
    setContractIssues(con.rows || []);
    setRejects(rej.rows || []);
    setTrendPoints(trends.points || []);
    setKpis(cfg.rows || []);
    setWidgetRows(widgets.rows || []);
  }

  useEffect(() => {
    loadAll().catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!refreshSec) return;
    const timer = setInterval(() => {
      loadAll().catch(() => undefined);
    }, refreshSec * 1000);
    return () => clearInterval(timer);
  }, [refreshSec, weeks]);

  const current = trendPoints.length ? trendPoints[trendPoints.length - 1] : null;

  const kpiValues = useMemo(() => {
    const quality = latest.enterprise_quality || {};
    const contract = latest.contract_migration || {};
    const release = latest.release_gates || {};
    const unresolvedCheck = (release.checks || []).find((c: any) => c.gate === "UNRESOLVED_MAPPING_THRESHOLD");
    const unresolved = Number(unresolvedCheck?.actual ?? 0);
    const map: Record<string, number> = {
      error_count: Number(quality.severity_counts?.ERROR ?? current?.error_count ?? 0),
      warning_count: Number(quality.severity_counts?.WARN ?? 0) + Number(contract.issue_counts?.WARN ?? current?.warning_count ?? 0),
      crosswalk_rejects: Number(contract.crosswalk_reject_count ?? current?.crosswalk_rejects ?? rejects.length ?? 0),
      population_ratio: Number(contract.overall_column_population_ratio ?? current?.population_ratio ?? 0),
      tables_written: Number(contract.tables_written ?? current?.tables_written ?? 0),
      unresolved_mapping: unresolved || Number(current?.unresolved_mapping ?? 0),
    };
    return kpis.map((k) => ({ ...k, value: map[k.id] ?? 0 }));
  }, [kpis, latest, rejects.length, current]);

  const issueByTable = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const row of [...enterpriseIssues, ...contractIssues]) {
      const t = String(row.table_name || "UNSPECIFIED");
      counts[t] = (counts[t] || 0) + 1;
    }
    return Object.entries(counts)
      .map(([table, count]) => ({ table, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);
  }, [enterpriseIssues, contractIssues]);

  const sourceWidgets = widgetRows.filter((r) => r.source === "source_runtime_profile");
  const gateWidgets = widgetRows.filter((r) => r.source === "migration_gate" && r.enabled !== false);

  async function saveKpis() {
    setBusy(true);
    setMsg("");
    try {
      await apiPostJson("/api/quality/kpis", { rows: kpis });
      setMsg("KPI configuration saved");
      await loadAll();
    } catch (e: any) {
      setMsg(e?.message || "Save failed");
    } finally {
      setBusy(false);
      setTimeout(() => setMsg(""), 3000);
    }
  }

  async function seedDemo() {
    setBusy(true);
    setMsg("");
    try {
      await apiPost(`/api/quality/trends/seed?weeks=${weeks}&replace=true`);
      setMsg(`Seeded ${weeks} weeks of demo quality trend data`);
      await loadAll(weeks);
    } catch (e: any) {
      setMsg(e?.message || "Seed failed");
    } finally {
      setBusy(false);
      setTimeout(() => setMsg(""), 3000);
    }
  }

  function patchKpi(id: string, patch: Partial<KpiConfig>) {
    setKpis((prev) => prev.map((k) => (k.id === id ? { ...k, ...patch } : k)));
  }

  return (
    <main className="grid quality-grid">
      <section className="card quality-hero" style={{ gridColumn: "1 / -1" }}>
        <h3>Data Quality Command Centre</h3>
        <div className="muted">Mission-critical quality governance for PAS/EPR migration readiness.</div>
        <div className="controls">
          <label>
            Weeks window
            <select value={weeks} onChange={(e) => setWeeks(Number(e.target.value))}>
              <option value={8}>8</option>
              <option value={12}>12</option>
              <option value={16}>16</option>
              <option value={26}>26</option>
            </select>
          </label>
          <label>
            Auto refresh
            <select value={refreshSec} onChange={(e) => setRefreshSec(Number(e.target.value))}>
              <option value={0}>Off</option>
              <option value={15}>15 sec</option>
              <option value={30}>30 sec</option>
              <option value={60}>60 sec</option>
            </select>
          </label>
          <label>
            Actions
            <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
              <button className="primary" disabled={busy} onClick={() => loadAll(weeks).catch(() => undefined)}>Refresh now</button>
              <button disabled={busy} onClick={() => seedDemo().catch(() => undefined)}>Seed demo trend</button>
            </div>
          </label>
        </div>
        {msg ? <div className="muted" style={{ marginTop: 8 }}>{msg}</div> : null}
      </section>

      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <div className="section-tabs">
          <button className={`section-tab ${activeTab === "dashboard" ? "active" : ""}`} onClick={() => setActiveTab("dashboard")}>Dashboard</button>
          <button className={`section-tab ${activeTab === "kpi_widgets" ? "active" : ""}`} onClick={() => setActiveTab("kpi_widgets")}>KPI Widgets</button>
          <button className={`section-tab ${activeTab === "issue_explorer" ? "active" : ""}`} onClick={() => setActiveTab("issue_explorer")}>Issue Explorer</button>
        </div>

        {activeTab === "dashboard" ? (
          <div className="grid">
            {kpiValues.filter((k) => k.enabled).map((k) => {
              const ok = passFail(k.value, k.threshold, k.direction);
              return (
                <section key={k.id} className="card kpi-card">
                  <div className="muted">{k.label}</div>
                  <div className={`kpi ${ok ? "status-pass" : "status-fail"}`}>{fmtValue(k.value, k.format)}</div>
                  <div className="muted">Threshold {k.direction === "max" ? "<=" : ">="} {fmtValue(k.threshold, k.format)}</div>
                </section>
              );
            })}

            <section className="card" style={{ gridColumn: "1 / -1" }}>
              <h3>Top Failing Tables</h3>
              {issueByTable.length === 0 ? <div className="muted">No issues in latest reports.</div> : issueByTable.map((t) => {
                const max = Math.max(...issueByTable.map((x) => x.count), 1);
                return (
                  <div className="bar-row" key={t.table}>
                    <div className="muted">{t.table} ({t.count})</div>
                    <div className="kpi-bar"><div className="kpi-fill fail" style={{ width: `${Math.max(5, (t.count / max) * 100)}%` }} /></div>
                  </div>
                );
              })}
            </section>
          </div>
        ) : null}

        {activeTab === "kpi_widgets" ? (
          <div className="grid">
            <section className="card" style={{ gridColumn: "1 / -1" }}>
              <h3>Source Runtime KPI Widgets</h3>
              <div className="muted">Profile-driven checks similar to operational data quality scorecards.</div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>KPI</th>
                      <th>{weeks} weeks</th>
                      <th>This Week</th>
                      <th>Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sourceWidgets.map((r) => (
                      <tr key={r.id}>
                        <td>{r.label}</td>
                        <td><Sparkline values={r.trend} /></td>
                        <td className={passFail(r.value, r.threshold, r.direction) ? "status-pass" : "status-fail"}>{fmtValue(r.value, r.format)}</td>
                        <td><Gauge ratio={r.percentage_of_threshold} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="card" style={{ gridColumn: "1 / -1" }}>
              <h3>Migration Gate KPI Widgets</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>KPI</th>
                      <th>{weeks} weeks</th>
                      <th>This Week</th>
                      <th>Percentage</th>
                    </tr>
                  </thead>
                  <tbody>
                    {gateWidgets.map((r) => (
                      <tr key={r.id}>
                        <td>{r.label}</td>
                        <td><Sparkline values={r.trend} /></td>
                        <td className={passFail(r.value, r.threshold, r.direction) ? "status-pass" : "status-fail"}>{fmtValue(r.value, r.format)}</td>
                        <td><Gauge ratio={r.percentage_of_threshold} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="card" style={{ gridColumn: "1 / -1" }}>
              <h3>KPI Configuration</h3>
              <div className="quality-actions">
                <button className="primary" disabled={busy} onClick={() => saveKpis().catch(() => undefined)}>Save KPI Config</button>
              </div>
              <DataTable
                columns={["kpi", "enabled", "direction", "threshold", "format"]}
                rows={kpis.map((k) => ({
                  kpi: k.label,
                  enabled: <input type="checkbox" checked={k.enabled} onChange={(e) => patchKpi(k.id, { enabled: e.target.checked })} />,
                  direction: (
                    <select value={k.direction} onChange={(e) => patchKpi(k.id, { direction: e.target.value as "max" | "min" })}>
                      <option value="max">max</option>
                      <option value="min">min</option>
                    </select>
                  ),
                  threshold: (
                    <input type="number" step={k.format === "pct" ? "0.01" : "1"} value={k.threshold} onChange={(e) => patchKpi(k.id, { threshold: Number(e.target.value || 0) })} />
                  ),
                  format: (
                    <select value={k.format || "int"} onChange={(e) => patchKpi(k.id, { format: e.target.value as "int" | "pct" })}>
                      <option value="int">int</option>
                      <option value="pct">pct</option>
                    </select>
                  ),
                }))}
              />
            </section>
          </div>
        ) : null}

        {activeTab === "issue_explorer" ? (
          <section className="card">
            <h3>Issue Explorer</h3>
            <DataTable
              columns={["severity", "category", "table_name", "field_name", "record_id", "message"]}
              rows={[...enterpriseIssues, ...contractIssues].slice(0, 1000)}
              emptyLabel="No quality issues."
            />
            <div className="muted" style={{ marginTop: 8 }}>Crosswalk rejects: {rejects.length}</div>
          </section>
        ) : null}
      </section>
    </main>
  );
}
