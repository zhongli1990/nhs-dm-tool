import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import MOCK_SOURCE_DIR, MOCK_TARGET_CONTRACT_DIR, REPORTS_DIR, SCHEMAS_DIR, DATA_MIGRATION_ROOT
from .connectors.registry import build_connector
from .models import ConnectorSpec
from .services.artifact_service import profile_schema, read_csv, read_json


app = FastAPI(
    title="NHS Data Migration Control Plane API",
    version="0.1.0",
    description="Enterprise migration API for schema, mapping, quality, and connector-driven exploration.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/schema/source")
def source_schema():
    rows = read_csv(SCHEMAS_DIR / "source_schema_catalog.csv")
    return {"tables": profile_schema(rows)}


@app.get("/api/schema/target")
def target_schema():
    rows = read_csv(SCHEMAS_DIR / "target_schema_catalog.csv")
    return {"tables": profile_schema(rows)}


@app.get("/api/schema/source/{table_name}")
def source_table_schema(table_name: str):
    rows = read_csv(SCHEMAS_DIR / "source_schema_catalog.csv")
    table_rows = [r for r in rows if r.get("table_name") == table_name]
    if not table_rows:
        raise HTTPException(status_code=404, detail=f"Source table not found: {table_name}")
    return {"table_name": table_name, "fields": table_rows}


@app.get("/api/schema/target/{table_name}")
def target_table_schema(table_name: str):
    rows = read_csv(SCHEMAS_DIR / "target_schema_catalog.csv")
    table_rows = [r for r in rows if r.get("table_name") == table_name]
    if not table_rows:
        raise HTTPException(status_code=404, detail=f"Target table not found: {table_name}")
    return {"table_name": table_name, "fields": table_rows}


@app.get("/api/mappings/contract")
def mapping_contract():
    summary = read_json(REPORTS_DIR / "mapping_contract_summary.json")
    rows = read_csv(REPORTS_DIR / "mapping_contract.csv")
    return {"summary": summary, "rows": rows}


@app.get("/api/mappings/contract/query")
def mapping_contract_query(
    target_table: Optional[str] = Query(default=None),
    mapping_class: Optional[str] = Query(default=None),
    limit: int = Query(default=500, ge=1, le=5000),
):
    rows = read_csv(REPORTS_DIR / "mapping_contract.csv")
    if target_table:
        rows = [r for r in rows if r.get("target_table") == target_table]
    if mapping_class:
        rows = [r for r in rows if r.get("mapping_class") == mapping_class]
    return {"row_count": len(rows), "rows": rows[:limit]}


@app.get("/api/runs/latest")
def latest_runs():
    return {
        "contract_migration": read_json(REPORTS_DIR / "contract_migration_report.json"),
        "enterprise_quality": read_json(REPORTS_DIR / "enterprise_pipeline_report.json"),
        "release_gates": read_json(REPORTS_DIR / "release_gate_report.json"),
    }


@app.get("/api/runs/history")
def runs_history():
    names = [
        "migration_run_report.json",
        "contract_migration_report.json",
        "enterprise_pipeline_report.json",
        "release_gate_report.json",
        "product_lifecycle_run.json",
    ]
    history = []
    for n in names:
        p = REPORTS_DIR / n
        payload = read_json(p)
        if payload:
            history.append({"report": n, "payload": payload})
    return {"reports": history}


@app.get("/api/rejects/crosswalk")
def crosswalk_rejects():
    return {"rows": read_csv(REPORTS_DIR / "contract_migration_rejects.csv")}


@app.get("/api/quality/issues")
def quality_issues(kind: str = Query(default="enterprise")):
    kind = kind.lower()
    if kind == "enterprise":
        return {"rows": read_csv(REPORTS_DIR / "enterprise_pipeline_issues.csv")}
    if kind == "contract":
        return {"rows": read_csv(REPORTS_DIR / "contract_migration_issues.csv")}
    if kind == "crosswalk_reject":
        return {"rows": read_csv(REPORTS_DIR / "contract_migration_rejects.csv")}
    raise HTTPException(status_code=400, detail="kind must be one of enterprise, contract, crosswalk_reject")


@app.get("/api/gates/profiles")
def gate_profiles():
    return read_json(DATA_MIGRATION_ROOT / "pipeline" / "release_gate_profiles.json")


