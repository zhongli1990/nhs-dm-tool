"use client";

import { useEffect, useMemo, useState } from "react";
import { apiGet } from "../../lib/api";

type Node = { id: string; label: string; column_count: number };
type Edge = {
  source: string;
  target: string;
  field: string;
  confidence: string;
  reason: string;
  cardinality?: string;
};

const NODE_W = 190;
const NODE_H = 66;
const SVG_W = 2200;

function chooseVisibleNodes(nodes: Node[], edges: Edge[], maxNodes: number) {
  const degree: Record<string, number> = {};
  for (const n of nodes) degree[n.id] = 0;
  for (const e of edges) {
    degree[e.source] = (degree[e.source] || 0) + 1;
    degree[e.target] = (degree[e.target] || 0) + 1;
  }
  return [...nodes]
    .sort((a, b) => (degree[b.id] || 0) - (degree[a.id] || 0) || a.id.localeCompare(b.id))
    .slice(0, maxNodes);
}

function buildForceLayout(
  nodes: Node[],
  edges: Edge[],
  width: number,
  height: number,
  density: "compact" | "normal" | "sparse"
) {
  const ids = nodes.map((n) => n.id);
  const n = ids.length;
  const pos: Record<string, { x: number; y: number }> = {};
  const vel: Record<string, { x: number; y: number }> = {};
  const centerX = width / 2;
  const centerY = height / 2;

  // Deterministic circular initialization.
  ids.forEach((id, i) => {
    const a = (2 * Math.PI * i) / Math.max(n, 1);
    const r = Math.min(width, height) * 0.35;
    pos[id] = { x: centerX + Math.cos(a) * r, y: centerY + Math.sin(a) * r };
    vel[id] = { x: 0, y: 0 };
  });

  const kRepel = density === "sparse" ? 42000 : density === "compact" ? 22000 : 30000;
  const kSpring = density === "sparse" ? 0.024 : density === "compact" ? 0.036 : 0.03;
  const linkLen = density === "sparse" ? 280 : density === "compact" ? 180 : 230;
  const gravity = 0.006;
  const damping = 0.84;
  const minDist = density === "sparse" ? 170 : density === "compact" ? 110 : 140;
  const margin = density === "sparse" ? 120 : 80;

  const steps = density === "sparse" ? 360 : density === "compact" ? 220 : 300;
  for (let step = 0; step < steps; step++) {
    const force: Record<string, { x: number; y: number }> = {};
    ids.forEach((id) => (force[id] = { x: 0, y: 0 }));

    // Repulsion + collision spacing.
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const a = ids[i];
        const b = ids[j];
        let dx = pos[b].x - pos[a].x;
        let dy = pos[b].y - pos[a].y;
        let d2 = dx * dx + dy * dy;
        if (d2 < 1) d2 = 1;
        let d = Math.sqrt(d2);
        if (d < 0.001) d = 0.001;
        const ux = dx / d;
        const uy = dy / d;

        const repel = kRepel / d2;
        force[a].x -= ux * repel;
        force[a].y -= uy * repel;
        force[b].x += ux * repel;
        force[b].y += uy * repel;

        if (d < minDist) {
          const push = (minDist - d) * 1.3;
          force[a].x -= ux * push;
          force[a].y -= uy * push;
          force[b].x += ux * push;
          force[b].y += uy * push;
        }
      }
    }

    // Springs.
    for (const e of edges) {
      if (!(e.source in pos) || !(e.target in pos)) continue;
      const a = e.source;
      const b = e.target;
      let dx = pos[b].x - pos[a].x;
      let dy = pos[b].y - pos[a].y;
      let d = Math.sqrt(dx * dx + dy * dy);
      if (d < 0.001) d = 0.001;
      const ux = dx / d;
      const uy = dy / d;
      const spring = kSpring * (d - linkLen);
      force[a].x += ux * spring;
      force[a].y += uy * spring;
      force[b].x -= ux * spring;
      force[b].y -= uy * spring;
    }

    // Gravity + integrate.
    for (const id of ids) {
      force[id].x += (centerX - pos[id].x) * gravity;
      force[id].y += (centerY - pos[id].y) * gravity;

      vel[id].x = (vel[id].x + force[id].x) * damping;
      vel[id].y = (vel[id].y + force[id].y) * damping;
      pos[id].x += vel[id].x;
      pos[id].y += vel[id].y;

      pos[id].x = Math.min(width - margin, Math.max(margin, pos[id].x));
      pos[id].y = Math.min(height - margin, Math.max(margin, pos[id].y));
    }
  }

  // Extra post-relax pass to eliminate residual overlaps.
  for (let pass = 0; pass < 24; pass++) {
    let moved = false;
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        const a = ids[i];
        const b = ids[j];
        let dx = pos[b].x - pos[a].x;
        let dy = pos[b].y - pos[a].y;
        let d = Math.sqrt(dx * dx + dy * dy);
        if (d < 0.001) d = 0.001;
        const needX = NODE_W + 28;
        const needY = NODE_H + 20;
        if (Math.abs(dx) < needX && Math.abs(dy) < needY) {
          const ux = dx / d;
          const uy = dy / d;
          const push = 8;
          pos[a].x -= ux * push;
          pos[a].y -= uy * push;
          pos[b].x += ux * push;
          pos[b].y += uy * push;
          moved = true;
        }
      }
    }
    if (!moved) break;
  }

  // Fit used bounds into viewport with padding.
  const xs = ids.map((id) => pos[id].x);
  const ys = ids.map((id) => pos[id].y);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);
  const usedW = Math.max(1, maxX - minX);
  const usedH = Math.max(1, maxY - minY);
  const pad = density === "sparse" ? 170 : density === "compact" ? 80 : 120;
  const scale = Math.min((width - pad * 2) / usedW, (height - pad * 2) / usedH);
  const out: Record<string, { x: number; y: number }> = {};
  for (const id of ids) {
    out[id] = {
      x: pad + (pos[id].x - minX) * scale,
      y: pad + (pos[id].y - minY) * scale,
    };
  }
  return out;
}

