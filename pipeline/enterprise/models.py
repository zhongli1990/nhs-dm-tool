from dataclasses import dataclass


@dataclass
class DataIssue:
    severity: str
    category: str
    table_name: str
    field_name: str
    record_id: str
    message: str

