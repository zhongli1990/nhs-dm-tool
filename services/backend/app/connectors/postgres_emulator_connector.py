from pathlib import Path
from typing import Dict, List

from .csv_connector import CsvFolderConnector


class PostgresEmulatorConnector:
    """
    Basic PostgreSQL emulator (target-side) backed by CSV tables.
    Assumes CSV filenames represent target table names within a schema.
    """

    def __init__(self, folder: Path, schema_name: str = "public"):
        self.folder = folder
        self.schema_name = schema_name or "public"
        self._csv = CsvFolderConnector(folder)

    def list_tables(self) -> List[str]:
        return [f"{self.schema_name}.{t.lower()}" for t in self._csv.list_tables()]

    def describe_table(self, table_name: str) -> List[Dict[str, str]]:
        local = table_name.split(".")[-1]
        # target CSVs are uppercase LOAD_ names
        upper_name = local.upper()
        cols = self._csv.describe_table(upper_name)
        for c in cols:
            c["column_name"] = c["column_name"].lower()
            c["inferred_type"] = "text"
        return cols

    def sample_rows(self, table_name: str, limit: int = 20) -> List[Dict[str, str]]:
        local = table_name.split(".")[-1]
        upper_name = local.upper()
        rows = self._csv.sample_rows(upper_name, limit=limit)
        out = []
        for r in rows:
            out.append({k.lower(): v for k, v in r.items()})
        return out
