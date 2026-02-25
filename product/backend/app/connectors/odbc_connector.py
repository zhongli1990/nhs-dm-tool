from typing import Dict, List

from .base import SourceTargetConnector


class OdbcConnector(SourceTargetConnector):
    """
    Adapter stub for future production implementation.
    Expected implementation path:
    - pyodbc connection management
    - information_schema introspection
    - paged row sampling with query timeout + read-only role
    """

    def __init__(self, connection_string: str, schema_name: str = ""):
        self.connection_string = connection_string
        self.schema_name = schema_name

    def list_tables(self) -> List[str]:
        raise NotImplementedError("ODBC connector plugin not yet enabled in this build.")

    def describe_table(self, table_name: str) -> List[Dict[str, str]]:
        raise NotImplementedError("ODBC connector plugin not yet enabled in this build.")

    def sample_rows(self, table_name: str, limit: int = 20) -> List[Dict[str, str]]:
        raise NotImplementedError("ODBC connector plugin not yet enabled in this build.")
