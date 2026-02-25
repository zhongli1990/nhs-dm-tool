import csv
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

from io_utils import read_csv, read_json


def _source_value(field_name: str, size: str, row_idx: int) -> str:
    name = field_name.lower()
    if "date" in name:
        return (date(1980, 1, 1) + timedelta(days=row_idx * 31)).strftime("%d/%m/%Y")
    if "time" in name:
        return "10:30"
    if "nhs" in name and "status" not in name:
        return f"9434765{900 + row_idx}"
    if "internalpatientnumber" in name:
        return f"MRN{10000 + row_idx}"
    if "episodenumber" in name:
        return f"{20000 + row_idx}"
    if "postcode" in name:
        return f"MK40 {row_idx}AA"
    if "sex" in name or "gender" in name:
        return "F" if row_idx % 2 == 0 else "M"
    if "name" in name:
        return f"VAL_{row_idx}_{field_name}"[: int(size or 30)]

    max_len = int(size) if size.isdigit() else 20
    if max_len <= 4:
        return str((row_idx % 9) + 1)[:max_len]
    return f"V{row_idx}_{field_name}"[:max_len]


def _write_csv(path: Path, headers: List[str], rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in rows:
            w.writerow({h: row.get(h, "") for h in headers})


def generate_mock_data(project_root: Path) -> None:
    source_catalog = read_csv(project_root / "schemas" / "source_schema_catalog.csv")
    target_catalog = read_csv(project_root / "schemas" / "target_schema_catalog.csv")

    source_tables = ["PATDATA", "ADMITDISCH"]
    target_tables = ["LOAD_PMI", "LOAD_ADT_ADMISSIONS"]

    for table in source_tables:
        fields = [r for r in source_catalog if r["table_name"] == table]
        headers = [r["field_name"] for r in fields]
        rows = []
        for idx in range(1, 4):
            row = {f["field_name"]: _source_value(f["field_name"], f.get("size", ""), idx) for f in fields}
            rows.append(row)
        _write_csv(project_root / "mock_data" / "source" / f"{table}.csv", headers, rows)

    for table in target_tables:
        fields = [r for r in target_catalog if r["table_name"] == table]
        headers = [r["field_name"] for r in fields]
        _write_csv(project_root / "mock_data" / "target" / f"{table}.csv", headers, [])


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    generate_mock_data(root)
    print("Mock data generated.")
