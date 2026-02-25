import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from enterprise.checks import (
    check_mapping_contract,
    check_source_quality,
    check_target_referential_integrity,
)
from enterprise.io import write_issues_csv


def _parse_args():
    p = argparse.ArgumentParser(description="Run enterprise-grade migration quality checks.")
    p.add_argument("--min-patients", type=int, default=20, help="Minimum expected rows per source/target table.")
    p.add_argument(
        "--contract-file",
        type=str,
        default="reports/mapping_contract.csv",
        help="Mapping contract CSV path (relative to data_migration root).",
    )
    return p.parse_args()


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    source_dir = root / "mock_data" / "source"
    target_dir = root / "mock_data" / "target"
    contract_path = root / args.contract_file

    issues = []
    issues.extend(check_source_quality(source_dir, args.min_patients))
    issues.extend(check_mapping_contract(contract_path))
    issues.extend(check_target_referential_integrity(target_dir))

    issues_rows = [i.__dict__ for i in issues]
    issues_csv = root / "reports" / "enterprise_pipeline_issues.csv"
    write_issues_csv(issues_csv, issues_rows)

    severity_counts = {"ERROR": 0, "WARN": 0, "INFO": 0}
    category_counts = {}
    for i in issues_rows:
        severity_counts[i["severity"]] = severity_counts.get(i["severity"], 0) + 1
        category_counts[i["category"]] = category_counts.get(i["category"], 0) + 1

    status = "PASS" if severity_counts.get("ERROR", 0) == 0 else "FAIL"
    report = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "min_patients_required": args.min_patients,
        "issue_count": len(issues_rows),
        "severity_counts": severity_counts,
        "category_counts": dict(sorted(category_counts.items(), key=lambda kv: kv[0])),
        "issues_csv": str(issues_csv),
    }
    report_path = root / "reports" / "enterprise_pipeline_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Enterprise migration quality pipeline completed.")
    print("Status:", status)
    print("Errors:", severity_counts.get("ERROR", 0))
    print("Warnings:", severity_counts.get("WARN", 0))
    print("Report:", report_path)
    print("Issues:", issues_csv)


if __name__ == "__main__":
    main()
