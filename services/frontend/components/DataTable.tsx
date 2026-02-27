"use client";

import { isValidElement, type ReactNode } from "react";

type Props = {
  columns: string[];
  rows: Record<string, ReactNode>[];
  emptyLabel?: string;
};

export default function DataTable({ columns, rows, emptyLabel = "No data." }: Props) {
  if (!rows.length) {
    return <div className="muted">{emptyLabel}</div>;
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, idx) => (
            <tr key={idx}>
              {columns.map((c) => (
                <td key={`${idx}-${c}`}>{isValidElement(r[c]) ? r[c] : String(r[c] ?? "")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
