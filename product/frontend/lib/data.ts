import fs from "fs";
import path from "path";

type Row = Record<string, string>;

const ROOT = path.resolve(process.cwd(), "..", "..");
const DATA_MIGRATION_ROOT = path.join(ROOT);

function parseCsv(content: string): Row[] {
  const lines = content.split(/\r?\n/).filter((l) => l.length > 0);
  if (lines.length === 0) return [];
  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const cells = splitCsvLine(line);
    const row: Row = {};
    headers.forEach((h, i) => {
      row[h] = cells[i] ?? "";
    });
    return row;
  });
}

function splitCsvLine(line: string): string[] {
  const out: string[] = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }
    if (ch === "," && !inQuotes) {
      out.push(current);
      current = "";
      continue;
    }
    current += ch;
  }
  out.push(current);
  return out;
}

export function readJson(relativePath: string): any {
  const p = path.join(DATA_MIGRATION_ROOT, relativePath);
  if (!fs.existsSync(p)) return {};
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

export function readCsv(relativePath: string): Row[] {
  const p = path.join(DATA_MIGRATION_ROOT, relativePath);
  if (!fs.existsSync(p)) return [];
  return parseCsv(fs.readFileSync(p, "utf-8"));
}

export function getSchemaProfiles() {
  const source = readCsv("schemas/source_schema_catalog.csv");
  const target = readCsv("schemas/target_schema_catalog.csv");
  return {
    source,
    target
  };
}

export function getGroupedSchema(rows: Row[]) {
  const grouped: Record<string, string[]> = {};
  for (const r of rows) {
    const t = r.table_name;
    const f = r.field_name;
    if (!t || !f) continue;
    grouped[t] = grouped[t] || [];
    grouped[t].push(f);
  }
  return Object.entries(grouped)
    .map(([table_name, columns]) => ({
      table_name,
      column_count: columns.length,
      columns
    }))
    .sort((a, b) => a.table_name.localeCompare(b.table_name));
}
