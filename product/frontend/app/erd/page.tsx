"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../../lib/api";

type Node = { id: string; label: string; column_count: number };
type Edge = { source: string; target: string; field: string; confidence: string; reason: string };

export default function ErdPage() {
  const [domain, setDomain] = useState<"source" | "target">("target");
  const [filter, setFilter] = useState("");
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  async function load() {
    const payload = await apiGet<{ nodes: Node[]; edges: Edge[] }>(
      `/api/schema-graph/${domain}/erd?table_filter=${encodeURIComponent(filter)}`
    );
    setNodes((payload.nodes || []).slice(0, 40));
    setEdges(payload.edges || []);
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, [domain]);

  const filteredEdges = useMemo(() => {
    const ids = new Set(nodes.map((n) => n.id));
    return edges.filter((e) => ids.has(e.source) && ids.has(e.target)).slice(0, 200);
  }, [nodes, edges]);

  const nodePos = useMemo(() => {
    const map: Record<string, { x: number; y: number }> = {};
    const cols = 5;
    const xStep = 230;
    const yStep = 130;
    nodes.forEach((n, idx) => {
      const row = Math.floor(idx / cols);
      const col = idx % cols;
      map[n.id] = { x: 80 + col * xStep, y: 70 + row * yStep };
    });
    return map;
  }, [nodes]);

  return (
    <main className="grid">
      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Schema ERD Explorer (MVP)</h3>
        <div className="muted">Visual relationship map for schema integration and lineage checks.</div>
        <div className="controls">
          <label>
            Domain
            <select value={domain} onChange={(e) => setDomain(e.target.value as "source" | "target")}>
              <option value="source">source</option>
              <option value="target">target</option>
            </select>
          </label>
          <label>
            Table filter
            <input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="LOAD_PMI / PATDATA / ADT..." />
          </label>
          <label>
            Actions
            <button className="primary" onClick={() => load().catch(() => undefined)}>
              Refresh ERD
            </button>
          </label>
        </div>
      </section>

      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>ERD Graph</h3>
        <div className="muted">Showing up to 40 nodes and 200 edges for usability.</div>
        <div className="table-wrap" style={{ height: 540 }}>
          <svg width={1300} height={900}>
            {filteredEdges.map((e, i) => {
              const s = nodePos[e.source];
              const t = nodePos[e.target];
              if (!s || !t) return null;
              return (
                <g key={`${e.source}-${e.target}-${i}`}>
                  <line x1={s.x + 65} y1={s.y + 20} x2={t.x + 65} y2={t.y + 20} stroke="#8aa7c7" strokeWidth={1.2} />
                </g>
              );
            })}
            {nodes.map((n) => {
              const p = nodePos[n.id];
              return (
                <g key={n.id}>
                  <rect x={p.x} y={p.y} width={130} height={52} rx={8} fill="#edf4fd" stroke="#8cb2dc" />
                  <text x={p.x + 8} y={p.y + 20} fontSize="10" fill="#0f2f56">
                    {n.id}
                  </text>
                  <text x={p.x + 8} y={p.y + 37} fontSize="10" fill="#37587f">
                    cols: {n.column_count}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </section>

      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Relationship List</h3>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Source</th>
                <th>Target</th>
                <th>Field</th>
                <th>Confidence</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {filteredEdges.slice(0, 300).map((e, i) => (
                <tr key={`${e.source}-${e.target}-${i}`}>
                  <td>{e.source}</td>
                  <td>{e.target}</td>
                  <td>{e.field}</td>
                  <td>{e.confidence}</td>
                  <td>{e.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
