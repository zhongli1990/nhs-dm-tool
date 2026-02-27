import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List


def read_json(path: Path) -> Dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def profile_schema(catalog_rows: List[Dict[str, str]], table_key: str = "table_name") -> List[Dict[str, object]]:
    grouped = defaultdict(list)
    for row in catalog_rows:
        grouped[row.get(table_key, "")].append(row)
    out = []
    for table_name in sorted(k for k in grouped.keys() if k):
        rows = grouped[table_name]
        out.append(
            {
                "table_name": table_name,
                "column_count": len(rows),
                "columns": [r.get("field_name", "") for r in rows if r.get("field_name", "")],
            }
        )
    return out
