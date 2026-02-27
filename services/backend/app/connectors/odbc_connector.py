from typing import Dict, List, Optional

from .base import SourceTargetConnector


class OdbcConnector(SourceTargetConnector):
    """
    Read-oriented ODBC connector.
    Requires `pyodbc` in runtime environment.
    """

    def __init__(self, connection_string: str, schema_name: str = "", options: Optional[Dict[str, str]] = None):
        self.connection_string = connection_string
        self.schema_name = schema_name
        self.options = options or {}
        self.query_timeout = int(self.options.get("query_timeout", 30))
        self.sample_limit_max = int(self.options.get("sample_limit_max", 1000))

    def _connect(self):
        try:
            import pyodbc  # type: ignore
        except Exception as ex:
            raise NotImplementedError("ODBC runtime dependency missing. Install pyodbc to enable this connector.") from ex

        conn = pyodbc.connect(self.connection_string, timeout=self.query_timeout)
        return conn

    def list_tables(self) -> List[str]:
        query = "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
        params: List[str] = []
        if self.schema_name:
            query += " AND TABLE_SCHEMA = ?"
            params.append(self.schema_name)
        query += " ORDER BY TABLE_SCHEMA, TABLE_NAME"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()
        return [f"{r[0]}.{r[1]}" for r in rows]

    def describe_table(self, table_name: str) -> List[Dict[str, str]]:
        schema, table = self._split_table_name(table_name)
        query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            ORDER BY ORDINAL_POSITION
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(query, (schema, table))
            rows = cur.fetchall()
        return [{"column_name": str(r[0]), "inferred_type": str(r[1])} for r in rows]

    def sample_rows(self, table_name: str, limit: int = 20) -> List[Dict[str, str]]:
        schema, table = self._split_table_name(table_name)
        safe_limit = max(1, min(int(limit), self.sample_limit_max))
        query = f"SELECT TOP {safe_limit} * FROM [{schema}].[{table}]"
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(query)
            cols = [c[0] for c in cur.description or []]
            out = []
            for row in cur.fetchall():
                out.append({str(cols[i]): "" if row[i] is None else str(row[i]) for i in range(len(cols))})
        return out

    def _split_table_name(self, table_name: str):
        if "." in table_name:
            schema, table = table_name.split(".", 1)
            return schema, table
        return (self.schema_name or "dbo"), table_name
