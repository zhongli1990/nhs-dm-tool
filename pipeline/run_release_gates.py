import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _parse_args():
    p = argparse.ArgumentParser(description="Run cutover release gates for migration readiness.")
    p.add_argument("--contract-report", default="reports/contract_migration_report.json")
    p.add_argument("--enterprise-report", default="reports/enterprise_pipeline_report.json")
    p.add_argument("--profile", default="cutover_ready", help="Gate profile name from pipeline/release_gate_profiles.json")
    p.add_argument("--profiles-file", default="pipeline/release_gate_profiles.json")
    p.add_argument("--max-errors", type=int, default=0)
    p.add_argument("--max-warnings", type=int, default=10)
    p.add_argument("--max-unresolved", type=int, default=5)
    p.add_argument("--max-crosswalk-rejects", type=int, default=0)
    p.add_argument("--min-population-ratio", type=float, default=0.60)
    p.add_argument("--min-tables-written", type=int, default=38)
    return p.parse_args()


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(name: str, passed: bool, actual, expected, message: str):
    return {
        "gate": name,
        "status": "PASS" if passed else "FAIL",
        "actual": actual,
        "expected": expected,
        "message": message,
    }


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    profiles_path = root / args.profiles_file
    if profiles_path.exists():
        profiles = _load_json(profiles_path)
        profile = profiles.get(args.profile, {})
        args.max_errors = int(profile.get("max_errors", args.max_errors))
        args.max_warnings = int(profile.get("max_warnings", args.max_warnings))
        args.max_unresolved = int(profile.get("max_unresolved", args.max_unresolved))
        args.max_crosswalk_rejects = int(profile.get("max_crosswalk_rejects", args.max_crosswalk_rejects))
        args.min_population_ratio = float(profile.get("min_population_ratio", args.min_population_ratio))
        args.min_tables_written = int(profile.get("min_tables_written", args.min_tables_written))

    contract = _load_json(root / args.contract_report)
    enterprise = _load_json(root / args.enterprise_report)

    contract_errors = int(contract.get("issue_counts", {}).get("ERROR", 0))
    enterprise_errors = int(enterprise.get("severity_counts", {}).get("ERROR", 0))
    total_errors = contract_errors + enterprise_errors

    contract_warn = int(contract.get("issue_counts", {}).get("WARN", 0))
    enterprise_warn = int(enterprise.get("severity_counts", {}).get("WARN", 0))
    total_warnings = contract_warn + enterprise_warn

    unresolved = int(enterprise.get("category_counts", {}).get("MAPPING_UNRESOLVED", 0))
    crosswalk_rejects = int(contract.get("crosswalk_reject_count", 0))
    pop_ratio = float(contract.get("overall_column_population_ratio", 0.0))
    tables_written = int(contract.get("tables_written", 0))

    checks = [
        _check("NO_ERRORS", total_errors <= args.max_errors, total_errors, f"<= {args.max_errors}", "Combined error count from ETL+quality gates."),
        _check("WARNINGS_THRESHOLD", total_warnings <= args.max_warnings, total_warnings, f"<= {args.max_warnings}", "Combined warnings threshold."),
        _check("UNRESOLVED_MAPPING_THRESHOLD", unresolved <= args.max_unresolved, unresolved, f"<= {args.max_unresolved}", "Unresolved mapping warnings must be within tolerance."),
        _check("CROSSWALK_REJECT_THRESHOLD", crosswalk_rejects <= args.max_crosswalk_rejects, crosswalk_rejects, f"<= {args.max_crosswalk_rejects}", "Crosswalk rejects from translation engine."),
        _check("POPULATION_RATIO_MIN", pop_ratio >= args.min_population_ratio, pop_ratio, f">= {args.min_population_ratio}", "Overall target column population ratio."),
        _check("TABLES_WRITTEN_MIN", tables_written >= args.min_tables_written, tables_written, f">= {args.min_tables_written}", "Expected number of target tables written."),
    ]

    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    report = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "inputs": {
            "contract_report": str(root / args.contract_report),
            "enterprise_report": str(root / args.enterprise_report),
        },
        "thresholds": {
            "profile": args.profile,
            "max_errors": args.max_errors,
            "max_warnings": args.max_warnings,
            "max_unresolved": args.max_unresolved,
            "max_crosswalk_rejects": args.max_crosswalk_rejects,
            "min_population_ratio": args.min_population_ratio,
            "min_tables_written": args.min_tables_written,
        },
        "checks": checks,
    }
    out = root / "reports" / "release_gate_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("Release gate evaluation completed.")
    print("Status:", status)
    print("Report:", out)


if __name__ == "__main__":
    main()
