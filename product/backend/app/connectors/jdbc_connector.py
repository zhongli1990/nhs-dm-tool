import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from .base import SourceTargetConnector


class JdbcConnector(SourceTargetConnector):
    """
    JDBC connector with two modes:
    - `jdbc:sqlite:<path>` using built-in sqlite3 bridge (active)
    - generic JDBC via jaydebeapi when options are supplied (experimental)
    """

    def __init__(self, connection_string: str, schema_name: str = "", options: Optional[Dict[str, str]] = None):
        self.connection_string = connection_string
        self.schema_name = schema_name
        self.options = options or {}
        self.sample_limit_max = int(self.options.get("sample_limit_max", 1000))

    def list_tables(self) -> List[str]:
        if self.connection_string.startswith("jdbc:sqlite:"):
            with self._sqlite_conn() as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                return [str(r[0]) for r in cur.fetchall()]
        return self._jdbc_query_tables()

    def describe_table(self, table_name: str) -> List[Dict[str, str]]:
        if self.connection_string.startswith("jdbc:sqlite:"):
            with self._sqlite_conn() as conn:
                cur = conn.cursor()
                cur.execute(f"PRAGMA table_info('{table_name}')")
                rows = cur.fetchall()
                return [{"column_name": str(r[1]), "inferred_type": str(r[2] or "TEXT")} for r in rows]
        return self._jdbc_query_columns(table_name)

    def sample_rows(self, table_name: str, limit: int = 20) -> List[Dict[str, str]]:
        safe_limit = max(1, min(int(limit), self.sample_limit_max))
        if self.connection_string.startswith("jdbc:sqlite:"):
            with self._sqlite_conn() as conn:
                cur = conn.cursor()
                cur.execute(f"SELECT * FROM '{table_name}' LIMIT {safe_limit}")
                cols = [c[0] for c in cur.description or []]
                rows = cur.fetchall()
                return [{str(cols[i]): "" if row[i] is None else str(row[i]) for i in range(len(cols))} for row in rows]
        return self._jdbc_query_rows(table_name, safe_limit)

    def _sqlite_conn(self):
        db_path = self.connection_string.replace("jdbc:sqlite:", "", 1).strip()
        p = Path(db_path)
        if not p.exists():
            raise FileNotFoundError(f"SQLite file not found for JDBC sqlite mode: {db_path}")
        return sqlite3.connect(str(p))

    def _jdbc_connect(self):
        try:
            import jaydebeapi  # type: ignore
        except Exception as ex:
            raise NotImplementedError(
                "JDBC runtime unavailable. Use jdbc:sqlite:<path> or install jaydebeapi with driver options."
            ) from ex
        driver_class = self.options.get("driver_class")
        jars = self.options.get("jars")
        user = self.options.get("user", "")
        password = self.options.get("password", "")
        if not driver_class or not jars:
            raise NotImplementedError("JDBC connector requires options.driver_class and options.jars for generic mode.")
        return jaydebeapi.connect(driver_class, self.connection_string, [user, password], jars)

    def _jdbc_query_tables(self) -> List[str]:
        with self._jdbc_connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_SCHEMA, TABLE_NAME"
            )
            rows = cur.fetchall()
            return [f"{r[0]}.{r[1]}" for r in rows]

    def _jdbc_query_columns(self, table_name: str) -> List[Dict[str, str]]:
        schema, table = self._split_table_name(table_name)
        with self._jdbc_connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=? AND TABLE_NAME=? ORDER BY ORDINAL_POSITION",
                (schema, table),
            )
            rows = cur.fetchall()
            return [{"column_name": str(r[0]), "inferred_type": str(r[1])} for r in rows]

    def _jdbc_query_rows(self, table_name: str, limit: int) -> List[Dict[str, str]]:
        schema, table = self._split_table_name(table_name)
        with self._jdbc_connect() as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {schema}.{table} FETCH FIRST {limit} ROWS ONLY")
            cols = [c[0] for c in cur.description or []]
            rows = cur.fetchall()
            return [{str(cols[i]): "" if row[i] is None else str(row[i]) for i in range(len(cols))} for row in rows]

    def _split_table_name(self, table_name: str):
        if "." in table_name:
            schema, table = table_name.split(".", 1)
            return schema, table
        return (self.schema_name or "dbo"), table_name
