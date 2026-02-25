from pathlib import Path
from typing import Dict, List

from .csv_connector import CsvFolderConnector


class CacheIrisEmulatorConnector:
    """
    Basic Cache/IRIS emulator (source-side) backed by CSV source extracts.
    Exposes uppercase table identifiers to mimic legacy schema naming.
    """

    def __init__(self, folder: Path, schema_name: str = "INQUIRE"):
        self.folder = folder
        self.schema_name = schema_name or "INQUIRE"
        self._csv = CsvFolderConnector(folder)

    def list_tables(self) -> List[str]:
        return [f"{self.schema_name}.{t.upper()}" for t in self._csv.list_tables()]

    def describe_table(self, table_name: str) -> List[Dict[str, str]]:
        local = table_name.split(".")[-1].upper()
        cols = self._csv.describe_table(local)
        for c in cols:
            c["inferred_type"] = "varchar"
        return cols

    def sample_rows(self, table_name: str, limit: int = 20) -> List[Dict[str, str]]:
        local = table_name.split(".")[-1].upper()
        return self._csv.sample_rows(local, limit=limit)