export default function ErdPage() {
  const [domain, setDomain] = useState<"source" | "target">("target");
  const [filter, setFilter] = useState("");
  const [density, setDensity] = useState<"compact" | "normal" | "sparse">("sparse");
  const [allNodes, setAllNodes] = useState<Node[]>([]);
  const [allEdges, setAllEdges] = useState<Edge[]>([]);

  async function load() {
    const payload = await apiGet<{ nodes: Node[]; edges: Edge[] }>(`/api/schema-graph/${domain}/erd`);
    setAllNodes(payload.nodes || []);
    setAllEdges(payload.edges || []);
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, [domain]);

  const visibleNodes = useMemo(() => {
    const tokens = filter
      .toLowerCase()
      .split(/[,\s/|]+/)
      .map((t) => t.trim())
      .filter(Boolean);
    if (tokens.length) {
      const matchSet = new Set(
        allNodes
          .filter((n) => tokens.some((t) => n.id.toLowerCase().includes(t)))
          .map((n) => n.id)
      );
      if (matchSet.size) {
        // Include 1-hop neighbors for graph context.
        for (const e of allEdges) {
          if (matchSet.has(e.source)) matchSet.add(e.target);
          if (matchSet.has(e.target)) matchSet.add(e.source);
        }
      }
      const matched = allNodes.filter((n) => matchSet.has(n.id));
      return matched.slice(0, 90);
    }
    return chooseVisibleNodes(allNodes, allEdges, 90);
  }, [allNodes, allEdges, filter]);

  const tableOptions = useMemo(() => allNodes.map((n) => n.id).sort(), [allNodes]);

  const filteredEdges = useMemo(() => {
    const ids = new Set(visibleNodes.map((n) => n.id));
    return allEdges.filter((e) => ids.has(e.source) && ids.has(e.target)).slice(0, 300);
  }, [visibleNodes, allEdges]);

  const graphHeight = useMemo(() => {
    const count = visibleNodes.length;
    if (count <= 24) return density === "sparse" ? 1120 : 980;
    if (count <= 50) return density === "sparse" ? 1420 : 1220;
    return density === "sparse" ? 1760 : 1480;
  }, [visibleNodes.length, density]);

  const nodeCenters = useMemo(
    () => buildForceLayout(visibleNodes, filteredEdges, SVG_W, graphHeight, density),
    [visibleNodes, filteredEdges, graphHeight, density]
  );

  return (
    <main className="grid">
      <section className="card" style={{ gridColumn: "1 / -1" }}>
        <h3>Schema ERD Explorer</h3>
        <div className="muted">Auto-distributed force layout with inferred links and cardinality labels.</div>
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
            <input
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              list="erd-table-options"
              placeholder="Type keyword or pick table..."
            />
            <datalist id="erd-table-options">
              {tableOptions.map((t) => (
                <option key={t} value={t} />
              ))}
            </datalist>
          </label>
          <label>
            Layout density
            <select value={density} onChange={(e) => setDensity(e.target.value as "compact" | "normal" | "sparse")}>
              <option value="compact">compact</option>
              <option value="normal">normal</option>
              <option value="sparse">sparse</option>
            </select>
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
        <div className="muted">
          Nodes: {visibleNodes.length} / {allNodes.length} | Edges: {filteredEdges.length} / {allEdges.length}
        </div>
        <div className="table-wrap" style={{ height: 650 }}>
          <svg width={SVG_W} height={graphHeight}>
            <defs>
              <marker id="erdArrow" markerWidth="9" markerHeight="6" refX="8" refY="3" orient="auto">
                <path d="M0,0 L9,3 L0,6 Z" fill="#6f90b8" />
              </marker>
            </defs>

            {filteredEdges.map((e, i) => {
              const s = nodeCenters[e.source];
              const t = nodeCenters[e.target];
              if (!s || !t) return null;
              const x1 = s.x + NODE_W / 2;
              const y1 = s.y + NODE_H / 2;
              const x2 = t.x + NODE_W / 2;
              const y2 = t.y + NODE_H / 2;
              const dx = x2 - x1;
              const dy = y2 - y1;
              const curve = 0.12;
              const cx1 = x1 + dx * 0.33 - dy * curve;
              const cy1 = y1 + dy * 0.33 + dx * curve;
              const cx2 = x1 + dx * 0.66 - dy * curve;
              const cy2 = y1 + dy * 0.66 + dx * curve;
              const mx = (x1 + x2) / 2;
              const my = (y1 + y2) / 2;
              return (
                <g key={`${e.source}-${e.target}-${i}`}>
                  <path d={`M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`} fill="none" stroke="#7e9abf" strokeWidth={1.3} markerEnd="url(#erdArrow)" />
                  <text x={mx} y={my - 8} fontSize="9" fill="#9eb7d6" textAnchor="middle">
                    {e.cardinality || "1:N"}
                  </text>
                </g>
              );
            })}

            {visibleNodes.map((n) => {
              const p = nodeCenters[n.id];
              return (
                <g key={n.id}>
                  <rect x={p.x} y={p.y} width={NODE_W} height={NODE_H} rx={10} fill="#233851" stroke="#6c8db3" />
                  <text x={p.x + 10} y={p.y + 24} fontSize="11" fill="#e8f1fa">
                    {n.id}
                  </text>
                  <text x={p.x + 10} y={p.y + 45} fontSize="10" fill="#b9cde5">
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
                <th>ID</th>
                <th>Source</th>
                <th>Target</th>
                <th>Field</th>
                <th>Cardinality</th>
                <th>Confidence</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {filteredEdges.slice(0, 450).map((e, i) => (
                <tr key={`${e.source}-${e.target}-${i}`}>
                  <td>{i + 1}</td>
                  <td>{e.source}</td>
                  <td>{e.target}</td>
                  <td>{e.field}</td>
                  <td>{e.cardinality || "1:N"}</td>
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
