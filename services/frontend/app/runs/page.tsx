"use client";

import { useEffect, useState } from "react";
import { apiGet, apiPost } from "../../lib/api";
import SectionTabs from "../../components/SectionTabs";
import DataTable from "../../components/DataTable";

export default function RunsPage() {
  const [contract, setContract] = useState<any>({});
  const [quality, setQuality] = useState<any>({});
  const [release, setRelease] = useState<any>({});
  const [rejects, setRejects] = useState<any[]>([]);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState("");
  const [runLog, setRunLog] = useState("");
  const [profile, setProfile] = useState("pre_production");
  const [rows, setRows] = useState(20);
  const [seed, setSeed] = useState(42);
  const [minPatients, setMinPatients] = useState(20);
  const [view, setView] = useState<"overview" | "gates" | "rejects">("overview");

  async function load() {
    const [latest, rejectPayload] = await Promise.all([
      apiGet<any>("/api/runs/latest"),
      apiGet<{ rows: any[] }>("/api/rejects/crosswalk"),
    ]);
    setContract(latest.contract_migration || {});
    setQuality(latest.enterprise_quality || {});
    setRelease(latest.release_gates || {});
    setRejects(rejectPayload.rows || []);
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  async function runAll() {
    setRunning(true);
    setRunError("");
    try {
      const payload = await apiPost<any>(
        `/api/runs/execute?rows=${rows}&seed=${seed}&min_patients=${minPatients}&release_profile=${profile}`
      );
      setRunLog(
        [
          `COMMAND: ${payload.command || "-"}`,
          `RETURN CODE: ${payload.return_code}`,
          "",
          payload.stdout_tail || "",
          payload.stderr_tail || "",
        ].join("\n")
      );
      await load();
    } catch (ex: any) {
      setRunError(ex?.message || "Lifecycle run failed");
    } finally {
      setRunning(false);
    }
  }

  return (
    <main className="grid">
      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Run Orchestration</h3>
        <div className="muted">Normal users and engineers can trigger backend lifecycle services with governed run parameters.</div>
        <div className="controls">
          <label>
            Rows
            <input type="number" value={rows} min={1} onChange={(e) => setRows(Number(e.target.value || 20))} />
          </label>
          <label>
            Seed
            <input type="number" value={seed} min={0} onChange={(e) => setSeed(Number(e.target.value || 42))} />
          </label>
          <label>
            Min patients
            <input type="number" value={minPatients} min={1} onChange={(e) => setMinPatients(Number(e.target.value || 20))} />
          </label>
          <label>
            Release profile
            <select value={profile} onChange={(e) => setProfile(e.target.value)}>
              <option value="development">development</option>
              <option value="pre_production">pre_production</option>
              <option value="cutover_ready">cutover_ready</option>
            </select>
          </label>
        </div>
        <button className="primary" onClick={runAll} disabled={running} style={{ marginTop: 10 }}>
          {running ? "Running..." : "Run Full Lifecycle"}
        </button>
        {runError ? <div className="status-fail" style={{ marginTop: 8 }}>{runError}</div> : null}
      </section>

      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <SectionTabs
          tabs={[
            { id: "overview", label: "Overview" },
            { id: "gates", label: "Gate Checks" },
            { id: "rejects", label: "Crosswalk Rejects" },
          ]}
          active={view}
          onChange={(id) => setView(id as "overview" | "gates" | "rejects")}
        />
      </section>

      {view === "overview" ? (
        <>
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
            <div className="muted">Profile: {release.thresholds?.profile ?? "-"}</div>
          </section>
        </>
      ) : null}

      {view === "gates" ? (
        <section className="card" style={{ gridColumn: "1 / -1" }}>
          <h3>Release Gate Checks</h3>
          <DataTable columns={["gate", "status", "actual", "expected", "message"]} rows={release.checks || []} emptyLabel="No gate report yet." />
        </section>
      ) : null}

      {view === "rejects" ? (
        <section className="card" style={{ gridColumn: "1 / -1" }}>
          <h3>Crosswalk Reject Sample</h3>
          <DataTable
            columns={["table_name", "field_name", "record_id", "source_value", "crosswalk_name"]}
            rows={rejects.slice(0, 500)}
            emptyLabel="No rejects."
          />
          <div className="muted">Showing up to 500 rows.</div>
        </section>
      ) : null}

      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Execution Log (tail)</h3>
        <pre className="log">{runLog || "Run lifecycle to view command output."}</pre>
      </section>
    </main>
  );
}
