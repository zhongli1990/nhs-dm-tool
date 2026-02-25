import { readJson } from "../lib/data";

export default function HomePage() {
  const schema = readJson("schemas/schema_catalog_summary.json");
  const contract = readJson("reports/contract_migration_report.json");
  const quality = readJson("reports/enterprise_pipeline_report.json");
  const release = readJson("reports/release_gate_report.json");

  return (
    <main className="grid">
      <section className="card">
        <div className="muted">Source Estate</div>
        <div className="kpi">{schema.source_total_tables ?? "-"}</div>
        <div className="muted">Tables ({schema.source_total_fields ?? "-"} fields)</div>
      </section>
      <section className="card">
        <div className="muted">Target Estate</div>
        <div className="kpi">{schema.target_total_tables ?? "-"}</div>
        <div className="muted">LOAD tables ({schema.target_total_fields ?? "-"} fields)</div>
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
