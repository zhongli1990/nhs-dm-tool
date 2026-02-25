from typing import Dict, Optional

from pydantic import BaseModel


class ConnectorSpec(BaseModel):
    connector_type: str
    connection_string: str
    schema_name: str = ""
    direction: str = "source"
    options: Dict[str, str] = {}


class TableProfile(BaseModel):
    table_name: str
    column_count: int
    field_count: int
