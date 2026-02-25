import { readCsv, readJson } from "../../lib/data";

export default function RunsPage() {
  const contract = readJson("reports/contract_migration_report.json");
  const quality = readJson("reports/enterprise_pipeline_report.json");
  const release = readJson("reports/release_gate_report.json");
  const rejects = readCsv("reports/contract_migration_rejects.csv");

  return (
    <main className="grid">
      <section className="card">
        <h3>Contract Migration</h3>
        <div className={contract.status === "PASS" ? "status-pass" : "status-fail"}>{contract.status || "UNKNOWN"}</div>
        <div className="muted">Tables written: {contract.tables_written ?? "-"}</div>
        <div className="muted">Population ratio: {contract.overall_column_population_ratio ?? "-"}</div>
        <div className="muted">Crosswalk rejects: {contract.crosswalk_reject_count ?? "-"}</div>
      </section>
      <section className="card">
        <h3>Enterprise Quality</h3>
        <div className={quality.status === "PASS" ? "status-pass" : "status-fail"}>{quality.status || "UNKNOWN"}</div>
        <div className="muted">Errors: {quality.severity_counts?.ERROR ?? "-"}</div>
        <div className="muted">Warnings: {quality.severity_counts?.WARN ?? "-"}</div>
      </section>
      <section className="card">
        <h3>Release Gate</h3>
        <div className={release.status === "PASS" ? "status-pass" : "status-fail"}>{release.status || "UNKNOWN"}</div>
        <table>
          <thead>
            <tr>
              <th>Gate</th>
              <th>Status</th>
              <th>Actual</th>
              <th>Expected</th>
            </tr>
          </thead>
          <tbody>
            {(release.checks || []).map((c: any) => (
              <tr key={c.gate}>
                <td>{c.gate}</td>
                <td className={c.status === "PASS" ? "status-pass" : "status-fail"}>{c.status}</td>
                <td>{String(c.actual)}</td>
                <td>{String(c.expected)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="card">
        <h3>Crosswalk Reject Sample</h3>
        <div className="muted">Rows: {rejects.length}</div>
        <table>
          <thead>
            <tr>
              <th>Table</th>
              <th>Field</th>
              <th>Record</th>
              <th>Source Value</th>
              <th>Crosswalk</th>
            </tr>
          </thead>
          <tbody>
            {rejects.slice(0, 50).map((r, i) => (
              <tr key={`${r.table_name}-${i}`}>
                <td>{r.table_name}</td>
                <td>{r.field_name}</td>
                <td>{r.record_id}</td>
                <td>{r.source_value}</td>
                <td>{r.crosswalk_name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
