import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _run(cmd, cwd: Path):
    p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "return_code": p.returncode,
        "stdout": p.stdout[-2000:],
        "stderr": p.stderr[-2000:],
    }


def _parse_args():
    p = argparse.ArgumentParser(description="Run full product lifecycle pipeline.")
    p.add_argument("--rows", type=int, default=20)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--min-patients", type=int, default=20)
    p.add_argument("--release-profile", default="pre_production")
    return p.parse_args()


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[1]
    steps = [
        ["python", "pipeline/extract_specs.py"],
        ["python", "pipeline/generate_all_mock_data.py", "--rows", str(args.rows), "--seed", str(args.seed)],
        ["python", "pipeline/analyze_semantic_mapping.py"],
        ["python", "pipeline/build_mapping_contract.py"],
        [
            "python",
            "pipeline/run_contract_migration.py",
            "--source-dir",
            "mock_data/source",
            "--output-dir",
            "mock_data/target_contract",
            "--contract-file",
            "reports/mapping_contract.csv",
            "--target-catalog-file",
            "schemas/target_schema_catalog.csv",
            "--crosswalk-dir",
            "schemas/crosswalks",
            "--impute-mode",
            "pre_production" if args.release_profile in {"development", "pre_production"} else "strict",
        ],
        ["python", "pipeline/run_enterprise_pipeline.py", "--min-patients", str(args.min_patients)],
        ["python", "pipeline/run_release_gates.py", "--profile", args.release_profile],
    ]

    results = []
    for s in steps:
        results.append(_run(s, root))
        if results[-1]["return_code"] != 0:
            break

    lifecycle = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if all(r["return_code"] == 0 for r in results) else "FAIL",
        "rows": args.rows,
        "seed": args.seed,
        "min_patients": args.min_patients,
        "release_profile": args.release_profile,
        "steps": results,
    }
    out = root / "reports" / "product_lifecycle_run.json"
    out.write_text(json.dumps(lifecycle, indent=2), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
