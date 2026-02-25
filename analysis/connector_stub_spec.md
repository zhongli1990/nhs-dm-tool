# ODBC/JDBC Connector Stub Specification

Date: 2026-02-25

## Scope

Define production-ready placeholder contracts for connector adapters while DB driver integration is pending.

Implemented modules:
- `product/backend/app/connectors/odbc_connector.py`
- `product/backend/app/connectors/jdbc_connector.py`
- `product/backend/app/connectors/postgres_emulator_connector.py`
- `product/backend/app/connectors/iris_emulator_connector.py`
- `product/backend/app/connectors/json_dummy_connector.py`

## Interface contract

Both connectors implement:
1. `list_tables() -> List[str]`
2. `describe_table(table_name) -> List[Dict[str, str]]`
3. `sample_rows(table_name, limit=20) -> List[Dict[str, str]]`

## Placeholder assumptions populated

### PostgreSQL emulator (target)

Assumed schema:
`public`

Assumed behavior:
- reads `mock_data/target_contract/*.csv`
- exposes schema-qualified table names
- provides column list and sample rows

### Cache/IRIS emulator (source)

Assumed schema:
`INQUIRE`

Assumed behavior:
- reads `mock_data/source/*.csv`
- exposes IRIS-style table naming
- provides column list and sample rows

### JSON dummy connector

Assumed behavior:
- returns synthetic JSON payload/event table structures
- supports UI/API integration testing without live JSON source

## JDBC/ODBC stubs

### ODBC

Assumed connection string pattern:
`Driver={ODBC Driver};Server=host;Database=db;Trusted_Connection=yes;`

Assumed runtime controls:
- read-only DB principal
- statement timeout
- max sample row limit
- schema filter support
- operation audit logging

### JDBC

Assumed connection string pattern:
`jdbc:sqlserver://host:1433;databaseName=db;encrypt=true;`

Assumed runtime controls:
- managed JDBC driver loading
- read-only transaction scope
- paginated metadata and sample pulls
- connector health-check endpoint

## Planned implementation sequence

1. Add secure secret provider integration for credentials.
2. Add database driver support and connection pooling.
3. Implement metadata introspection queries per vendor.
4. Add robust error classes and connector telemetry.
