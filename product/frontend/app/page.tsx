"use client";

import { useEffect, useState } from "react";
import { apiGet } from "../lib/api";

type TableProfile = { table_name: string; column_count: number };
type LatestRuns = {
  contract_migration?: any;
  enterprise_quality?: any;
  release_gates?: any;
};

export default function HomePage() {
  const [sourceTables, setSourceTables] = useState<TableProfile[]>([]);
  const [targetTables, setTargetTables] = useState<TableProfile[]>([]);
  const [runs, setRuns] = useState<LatestRuns>({});

  useEffect(() => {
    async function load() {
      const [source, target, latest] = await Promise.all([
        apiGet<{ tables: TableProfile[] }>("/api/schema/source"),
        apiGet<{ tables: TableProfile[] }>("/api/schema/target"),
        apiGet<LatestRuns>("/api/runs/latest"),
      ]);
      setSourceTables(source.tables || []);
      setTargetTables(target.tables || []);
      setRuns(latest || {});
    }
    load().catch(() => undefined);
  }, []);

  const contract = runs.contract_migration || {};
  const quality = runs.enterprise_quality || {};
  const release = runs.release_gates || {};

  const sourceFieldCount = sourceTables.reduce((acc, t) => acc + (t.column_count || 0), 0);
  const targetFieldCount = targetTables.reduce((acc, t) => acc + (t.column_count || 0), 0);

  return (
    <main className="grid">
      <section className="card">
        <div className="muted">Source Estate</div>
        <div className="kpi">{sourceTables.length || "-"}</div>
        <div className="muted">Tables ({sourceFieldCount || "-"} fields)</div>
      </section>
      <section className="card">
        <div className="muted">Target Estate</div>
        <div className="kpi">{targetTables.length || "-"}</div>
        <div className="muted">LOAD tables ({targetFieldCount || "-"} fields)</div>
      </section>
      <section className="card">
        <div className="muted">Contract ETL</div>
        <div className={`kpi ${contract.status === "PASS" ? "status-pass" : "status-fail"}`}>{contract.status ?? "-"}</div>
        <div className="muted">Rows: {contract.rows_written_total ?? "-"}</div>
      </section>
      <section className="card">
        <div className="muted">Enterprise Quality</div>
        <div className={`kpi ${quality.status === "PASS" ? "status-pass" : "status-fail"}`}>{quality.status ?? "-"}</div>
        <div className="muted">Errors: {quality.severity_counts?.ERROR ?? "-"} | Warnings: {quality.severity_counts?.WARN ?? "-"}</div>
      </section>
      <section className="card">
        <div className="muted">Release Gates</div>
        <div className={`kpi ${release.status === "PASS" ? "status-pass" : "status-fail"}`}>{release.status ?? "-"}</div>
        <div className="muted">Cutover readiness control</div>
      </section>
      <section className="card">
        <div className="muted">Crosswalk Rejects</div>
        <div className="kpi">{contract.crosswalk_reject_count ?? "-"}</div>
        <div className="muted">Strict translation quality indicator</div>
      </section>
    </main>
  );
}
