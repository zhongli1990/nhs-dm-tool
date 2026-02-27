from typing import Dict, List


class JsonDummyConnector:
    """
    Dummy JSON connector placeholder.
    This is intentionally non-production and returns synthetic metadata/rows.
    """

    def __init__(self, connection_string: str, schema_name: str = ""):
        self.connection_string = connection_string
        self.schema_name = schema_name or "json"

    def list_tables(self) -> List[str]:
        return [f"{self.schema_name}.payload_documents", f"{self.schema_name}.message_events"]

    def describe_table(self, table_name: str) -> List[Dict[str, str]]:
        if table_name.endswith("payload_documents"):
            return [
                {"column_name": "document_id", "inferred_type": "string"},
                {"column_name": "source_system", "inferred_type": "string"},
                {"column_name": "payload_json", "inferred_type": "json"},
                {"column_name": "ingested_at", "inferred_type": "datetime"},
            ]
        return [
            {"column_name": "event_id", "inferred_type": "string"},
            {"column_name": "event_type", "inferred_type": "string"},
            {"column_name": "event_json", "inferred_type": "json"},
            {"column_name": "created_at", "inferred_type": "datetime"},
        ]

    def sample_rows(self, table_name: str, limit: int = 20) -> List[Dict[str, str]]:
        rows = []
        if table_name.endswith("payload_documents"):
            rows.append(
                {
                    "document_id": "DOC0001",
                    "source_system": "VENDOR_X",
                    "payload_json": '{"patient":{"mrn":"MRN10001"}}',
                    "ingested_at": "2026-02-25T00:00:00Z",
                }
            )
        else:
            rows.append(
                {
                    "event_id": "EVT0001",
                    "event_type": "MIGRATION_STATUS",
                    "event_json": '{"status":"QUEUED"}',
                    "created_at": "2026-02-25T00:00:00Z",
                }
            )
        return rows[: max(0, limit)]
