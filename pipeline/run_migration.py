import csv
from pathlib import Path
from typing import Dict, List

from extract_specs import extract_all
from gap_report import build_gap_report
from generate_mock_data import generate_mock_data
from io_utils import read_csv, read_json, write_json


def _field_lookup(rows: List[Dict[str, str]], table_name: str) -> List[str]:
    return [r["field_name"] for r in rows if r["table_name"] == table_name]


def _read_table(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    return read_csv(path)


def _write_table(path: Path, headers: List[str], rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})


def _apply_migration(
    migration: Dict,
    source_rows: List[Dict[str, str]],
    target_headers: List[str],
    target_catalog_rows: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    mandatory_fields = {
        r["field_name"] for r in target_catalog_rows if r.get("mandatory_hint", "N") == "Y" and r["table_name"] == migration["target_table"]
    }

    for idx, src in enumerate(source_rows, start=1):
        row = {h: "" for h in target_headers}

        for src_field, tgt_field in migration.get("field_map", {}).items():
            if tgt_field in row:
                row[tgt_field] = src.get(src_field, "")

        for tgt_field, default_value in migration.get("defaults", {}).items():
            if tgt_field not in row:
                continue
            if default_value == "AUTO":
                row[tgt_field] = str(idx)
            elif default_value.startswith("FROM:"):
                src_field = default_value.split(":", 1)[1]
                row[tgt_field] = src.get(src_field, "")
            else:
                row[tgt_field] = default_value

        missing_mandatory = [f for f in mandatory_fields if not str(row.get(f, "")).strip()]
        row["__quality__"] = "FAIL" if missing_mandatory else "PASS"
        row["__issues__"] = "; ".join(f"missing:{f}" for f in missing_mandatory)
        out.append(row)
    return out


def main() -> None:
    root = Path(__file__).resolve().parents[1]

    # 1) Extract schemas from spec files.
    schema_stats = extract_all(root)

    # 2) Generate spec-aligned source and target mock files.
    generate_mock_data(root)

    source_catalog = read_csv(root / "schemas" / "source_schema_catalog.csv")
    target_catalog = read_csv(root / "schemas" / "target_schema_catalog.csv")
    mapping_spec = read_json(root / "schemas" / "mapping_spec.json")

    migration_results = []
    quality_summary = {"PASS": 0, "FAIL": 0}

    for migration in mapping_spec["migrations"]:
        source_table = migration["source_table"]
        target_table = migration["target_table"]

        source_path = root / "mock_data" / "source" / f"{source_table}.csv"
        target_path = root / "mock_data" / "target" / f"{target_table}.csv"

        source_rows = _read_table(source_path)
        target_headers = _field_lookup(target_catalog, target_table)
        transformed = _apply_migration(migration, source_rows, target_headers, target_catalog)

        for row in transformed:
            quality_summary[row["__quality__"]] = quality_summary.get(row["__quality__"], 0) + 1

        write_rows = [{k: v for k, v in r.items() if not k.startswith("__")} for r in transformed]
        _write_table(target_path, target_headers, write_rows)

        migration_results.append(
            {
                "migration_name": migration["name"],
                "source_table": source_table,
                "target_table": target_table,
                "source_rows": len(source_rows),
                "target_rows": len(write_rows),
                "failed_rows": sum(1 for r in transformed if r["__quality__"] == "FAIL"),
            }
        )

    gap_summary = build_gap_report(root, source_catalog, target_catalog, mapping_spec)

    report = {
        "schema_catalog_stats": schema_stats,
        "migrations": migration_results,
        "quality_summary": quality_summary,
        "gap_summary": gap_summary,
    }
    write_json(root / "reports" / "migration_run_report.json", report)

    print("Migration run completed from real requirement specs.")
    print(f"Source schema tables: {schema_stats['source_total_tables']}")
    print(f"Target schema tables: {schema_stats['target_total_tables']}")
    print(f"Target parse confidence avg: {schema_stats['target_parse_confidence_avg']}")
    print(f"High-severity gaps: {gap_summary['high_severity_gap_count']}")


if __name__ == "__main__":
    main()
