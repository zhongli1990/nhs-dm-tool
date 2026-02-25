import csv
from pathlib import Path
from typing import Dict, List

from io_utils import write_json


def _write_csv(path: Path, rows: List[Dict[str, str]], headers: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})


def build_gap_report(
    root: Path,
    source_catalog: List[Dict[str, str]],
    target_catalog: List[Dict[str, str]],
    mapping_spec: Dict,
) -> Dict[str, int]:
    source_tables = {r["table_name"] for r in source_catalog if r["table_name"]}
    target_tables = {r["table_name"] for r in target_catalog if r["table_name"]}

    mapped_source_tables = {m["source_table"] for m in mapping_spec["migrations"]}
    mapped_target_tables = {m["target_table"] for m in mapping_spec["migrations"]}

    rows: List[Dict[str, str]] = []

    for table in sorted(source_tables - mapped_source_tables):
        rows.append(
            {
                "gap_type": "UNMAPPED_SOURCE_TABLE",
                "severity": "HIGH",
                "entity": table,
                "field_name": "",
                "detail": "Source table exists in dictionary but has no migration mapping defined.",
            }
        )

    for table in sorted(target_tables - mapped_target_tables):
        rows.append(
            {
                "gap_type": "UNMAPPED_TARGET_TABLE",
                "severity": "HIGH",
                "entity": table,
                "field_name": "",
                "detail": "Target load table exists in migration guide but has no population mapping defined.",
            }
        )

    for migration in mapping_spec["migrations"]:
        source_table = migration["source_table"]
        target_table = migration["target_table"]

        source_fields = {r["field_name"] for r in source_catalog if r["table_name"] == source_table}
        target_fields = {r["field_name"] for r in target_catalog if r["table_name"] == target_table}

        mapped_source_fields = set(migration.get("field_map", {}).keys())
        mapped_target_fields = set(migration.get("field_map", {}).values()) | set(migration.get("defaults", {}).keys())

        for field in sorted(mapped_source_fields - source_fields):
            rows.append(
                {
                    "gap_type": "MAPPING_SOURCE_FIELD_NOT_FOUND",
                    "severity": "HIGH",
                    "entity": source_table,
                    "field_name": field,
                    "detail": f"Field in mapping spec not found in source table {source_table}.",
                }
            )

        for field in sorted(mapped_target_fields - target_fields):
            rows.append(
                {
                    "gap_type": "MAPPING_TARGET_FIELD_NOT_FOUND",
                    "severity": "HIGH",
                    "entity": target_table,
                    "field_name": field,
                    "detail": f"Field in mapping spec not found in target table {target_table}.",
                }
            )

        uncovered_target = sorted(target_fields - mapped_target_fields)
        for field in uncovered_target:
            rows.append(
                {
                    "gap_type": "UNMAPPED_TARGET_FIELD",
                    "severity": "MEDIUM",
                    "entity": target_table,
                    "field_name": field,
                    "detail": "Target field is in catalog but has no source mapping/default in current pipeline.",
                }
            )

    low_conf_rows = [
        r
        for r in target_catalog
        if r.get("parse_confidence") and float(r["parse_confidence"]) < 0.60
    ]
    for r in low_conf_rows:
        rows.append(
            {
                "gap_type": "LOW_CONFIDENCE_TARGET_PARSE",
                "severity": "MEDIUM",
                "entity": r["table_name"],
                "field_name": r["field_name"],
                "detail": f"Field extracted from PDF with confidence {r['parse_confidence']}.",
            }
        )

    _write_csv(
        root / "reports" / "schema_gap_report.csv",
        rows,
        ["gap_type", "severity", "entity", "field_name", "detail"],
    )

    summary = {
        "high_severity_gap_count": sum(1 for r in rows if r["severity"] == "HIGH"),
        "medium_severity_gap_count": sum(1 for r in rows if r["severity"] == "MEDIUM"),
        "mapped_source_table_count": len(mapped_source_tables),
        "mapped_target_table_count": len(mapped_target_tables),
        "total_source_table_count": len(source_tables),
        "total_target_table_count": len(target_tables),
    }
    write_json(root / "reports" / "schema_gap_summary.json", summary)
    return summary
