import { readCsv, readJson } from "../../lib/data";

export default function MappingsPage() {
  const summary = readJson("reports/mapping_contract_summary.json");
  const rows = readCsv("reports/mapping_contract.csv").slice(0, 300);

  return (
    <main className="grid">
      <section className="card">
        <h3>Mapping Class Summary</h3>
        <table>
          <thead>
            <tr>
              <th>Class</th>
              <th>Count</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(summary.mapping_class_counts || {}).map(([k, v]) => (
              <tr key={k}>
                <td>{k}</td>
                <td>{String(v)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="card">
        <h3>Contract Rows (Sample)</h3>
        <div className="muted">Showing first 300 rows for UI performance</div>
        <table>
          <thead>
            <tr>
              <th>Target Table</th>
              <th>Target Field</th>
              <th>Class</th>
              <th>Source Table</th>
              <th>Source Field</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={`${r.target_table}-${r.target_field}-${i}`}>
                <td>{r.target_table}</td>
                <td>{r.target_field}</td>
                <td><span className="chip">{r.mapping_class}</span></td>
                <td>{r.primary_source_table}</td>
                <td>{r.primary_source_field}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
