import csv
from pathlib import Path
from typing import Dict, List

from .base import SourceTargetConnector


class CsvFolderConnector(SourceTargetConnector):
    def __init__(self, folder: Path):
        self.folder = folder

    def list_tables(self) -> List[str]:
        if not self.folder.exists():
            return []
        return sorted(p.stem for p in self.folder.glob("*.csv"))

    def describe_table(self, table_name: str) -> List[Dict[str, str]]:
        path = self.folder / f"{table_name}.csv"
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as f:
            headers = next(csv.reader(f), [])
        return [{"column_name": h, "inferred_type": "string"} for h in headers]

    def sample_rows(self, table_name: str, limit: int = 20) -> List[Dict[str, str]]:
        path = self.folder / f"{table_name}.csv"
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        return rows[: max(0, limit)]
