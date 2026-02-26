"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet, apiPost } from "../../lib/api";
import DataTable from "../../components/DataTable";

type Step = {
  id: string;
  name: string;
  description: string;
  command: string[];
};

export default function LifecyclePage() {
  const [rows, setRows] = useState(20);
  const [seed, setSeed] = useState(42);
  const [minPatients, setMinPatients] = useState(20);
  const [profile, setProfile] = useState("pre_production");
  const [steps, setSteps] = useState<Step[]>([]);
  const [runningStep, setRunningStep] = useState<string>("");
  const [log, setLog] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [stepStatus, setStepStatus] = useState<Record<string, "PASS" | "FAIL" | "PENDING">>({});

  const query = useMemo(
    () => `rows=${rows}&seed=${seed}&min_patients=${minPatients}&release_profile=${profile}`,
    [rows, seed, minPatients, profile]
  );

  async function loadSteps() {
    const payload = await apiGet<{ steps: Step[] }>(`/api/lifecycle/steps?${query}`);
    setSteps(payload.steps || []);
    setStepStatus(
      (payload.steps || []).reduce((acc: Record<string, "PENDING">, s) => {
        acc[s.id] = "PENDING";
        return acc;
      }, {})
    );
  }

  useEffect(() => {
    loadSteps().catch(() => undefined);
  }, [query]);

  async function runStep(stepId: string) {
    setRunningStep(stepId);
    setError("");
    try {
      const payload = await apiPost<any>(`/api/lifecycle/steps/${stepId}/execute?${query}`);
      const ok = payload.return_code === 0;
      setStepStatus((prev) => ({ ...prev, [stepId]: ok ? "PASS" : "FAIL" }));
      const nextLog = [
        `STEP: ${stepId}`,
        `COMMAND: ${payload.command}`,
        `RETURN CODE: ${payload.return_code}`,
        "",
        payload.stdout_tail || "",
        payload.stderr_tail || "",
      ].join("\n");
      setLog(nextLog);
      if (!ok) throw new Error(`Step failed: ${stepId}`);
    } catch (ex: any) {
      setStepStatus((prev) => ({ ...prev, [stepId]: "FAIL" }));
      setError(ex?.message || "Step execution failed");
      throw ex;
    } finally {
      setRunningStep("");
    }
  }

  async function runAllSteps() {
    setError("");
    for (const s of steps) {
      try {
        await runStep(s.id);
      } catch {
        break;
      }
    }
  }

  return (
    <main className="grid">
      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Lifecycle Orchestration Console</h3>
        <div className="muted">Run each migration stage from UI; backend executes the same pipeline commands used by CLI users.</div>
        <div className="controls">
          <label>
            Rows
            <input type="number" min={1} value={rows} onChange={(e) => setRows(Number(e.target.value || 20))} />
          </label>
          <label>
            Seed
            <input type="number" min={0} value={seed} onChange={(e) => setSeed(Number(e.target.value || 42))} />
          </label>
          <label>
            Min patients
            <input type="number" min={1} value={minPatients} onChange={(e) => setMinPatients(Number(e.target.value || 20))} />
          </label>
          <label>
            Release profile
            <select value={profile} onChange={(e) => setProfile(e.target.value)}>
              <option value="development">development</option>
              <option value="pre_production">pre_production</option>
              <option value="cutover_ready">cutover_ready</option>
            </select>
          </label>
          <label>
            Actions
            <button className="primary" type="button" onClick={() => runAllSteps().catch(() => undefined)} disabled={!!runningStep || steps.length === 0}>
              {runningStep ? `Running ${runningStep}...` : "Run All Steps In Order"}
            </button>
          </label>
        </div>
        {error ? <div className="status-fail" style={{ marginTop: 8 }}>{error}</div> : null}
      </section>

      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Lifecycle Steps</h3>
        <DataTable
          columns={["name", "description", "command", "status", "action"]}
          rows={steps.map((s) => ({
            name: s.name,
            description: s.description,
            command: s.command.join(" "),
            status: stepStatus[s.id] || "PENDING",
            action: (
              <button type="button" disabled={!!runningStep} onClick={() => runStep(s.id).catch(() => undefined)}>
                {runningStep === s.id ? "Running..." : "Run Step"}
              </button>
            ),
          }))}
          emptyLabel="No lifecycle steps loaded."
        />
      </section>

      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Execution Log (tail)</h3>
        <pre className="log">{log || "Run a lifecycle step to view execution output."}</pre>
      </section>
    </main>
  );
}