@app.post("/api/connectors/explore")
def connector_explore(spec: ConnectorSpec):
    try:
        connector = build_connector(
            spec.connector_type,
            spec.connection_string,
            spec.schema_name,
            direction=spec.direction,
            options=spec.options,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex)) from ex
    except NotImplementedError as ex:
        raise HTTPException(status_code=501, detail=str(ex)) from ex
    tables = connector.list_tables()
    previews = {}
    for t in tables[:20]:
        previews[t] = {
            "columns": connector.describe_table(t)[:50],
            "sample_rows": connector.sample_rows(t, limit=5),
        }
    return {
        "connector_type": spec.connector_type,
        "direction": spec.direction,
        "table_count": len(tables),
        "tables": tables,
        "previews": previews,
    }


@app.get("/api/connectors/templates")
def connector_templates():
    return {
        "csv_source": {"connector_type": "csv", "connection_string": str(MOCK_SOURCE_DIR), "schema_name": "", "direction": "source", "options": {}},
        "csv_target": {"connector_type": "csv", "connection_string": str(MOCK_TARGET_CONTRACT_DIR), "schema_name": "", "direction": "target", "options": {}},
        "postgresql_emulator": {"connector_type": "postgres_emulator", "connection_string": str(MOCK_TARGET_CONTRACT_DIR), "schema_name": "public", "direction": "target", "options": {"engine": "postgresql_emulator"}},
        "cache_iris_emulator": {"connector_type": "cache_iris_emulator", "connection_string": str(MOCK_SOURCE_DIR), "schema_name": "INQUIRE", "direction": "source", "options": {"engine": "cache_iris_emulator"}},
        "json_dummy": {"connector_type": "json_dummy", "connection_string": "json://dummy", "schema_name": "json", "direction": "source", "options": {"engine": "json_dummy"}},
        "odbc": {"connector_type": "odbc", "connection_string": "Driver={ODBC Driver};Server=host;Database=db;Trusted_Connection=yes;", "schema_name": "dbo"},
        "jdbc": {"connector_type": "jdbc", "connection_string": "jdbc:sqlserver://host:1433;databaseName=db;encrypt=true;", "schema_name": "dbo"},
    }


@app.get("/api/connectors/types")
def connector_types():
    return {
        "types": [
            {"id": "csv", "label": "CSV Folder", "mode": "real", "direction": "source_or_target"},
            {"id": "postgres_emulator", "label": "PostgreSQL Emulator (Target)", "mode": "emulator", "direction": "target"},
            {"id": "cache_iris_emulator", "label": "Cache/IRIS Emulator (Source)", "mode": "emulator", "direction": "source"},
            {"id": "json_dummy", "label": "JSON Dummy Connector", "mode": "dummy", "direction": "source_or_target"},
            {"id": "odbc", "label": "ODBC Connector", "mode": "stub", "direction": "source_or_target"},
            {"id": "jdbc", "label": "JDBC Connector", "mode": "stub", "direction": "source_or_target"},
        ]
    }


@app.get("/api/connectors/default/csv-source")
def default_csv_source():
    connector = build_connector("csv", str(Path(MOCK_SOURCE_DIR)))
    tables = connector.list_tables()
    return {"table_count": len(tables), "tables": tables}


@app.get("/api/connectors/default/csv-target-contract")
def default_csv_target_contract():
    connector = build_connector("csv", str(Path(MOCK_TARGET_CONTRACT_DIR)))
    tables = connector.list_tables()
    return {"table_count": len(tables), "tables": tables}


@app.post("/api/runs/execute")
def execute_lifecycle(
    rows: int = Query(default=20, ge=1, le=100000),
    seed: int = Query(default=42, ge=0, le=999999),
    min_patients: int = Query(default=20, ge=1, le=100000),
    release_profile: str = Query(default="pre_production"),
):
    cmd = [
        "python",
        "pipeline/run_product_lifecycle.py",
        "--rows",
        str(rows),
        "--seed",
        str(seed),
        "--min-patients",
        str(min_patients),
        "--release-profile",
        release_profile,
    ]
    proc = subprocess.run(cmd, cwd=str(DATA_MIGRATION_ROOT), capture_output=True, text=True)
    payload = read_json(REPORTS_DIR / "product_lifecycle_run.json")
    return {
        "command": " ".join(cmd),
        "return_code": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "report": payload,
    }
