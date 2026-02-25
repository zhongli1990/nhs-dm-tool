import { getGroupedSchema, getSchemaProfiles } from "../../lib/data";

export default function SchemasPage() {
  const { source, target } = getSchemaProfiles();
  const sourceTables = getGroupedSchema(source);
  const targetTables = getGroupedSchema(target);

  return (
    <main className="grid">
      <section className="card">
        <h3>Source Schema Catalog</h3>
        <div className="muted">{sourceTables.length} tables</div>
        <table>
          <thead>
            <tr>
              <th>Table</th>
              <th>Columns</th>
            </tr>
          </thead>
          <tbody>
            {sourceTables.map((t) => (
              <tr key={t.table_name}>
                <td>{t.table_name}</td>
                <td>{t.column_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="card">
        <h3>Target Schema Catalog</h3>
        <div className="muted">{targetTables.length} tables</div>
        <table>
          <thead>
            <tr>
              <th>Table</th>
              <th>Columns</th>
            </tr>
          </thead>
          <tbody>
            {targetTables.map((t) => (
              <tr key={t.table_name}>
                <td>{t.table_name}</td>
                <td>{t.column_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>
  );
}
