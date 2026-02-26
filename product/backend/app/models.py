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


class MappingWorkbenchUpdate(BaseModel):
    workbench_id: str
    mapping_class: Optional[str] = None
    primary_source_table: Optional[str] = None
    primary_source_field: Optional[str] = None
    transformation_rule: Optional[str] = None
    notes: Optional[str] = None
    updated_by: str = "ui_user"


class MappingWorkbenchTransition(BaseModel):
    workbench_id: str
    status: str
    updated_by: str = "ui_user"
    notes: Optional[str] = None
