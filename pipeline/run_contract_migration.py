import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from enterprise.contract_etl import build_contract_targets
from enterprise.io import write_issues_csv


def _parse_args():
    p = argparse.ArgumentParser(
        description="Execute contract-driven NHS PAS migration from source CSVs into target LOAD_ tables."
    )
    p.add_argument(
        "--source-dir",
        default="mock_data/source",
        help="Source CSV folder relative to data_migration root.",
    )
    p.add_argument(
        "--output-dir",
        default="mock_data/target_contract",
        help="Output target folder relative to data_migration root.",
    )
    p.add_argument(
        "--contract-file",
        default="reports/mapping_contract.csv",
        help="Mapping contract CSV path relative to data_migration root.",
    )
    p.add_argument(
        "--target-catalog-file",
        default="schemas/target_schema_catalog.csv",
        help="Target schema catalog CSV path relative to data_migration root.",
    )
    p.add_argument(
        "--crosswalk-dir",
        default="schemas/crosswalks",
        help="Crosswalk directory containing source_value->target_value CSV files.",
    )
    p.add_argument(
        "--impute-mode",
        default="strict",
        choices=["strict", "pre_production"],
        help="strict keeps only mapped values; pre_production applies fallback imputation for completeness testing.",
    )
    return p.parse_args()


def _write_stats_csv(path: Path, stats_rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "target_table",
        "source_table",
        "rows_written",
        "columns_total",
        "columns_populated",
        "mapped_fields",
        "column_population_ratio",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(stats_rows)


def _write_rejects_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["severity", "category", "table_name", "field_name", "record_id", "source_value", "crosswalk_name", "message"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    source_dir = root / args.source_dir
    output_dir = root / args.output_dir
    contract_csv = root / args.contract_file
    target_catalog_csv = root / args.target_catalog_file
    crosswalk_dir = root / args.crosswalk_dir

    stats, issues, rejects = build_contract_targets(
        root=root,
        source_dir=source_dir,
        output_dir=output_dir,
        contract_csv=contract_csv,
        target_catalog_csv=target_catalog_csv,
        crosswalk_dir=crosswalk_dir,
        impute_mode=args.impute_mode,
    )

    stats_rows = []
    for s in stats:
        ratio = round((s.columns_populated / s.columns_total), 4) if s.columns_total else 0.0
        stats_rows.append(
            {
                "target_table": s.target_table,
                "source_table": s.source_table,
                "rows_written": s.rows_written,
                "columns_total": s.columns_total,
                "columns_populated": s.columns_populated,
                "mapped_fields": s.mapped_fields,
                "column_population_ratio": ratio,
            }
        )

    stats_csv = root / "reports" / "contract_migration_table_stats.csv"
    _write_stats_csv(stats_csv, stats_rows)

    issues_csv = root / "reports" / "contract_migration_issues.csv"
    write_issues_csv(issues_csv, issues)
    rejects_csv = root / "reports" / "contract_migration_rejects.csv"
    _write_rejects_csv(rejects_csv, rejects)

    total_rows = sum(s.rows_written for s in stats)
    total_cols = sum(s.columns_total for s in stats)
    total_populated = sum(s.columns_populated for s in stats)

    sev_counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
    for i in issues:
        sev_counts[i["severity"]] = sev_counts.get(i["severity"], 0) + 1

    report = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if sev_counts.get("ERROR", 0) == 0 else "FAIL",
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "contract_file": str(contract_csv),
        "target_catalog_file": str(target_catalog_csv),
        "crosswalk_dir": str(crosswalk_dir),
        "impute_mode": args.impute_mode,
        "tables_written": len(stats),
        "rows_written_total": total_rows,
        "columns_total": total_cols,
        "columns_populated": total_populated,
        "overall_column_population_ratio": round(total_populated / total_cols, 4) if total_cols else 0.0,
        "issue_counts": sev_counts,
        "crosswalk_reject_count": len(rejects),
        "table_stats_csv": str(stats_csv),
        "issues_csv": str(issues_csv),
        "rejects_csv": str(rejects_csv),
    }
    report_path = root / "reports" / "contract_migration_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Contract-driven migration pipeline completed.")
    print("Status:", report["status"])
    print("Tables written:", report["tables_written"])
    print("Output directory:", output_dir)
    print("Report:", report_path)


if __name__ == "__main__":
    main()
