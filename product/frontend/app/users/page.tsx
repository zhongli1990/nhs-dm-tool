export default function UsersPage() {
  return (
    <main className="grid">
      <section className="card">
        <h3>Mission-Critical User Roles</h3>
        <table>
          <thead>
            <tr>
              <th>User Role</th>
              <th>Primary Responsibilities</th>
              <th>Core UI Pages</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>DM Engineer</td>
              <td>Connector setup, mapping execution, pipeline runs, reject triage</td>
              <td>Connectors, Mappings, Runs</td>
            </tr>
            <tr>
              <td>Data Architect</td>
              <td>Schema alignment, mapping contract governance, policy overrides</td>
              <td>Schemas, Mappings, Runs</td>
            </tr>
            <tr>
              <td>Clinical Informatics Lead</td>
              <td>Clinical code-set approval, patient-safety DQ thresholds</td>
              <td>Mappings, Runs</td>
            </tr>
            <tr>
              <td>Programme/Release Manager</td>
              <td>Release gate decisions, cutover readiness and sign-off</td>
              <td>Dashboard, Runs</td>
            </tr>
            <tr>
              <td>DBA / Platform Engineer</td>
              <td>DB connectivity, connector operational controls, performance and security</td>
              <td>Connectors, Runs</td>
            </tr>
          </tbody>
        </table>
      </section>
      <section className="card">
        <h3>Lifecycle Tasks Supported</h3>
        <ol>
          <li>Ingest schema catalogs from source and target PAS vendors.</li>
          <li>Configure source and target connectors (CSV now, emulators now, ODBC/JDBC next).</li>
          <li>Inspect source/target table and field structures dynamically.</li>
          <li>Build and review mapping contract by class and field-level rules.</li>
          <li>Execute lifecycle pipelines and monitor run status.</li>
          <li>Review quality issues and translation rejects for remediation.</li>
          <li>Assess release gates by profile (`development`, `pre_production`, `cutover_ready`).</li>
          <li>Generate audit-ready evidence for governance and cutover boards.</li>
        </ol>
      </section>
    </main>
  );
}
