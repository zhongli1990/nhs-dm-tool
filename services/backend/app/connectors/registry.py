from pathlib import Path

from ..config import MOCK_SOURCE_DIR, MOCK_TARGET_CONTRACT_DIR
from .csv_connector import CsvFolderConnector
from .iris_emulator_connector import CacheIrisEmulatorConnector
from .jdbc_connector import JdbcConnector
from .json_dummy_connector import JsonDummyConnector
from .odbc_connector import OdbcConnector
from .postgres_emulator_connector import PostgresEmulatorConnector


def build_connector(connector_type: str, connection_string: str, schema_name: str = "", direction: str = "source", options=None):
    options = options or {}
    t = (connector_type or "").strip().lower()
    if t == "csv":
        folder = Path(connection_string) if connection_string else (MOCK_SOURCE_DIR if direction == "source" else MOCK_TARGET_CONTRACT_DIR)
        return CsvFolderConnector(folder)
    if t in {"postgresql", "postgres_emulator"}:
        folder = Path(connection_string) if connection_string else MOCK_TARGET_CONTRACT_DIR
        return PostgresEmulatorConnector(folder=folder, schema_name=schema_name or options.get("schema_name", "public"))
    if t in {"cache_iris", "cache_iris_emulator", "iris"}:
        folder = Path(connection_string) if connection_string else MOCK_SOURCE_DIR
        return CacheIrisEmulatorConnector(folder=folder, schema_name=schema_name or options.get("schema_name", "INQUIRE"))
    if t in {"json", "json_dummy"}:
        return JsonDummyConnector(connection_string=connection_string, schema_name=schema_name or options.get("schema_name", "json"))
    if t == "odbc":
        return OdbcConnector(connection_string=connection_string, schema_name=schema_name, options=options)
    if t == "jdbc":
        return JdbcConnector(connection_string=connection_string, schema_name=schema_name, options=options)
    raise ValueError(f"Unsupported connector_type: {connector_type}")
