from typing import Dict, List

from .base import SourceTargetConnector


class JdbcConnector(SourceTargetConnector):
    """
    Adapter stub for future production implementation.
    Expected implementation path:
    - jaydebeapi / custom JVM bridge
    - secure credential vault integration
    - schema catalog + sampling APIs
    """

    def __init__(self, connection_string: str, schema_name: str = ""):
        self.connection_string = connection_string
        self.schema_name = schema_name

    def list_tables(self) -> List[str]:
        raise NotImplementedError("JDBC connector plugin not yet enabled in this build.")

    def describe_table(self, table_name: str) -> List[Dict[str, str]]:
        raise NotImplementedError("JDBC connector plugin not yet enabled in this build.")

    def sample_rows(self, table_name: str, limit: int = 20) -> List[Dict[str, str]]:
        raise NotImplementedError("JDBC connector plugin not yet enabled in this build.")
