import json
import os
import re
import subprocess
import random
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import MOCK_SOURCE_DIR, MOCK_TARGET_CONTRACT_DIR, REPORTS_DIR, SCHEMAS_DIR, DATA_MIGRATION_ROOT
from .connectors.registry import build_connector
from .models import (
    AuthLoginRequest,
    AuthRegisterRequest,
    ConnectorSpec,
    ContextSwitchRequest,
    CreateNameRequest,
    MappingWorkbenchTransition,
    MappingWorkbenchUpdate,
    RegistrationReviewRequest,
)
from .audit_store import AuditStore
from .saas_store import DEFAULT_DMM_PERMISSIONS, SaaSStore
from .security import create_token, decode_token, parse_bearer_token
from .services.artifact_service import profile_schema, read_csv, read_json
from .state_store import RuntimeStateStore


app = FastAPI(
    title="OpenLI DMM API",
    version="0.2.4",
    description="OpenLI DMM multi-tenant migration API for schema, mapping, quality, lifecycle, and enterprise onboarding.",
)

_allow_origins = os.environ.get("DM_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAPPING_WORKBENCH_FILE = REPORTS_DIR / "mapping_workbench.json"
QUALITY_HISTORY_FILE = REPORTS_DIR / "quality_history.json"
QUALITY_KPI_CONFIG_FILE = REPORTS_DIR / "quality_kpi_config.json"
SNAPSHOT_DIR = REPORTS_DIR / "snapshots"
SAAS_STORE_FILE = DATA_MIGRATION_ROOT / "services" / "backend" / "data" / "saas_store.json"
VERSION_MANIFEST_FILE = DATA_MIGRATION_ROOT / "services" / "version_manifest.json"
saas_store = SaaSStore(SAAS_STORE_FILE)
state_store = RuntimeStateStore(
    backend=os.environ.get("DM_STATE_BACKEND", "postgres"),
    database_url=os.environ.get("DM_DATABASE_URL", ""),
    mapping_workbench_file=MAPPING_WORKBENCH_FILE,
    quality_history_file=QUALITY_HISTORY_FILE,
    quality_kpi_config_file=QUALITY_KPI_CONFIG_FILE,
)
audit_store = AuditStore(
    backend=os.environ.get("DM_AUDIT_BACKEND", "postgres"),
    database_url=os.environ.get("DM_DATABASE_URL", ""),
)
PUBLIC_API_PATHS = {
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/orgs",
}
DEFAULT_QUALITY_KPIS = [
    {"id": "error_count", "label": "DQ Errors", "threshold": 0, "direction": "max", "enabled": True, "format": "int"},
    {"id": "warning_count", "label": "DQ Warnings", "threshold": 20, "direction": "max", "enabled": True, "format": "int"},
    {"id": "crosswalk_rejects", "label": "Crosswalk Rejects", "threshold": 0, "direction": "max", "enabled": True, "format": "int"},
    {"id": "population_ratio", "label": "Population Ratio", "threshold": 0.55, "direction": "min", "enabled": True, "format": "pct"},
    {"id": "tables_written", "label": "Tables Written", "threshold": 38, "direction": "min", "enabled": True, "format": "int"},
    {"id": "unresolved_mapping", "label": "Unresolved Mapping", "threshold": 10, "direction": "max", "enabled": True, "format": "int"},
]

DEFAULT_VERSION_MANIFEST = {
    "product_name": "OpenLI DMM",
    "current_version": "0.2.4",
    "released_on": "2026-02-27",
    "history": [
        {"version": "0.0.1", "released_on": "2026-02-26", "summary": "Baseline lifecycle control plane and migration pipeline."},
        {"version": "0.0.5", "released_on": "2026-02-27", "summary": "UX hardening, mapping workbench scale features, ERD and quality upgrades."},
        {"version": "0.2.0", "released_on": "2026-02-27", "summary": "SaaS baseline: auth, tenancy model, onboarding/settings, compact context UX."},
        {"version": "0.2.1", "released_on": "2026-02-27", "summary": "Connector preview UX fix, table pagination default 10, version metadata display, lifecycle doc alignment."},
        {"version": "0.2.2", "released_on": "2026-02-27", "summary": "Dockerized enterprise full-stack architecture, postgres integration, and merged 0.2.1 feature line into services runtime."},
        {"version": "0.2.3", "released_on": "2026-02-27", "summary": "PostgreSQL-backed identity/RBAC and runtime state hardening for mapping and quality control-plane data."},
        {"version": "0.2.4", "released_on": "2026-02-27", "summary": "Alembic migration governance and immutable audit-event trail for mission-critical enterprise operations."},
    ],
}


def _read_version_manifest() -> Dict[str, object]:
    if not VERSION_MANIFEST_FILE.exists():
        VERSION_MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
        VERSION_MANIFEST_FILE.write_text(json.dumps(DEFAULT_VERSION_MANIFEST, indent=2), encoding="utf-8")
        return DEFAULT_VERSION_MANIFEST
    payload = read_json(VERSION_MANIFEST_FILE)
    if not isinstance(payload, dict):
        return DEFAULT_VERSION_MANIFEST
    merged = dict(DEFAULT_VERSION_MANIFEST)
    merged.update(payload)
    if not isinstance(merged.get("history"), list):
        merged["history"] = list(DEFAULT_VERSION_MANIFEST["history"])
    return merged


def _permissions_for_actor(actor: Dict[str, object]) -> set:
    token_permissions = actor.get("permissions")
    if isinstance(token_permissions, list) and token_permissions:
        return set(str(p) for p in token_permissions)
    role = str(actor.get("role", "org_dm_engineer"))
    try:
        return set(saas_store.list_permissions_for_role(role))
    except Exception:
        return set(DEFAULT_DMM_PERMISSIONS.get(role, set()))


def _require_permission(request: Request, permission: str) -> Dict[str, object]:
    actor = getattr(request.state, "actor", None)
    if not actor:
        raise HTTPException(status_code=401, detail="authentication required")
    perms = _permissions_for_actor(actor)
    if "*" in perms or permission in perms:
        return actor
    raise HTTPException(status_code=403, detail=f"missing permission: {permission}")


def _request_context(request: Optional[Request]) -> Dict[str, str]:
    if request is None:
        return {"request_id": str(uuid.uuid4()), "request_ip": "", "user_agent": ""}
    rid = request.headers.get("x-request-id", "").strip() or str(uuid.uuid4())
    xff = request.headers.get("x-forwarded-for", "").strip()
    request_ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "")
    user_agent = request.headers.get("user-agent", "")
    return {"request_id": rid, "request_ip": request_ip, "user_agent": user_agent}


def _audit_event(
    request: Optional[Request],
    *,
    event_type: str,
    outcome: str,
    target_type: str = "",
    target_id: str = "",
    details: Optional[Dict[str, object]] = None,
    actor_override: Optional[Dict[str, object]] = None,
) -> None:
    actor = actor_override or (getattr(request.state, "actor", None) if request else None) or {}
    ctx = _request_context(request)
    audit_store.record(
        event_type=event_type,
        outcome=outcome,
        actor_user_id=str(actor.get("sub", "")),
        actor_role=str(actor.get("role", "")),
        actor_org_id=str(actor.get("org_id", "")),
        actor_workspace_id=str(actor.get("workspace_id", "")),
        actor_project_id=str(actor.get("project_id", "")),
        target_type=target_type,
        target_id=target_id,
        request_id=ctx["request_id"],
        request_ip=ctx["request_ip"],
        user_agent=ctx["user_agent"],
        details=details or {},
    )


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # Let CORS preflight pass through without bearer enforcement.
    if request.method.upper() == "OPTIONS":
        return await call_next(request)

    path = request.url.path
    if path.startswith("/api") and path not in PUBLIC_API_PATHS:
        token = parse_bearer_token(request.headers.get("Authorization", ""))
        if not token:
            return JSONResponse(status_code=401, content={"detail": "missing bearer token"})
        try:
            payload = decode_token(token)
        except ValueError as ex:
            return JSONResponse(status_code=401, content={"detail": str(ex)})
        request.state.actor = payload
    return await call_next(request)


def _lifecycle_steps(rows: int, seed: int, min_patients: int, release_profile: str) -> List[Dict[str, object]]:
    impute_mode = "pre_production" if release_profile in {"development", "pre_production"} else "strict"
    return [
        {
            "id": "extract_specs",
            "name": "Extract Specs",
            "description": "Parse requirement specs into source/target schema catalogs.",
            "command": ["python", "pipeline/extract_specs.py"],
        },
        {
            "id": "generate_mock_data",
            "name": "Generate Mock Data",
            "description": "Generate coherent source/target mock data for configured patient cohort.",
            "command": ["python", "pipeline/generate_all_mock_data.py", "--rows", str(rows), "--seed", str(seed)],
        },
        {
            "id": "analyze_semantic_mapping",
            "name": "Analyze Semantic Mapping",
            "description": "Build source-to-target semantic mapping matrix and summary.",
            "command": ["python", "pipeline/analyze_semantic_mapping.py"],
        },
        {
            "id": "build_mapping_contract",
            "name": "Build Mapping Contract",
            "description": "Classify all target fields into strict contract mapping classes.",
            "command": ["python", "pipeline/build_mapping_contract.py"],
        },
        {
            "id": "run_contract_migration",
            "name": "Run Contract Migration",
            "description": "Execute contract-driven ETL from source extracts to target contract outputs.",
            "command": [
                "python",
                "pipeline/run_contract_migration.py",
                "--source-dir",
                "mock_data/source",
                "--output-dir",
                "mock_data/target_contract",
                "--contract-file",
                "reports/mapping_contract.csv",
                "--target-catalog-file",
                "schemas/target_schema_catalog.csv",
                "--crosswalk-dir",
                "schemas/crosswalks",
                "--impute-mode",
                impute_mode,
            ],
        },
        {
            "id": "run_enterprise_quality",
            "name": "Run Enterprise Quality",
            "description": "Run enterprise validation checks and produce severity issues.",
            "command": ["python", "pipeline/run_enterprise_pipeline.py", "--min-patients", str(min_patients)],
        },
        {
            "id": "run_release_gates",
            "name": "Run Release Gates",
            "description": "Evaluate release profile gates for readiness decision.",
            "command": ["python", "pipeline/run_release_gates.py", "--profile", release_profile],
        },
    ]


def _read_quality_history() -> List[Dict[str, object]]:
    return state_store.read_quality_history()


def _write_quality_history(history: List[Dict[str, object]]) -> None:
    state_store.write_quality_history(history)


def _read_quality_kpis() -> List[Dict[str, object]]:
    payload = state_store.read_quality_kpis(DEFAULT_QUALITY_KPIS)
    normalized = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        normalized.append(
            {
                "id": str(row.get("id", "")),
                "label": str(row.get("label", "")),
                "threshold": float(row.get("threshold", 0) or 0),
                "direction": "min" if str(row.get("direction", "max")).lower() == "min" else "max",
                "enabled": bool(row.get("enabled", True)),
                "format": "pct" if str(row.get("format", "int")).lower() == "pct" else "int",
            }
        )
    if not normalized:
        state_store.write_quality_kpis(DEFAULT_QUALITY_KPIS)
        return DEFAULT_QUALITY_KPIS
    return normalized


def _write_quality_kpis(rows: List[Dict[str, object]]) -> None:
    state_store.write_quality_kpis(rows)


def _snapshot_payload() -> Dict[str, object]:
    contract = read_json(REPORTS_DIR / "contract_migration_report.json")
    enterprise = read_json(REPORTS_DIR / "enterprise_pipeline_report.json")
    gates = read_json(REPORTS_DIR / "release_gate_report.json")
    unresolved = 0
    for c in gates.get("checks", []):
        if c.get("gate") == "UNRESOLVED_MAPPING_THRESHOLD":
            unresolved = int(c.get("actual", 0))
            break
    return {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "error_count": int(enterprise.get("severity_counts", {}).get("ERROR", 0)),
        "warning_count": int(enterprise.get("severity_counts", {}).get("WARN", 0)) + int(contract.get("issue_counts", {}).get("WARN", 0)),
        "crosswalk_rejects": int(contract.get("crosswalk_reject_count", 0)),
        "population_ratio": float(contract.get("overall_column_population_ratio", 0) or 0),
        "tables_written": int(contract.get("tables_written", 0)),
        "unresolved_mapping": unresolved,
        "release_status": gates.get("status", "UNKNOWN"),
    }


def _find_col(rows: List[Dict[str, object]], candidates: List[str]) -> Optional[str]:
    if not rows:
        return None
    first = rows[0]
    lookup = {str(k).lower(): k for k in first.keys()}
    for c in candidates:
        hit = lookup.get(c.lower())
        if hit:
            return hit
    return None


def _nonnul(v: object) -> str:
    return str(v or "").strip()


def _is_valid_postcode(v: str) -> bool:
    s = v.strip().upper().replace(" ", "")
    if not s:
        return False
    return bool(re.match(r"^[A-Z]{1,2}[0-9][0-9A-Z]?[0-9][A-Z]{2}$", s))


def _compute_source_kpi_rows() -> List[Dict[str, object]]:
    pat_rows = read_csv(DATA_MIGRATION_ROOT / "mock_data" / "source" / "PATDATA.csv")
    opa_rows = read_csv(DATA_MIGRATION_ROOT / "mock_data" / "source" / "OPA.csv")
    if not pat_rows:
        return []

    nhs_col = _find_col(pat_rows, ["NhsNumber", "NHSNumber", "nhsnumber"])
    dob_col = _find_col(pat_rows, ["Dob", "DateOfBirth", "DOB", "InternalDateOfBirth"])
    post_col = _find_col(pat_rows, ["Postcode", "PostCode", "PseudoPostCode"])
    gp_col = _find_col(pat_rows, ["GpCode", "RegGpCode", "EpiGp"])
    practice_col = _find_col(pat_rows, ["PracticeCode", "EpiGpPracticeCode"])
    ethnic_col = _find_col(pat_rows, ["EthnicType", "Ethnicity", "EthnicCategory"])
    a1_col = _find_col(pat_rows, ["ExtAddressLine1", "Address1", "PatAddress1"])
    a2_col = _find_col(pat_rows, ["ExtAddressLine2", "Address2", "PatAddress2"])
    a3_col = _find_col(pat_rows, ["ExtAddressLine3", "Address3", "PatAddress3"])

    nhs_values = [_nonnul(r.get(nhs_col, "")) for r in pat_rows] if nhs_col else []
    nhs_nonblank = [v for v in nhs_values if v]
    dup_count = len(nhs_nonblank) - len(set(nhs_nonblank))
    missing_nhs = len([v for v in nhs_values if not v])
    invalid_nhs = len([v for v in nhs_nonblank if not re.match(r"^\d{10}$", v)])

    postcode_values = [_nonnul(r.get(post_col, "")) for r in pat_rows] if post_col else []
    missing_postcode = len([v for v in postcode_values if not v])
    invalid_postcode = len([v for v in postcode_values if v and not _is_valid_postcode(v)])

    missing_gp = len([r for r in pat_rows if not _nonnul(r.get(gp_col, ""))]) if gp_col else len(pat_rows)
    missing_practice = len([r for r in pat_rows if not _nonnul(r.get(practice_col, ""))]) if practice_col else len(pat_rows)
    missing_dob = len([r for r in pat_rows if not _nonnul(r.get(dob_col, ""))]) if dob_col else len(pat_rows)
    missing_ethnic = len([r for r in pat_rows if not _nonnul(r.get(ethnic_col, ""))]) if ethnic_col else len(pat_rows)

    long_addr = 0
    for r in pat_rows:
        lines = []
        if a1_col:
            lines.append(_nonnul(r.get(a1_col, "")))
        if a2_col:
            lines.append(_nonnul(r.get(a2_col, "")))
        if a3_col:
            lines.append(_nonnul(r.get(a3_col, "")))
        if any(len(x) > 35 for x in lines) or any(len(_nonnul(r.get(post_col, ""))) > 8 for _ in [0] if post_col):
            long_addr += 1

    unoutcomed = 0
    if opa_rows:
        dispo_col = _find_col(opa_rows, ["Disposal", "Outcome"])
        status_col = _find_col(opa_rows, ["ApptStatus", "AppointmentStatus"])
        for r in opa_rows:
            dispo = _nonnul(r.get(dispo_col, "")) if dispo_col else ""
            status = _nonnul(r.get(status_col, "")).upper() if status_col else ""
            if not dispo or status in {"", "BOOKED", "PENDING", "NATT"}:
                unoutcomed += 1

    total = max(len(pat_rows), 1)
    return [
        {"id": "duplicate_nhs_numbers", "label": "Duplicate NHS Numbers", "value": dup_count, "threshold": 0, "direction": "max", "format": "int", "denominator": total},
        {"id": "incomplete_nhs_numbers", "label": "Incomplete NHS Numbers", "value": missing_nhs, "threshold": 0, "direction": "max", "format": "int", "denominator": total},
        {"id": "invalid_nhs_numbers", "label": "Invalid NHS Numbers", "value": invalid_nhs, "threshold": 0, "direction": "max", "format": "int", "denominator": total},
        {"id": "incomplete_postcodes", "label": "Incomplete Postcodes", "value": missing_postcode, "threshold": 0, "direction": "max", "format": "int", "denominator": total},
        {"id": "invalid_postcodes", "label": "Invalid Postcodes", "value": invalid_postcode, "threshold": 0, "direction": "max", "format": "int", "denominator": total},
        {"id": "incomplete_current_gp", "label": "Incomplete Current GP", "value": missing_gp, "threshold": 0, "direction": "max", "format": "int", "denominator": total},
        {"id": "incomplete_gp_practice", "label": "Incomplete GP Practice", "value": missing_practice, "threshold": 0, "direction": "max", "format": "int", "denominator": total},
        {"id": "incomplete_date_of_birth", "label": "Incomplete Date of Birth", "value": missing_dob, "threshold": 0, "direction": "max", "format": "int", "denominator": total},
        {"id": "incomplete_ethnic_category", "label": "Incomplete Ethnic Category", "value": missing_ethnic, "threshold": 0, "direction": "max", "format": "int", "denominator": total},
        {"id": "address_postcode_length_breach", "label": "Address/postcode length breach", "value": long_addr, "threshold": 0, "direction": "max", "format": "int", "denominator": total},
        {"id": "unoutcomed_appointments_historical", "label": "Un-outcomed appointments - historical", "value": unoutcomed, "threshold": 0, "direction": "max", "format": "int", "denominator": max(len(opa_rows), 1)},
    ]


def _metric_from_point(point: Dict[str, object], kpi_id: str) -> float:
    if kpi_id in point:
        return float(point.get(kpi_id, 0) or 0)
    return float(
        {
            "error_count": point.get("error_count", 0),
            "warning_count": point.get("warning_count", 0),
            "crosswalk_rejects": point.get("crosswalk_rejects", 0),
            "population_ratio": point.get("population_ratio", 0),
            "tables_written": point.get("tables_written", 0),
            "unresolved_mapping": point.get("unresolved_mapping", 0),
        }.get(kpi_id, 0)
        or 0
    )


def _synthetic_trend(seed_key: str, current: float, weeks: int) -> List[float]:
    rng = random.Random(f"{seed_key}:{int(current)}:{weeks}")
    out = []
    base = max(0.0, float(current))
    for i in range(weeks):
        factor = (weeks - i) / max(weeks, 1)
        jitter = rng.uniform(-0.2, 0.2)
        v = max(0.0, base * (0.7 + 0.3 * factor + jitter * 0.15))
        out.append(round(v, 4))
    if out:
        out[-1] = round(base, 4)
    return out


def _record_quality_snapshot(event: str) -> Dict[str, object]:
    history = _read_quality_history()
    payload = _snapshot_payload()
    payload["event"] = event
    history.append(payload)
    _write_quality_history(history)
    return payload


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _create_snapshot(label: str) -> str:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    snap_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"_{label}"
    root = SNAPSHOT_DIR / snap_id
    root.mkdir(parents=True, exist_ok=True)

    report_files = [
        "contract_migration_report.json",
        "enterprise_pipeline_report.json",
        "release_gate_report.json",
        "product_lifecycle_run.json",
        "contract_migration_issues.csv",
        "enterprise_pipeline_issues.csv",
        "contract_migration_rejects.csv",
    ]
    for fn in report_files:
        _copy_if_exists(REPORTS_DIR / fn, root / "reports" / fn)

    target_contract_dir = DATA_MIGRATION_ROOT / "mock_data" / "target_contract"
    if target_contract_dir.exists():
        for p in target_contract_dir.glob("*.csv"):
            _copy_if_exists(p, root / "target_contract" / p.name)

    metadata = {
        "snapshot_id": snap_id,
        "label": label,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "quality": _snapshot_payload(),
    }
    (root / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return snap_id


def _list_snapshots() -> List[Dict[str, object]]:
    if not SNAPSHOT_DIR.exists():
        return []
    out = []
    for d in sorted([p for p in SNAPSHOT_DIR.iterdir() if p.is_dir()], reverse=True):
        meta = read_json(d / "metadata.json")
        if meta:
            out.append(meta)
    return out


def _restore_snapshot(snapshot_id: str) -> None:
    root = SNAPSHOT_DIR / snapshot_id
    if not root.exists():
        raise FileNotFoundError(snapshot_id)
    for p in (root / "reports").glob("*"):
        _copy_if_exists(p, REPORTS_DIR / p.name)
    target_contract_dir = DATA_MIGRATION_ROOT / "mock_data" / "target_contract"
    target_contract_dir.mkdir(parents=True, exist_ok=True)
    for p in target_contract_dir.glob("*.csv"):
        p.unlink(missing_ok=True)
    for p in (root / "target_contract").glob("*.csv"):
        _copy_if_exists(p, target_contract_dir / p.name)


def _bootstrap_workbench() -> List[Dict[str, object]]:
    rows = read_csv(REPORTS_DIR / "mapping_contract.csv")
    out = []
    now = datetime.now(timezone.utc).isoformat()
    for r in rows:
        key = f"{r.get('target_table','')}::{r.get('target_field','')}"
        out.append(
            {
                "workbench_id": key,
                "target_table": r.get("target_table", ""),
                "target_field": r.get("target_field", ""),
                "mapping_class": r.get("mapping_class", ""),
                "primary_source_table": r.get("primary_source_table", ""),
                "primary_source_field": r.get("primary_source_field", ""),
                "transformation_rule": r.get("transformation_rule", ""),
                "status": "DRAFT",
                "notes": "",
                "last_updated_by": "system_bootstrap",
                "last_updated_at_utc": now,
            }
        )
    state_store.write_workbench(out)
    return out


def _read_workbench() -> List[Dict[str, object]]:
    payload = state_store.read_workbench()
    if not payload:
        return _bootstrap_workbench()
    if isinstance(payload, list):
        now = datetime.now(timezone.utc).isoformat()
        normalized = []
        for r in payload:
            row = dict(r)
            row["status"] = str(row.get("status") or "DRAFT").upper()
            row.setdefault("notes", "")
            row.setdefault("last_updated_by", "system_normalize")
            row.setdefault("last_updated_at_utc", now)
            normalized.append(row)
        return normalized
    return _bootstrap_workbench()


def _write_workbench(rows: List[Dict[str, object]]) -> None:
    state_store.write_workbench(rows)


def _infer_schema_relationships(domain: str) -> Dict[str, object]:
    if domain not in {"source", "target"}:
        raise ValueError(domain)
    file = SCHEMAS_DIR / ("source_schema_catalog.csv" if domain == "source" else "target_schema_catalog.csv")
    rows = read_csv(file)
    tables = profile_schema(rows)
    table_map = {t["table_name"]: t for t in tables}

    edges = []
    seen = set()

    target_hint_map = {
        "pmi": "LOAD_PMI",
        "ref": "LOAD_REFERRALS",
        "rttpwy": "LOAD_RTT_PATHWAYS",
        "rttprd": "LOAD_RTT_PERIODS",
        "rttevent": "LOAD_RTT_EVENTS",
        "adt_adm": "LOAD_ADT_ADMISSIONS",
        "adt_eps": "LOAD_ADT_EPISODES",
        "owl": "LOAD_OPDWAITLIST",
        "iwl": "LOAD_IWL",
    }

    for t in tables:
        table = t["table_name"]
        cols = [c.lower() for c in t.get("columns", [])]

        if domain == "source" and "internalpatientnumber" in cols and table != "PATDATA":
            key = ("PATDATA", table, "InternalPatientNumber")
            if key not in seen and "PATDATA" in table_map:
                seen.add(key)
                edges.append(
                    {
                        "source": "PATDATA",
                        "target": table,
                        "field": "InternalPatientNumber",
                        "confidence": "inferred",
                        "reason": "shared patient key",
                        "cardinality": "1:N",
                    }
                )

        if domain == "target":
            for c in cols:
                m = re.match(r"^load([a-z0-9_]+)_record_number$", c)
                if m:
                    token = m.group(1)
                    parent = target_hint_map.get(token)
                    if parent and parent in table_map and parent != table:
                        key = (parent, table, c)
                        if key not in seen:
                            seen.add(key)
                            edges.append(
                                {
                                    "source": parent,
                                    "target": table,
                                    "field": c,
                                    "confidence": "inferred",
                                    "reason": "record-number reference naming",
                                    "cardinality": "1:N",
                                }
                            )

            if "record_number" in cols and table.startswith("LOAD_") and table != "LOAD_PMI":
                if "LOAD_PMI" in table_map:
                    key = ("LOAD_PMI", table, "record_number")
                    if key not in seen:
                        seen.add(key)
                        edges.append(
                            {
                                "source": "LOAD_PMI",
                                "target": table,
                                "field": "record_number",
                                "confidence": "inferred",
                                "reason": "shared record_number",
                                "cardinality": "1:N",
                            }
                        )

    return {"domain": domain, "nodes": [{"id": t["table_name"], "label": t["table_name"], "column_count": t["column_count"]} for t in tables], "edges": edges}


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/meta/version")
def api_meta_version(request: Request):
    _require_permission(request, "project.design")
    return _read_version_manifest()


@app.post("/api/auth/login")
def auth_login(payload: AuthLoginRequest, request: Request):
    user = saas_store.authenticate(payload.username_or_email, payload.password)
    if not user:
        _audit_event(
            request,
            event_type="AUTH_LOGIN",
            outcome="DENIED",
            target_type="user",
            target_id=payload.username_or_email,
            details={"reason": "invalid_credentials"},
        )
        raise HTTPException(status_code=401, detail="invalid credentials")
    memberships = saas_store.list_user_memberships(str(user.get("id")))
    role = "super_admin" if user.get("is_super_admin") else (memberships[0]["role"] if memberships else "org_dm_engineer")
    permissions = sorted(_permissions_for_actor({"role": role}))
    org_id = payload.org_id or (memberships[0]["org_id"] if memberships else "")
    workspace_id = payload.workspace_id
    project_id = payload.project_id
    if not workspace_id and org_id:
        workspaces = saas_store.list_workspaces_for_org(org_id)
        workspace_id = workspaces[0]["id"] if workspaces else ""
    if not project_id and workspace_id:
        projects = saas_store.list_projects_for_workspace(workspace_id)
        project_id = projects[0]["id"] if projects else ""
    token = create_token(
        {
            "sub": user["id"],
            "username": user.get("username"),
            "email": user.get("email"),
            "display_name": user.get("display_name", ""),
            "role": role,
            "org_id": org_id,
            "workspace_id": workspace_id or "",
            "project_id": project_id or "",
            "permissions": permissions,
        }
    )
    _audit_event(
        request,
        event_type="AUTH_LOGIN",
        outcome="SUCCESS",
        target_type="user",
        target_id=str(user.get("id", "")),
        details={"username": str(user.get("username", "")), "role": role},
        actor_override={
            "sub": user.get("id", ""),
            "role": role,
            "org_id": org_id,
            "workspace_id": workspace_id or "",
            "project_id": project_id or "",
        },
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user.get("username"),
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "role": role,
            "org_id": org_id,
            "workspace_id": workspace_id or "",
            "project_id": project_id or "",
            "permissions": permissions,
        },
        "memberships": memberships,
    }


@app.post("/api/auth/register")
def auth_register(payload: AuthRegisterRequest, request: Request):
    try:
        req = saas_store.create_registration_request(
            username=payload.username,
            email=payload.email,
            display_name=payload.display_name,
            password=payload.password,
            requested_org_id=payload.requested_org_id,
        )
    except ValueError as ex:
        _audit_event(
            request,
            event_type="AUTH_REGISTER",
            outcome="DENIED",
            target_type="registration_request",
            target_id=payload.username,
            details={"reason": str(ex), "requested_org_id": payload.requested_org_id},
        )
        raise HTTPException(status_code=400, detail=str(ex))
    _audit_event(
        request,
        event_type="AUTH_REGISTER",
        outcome="SUCCESS",
        target_type="registration_request",
        target_id=str(req.get("id", "")),
        details={"username": payload.username, "requested_org_id": payload.requested_org_id},
    )
    return {"status": "PENDING_APPROVAL", "request": req}


@app.get("/api/auth/orgs")
def auth_orgs():
    return {"rows": saas_store.list_orgs_for_user({"id": "", "is_super_admin": True})}


@app.get("/api/auth/me")
def auth_me(request: Request):
    actor = getattr(request.state, "actor", None)
    if not actor:
        raise HTTPException(status_code=401, detail="authentication required")
    return {"user": actor}


@app.post("/api/auth/switch-context")
def auth_switch_context(payload: ContextSwitchRequest, request: Request):
    actor = getattr(request.state, "actor", None)
    if not actor:
        raise HTTPException(status_code=401, detail="authentication required")
    user_id = str(actor.get("sub", ""))
    if not saas_store.user_has_org(user_id, payload.org_id):
        _audit_event(
            request,
            event_type="AUTH_SWITCH_CONTEXT",
            outcome="DENIED",
            target_type="org",
            target_id=payload.org_id,
            details={"reason": "org_access_denied"},
        )
        raise HTTPException(status_code=403, detail="org access denied")
    if not saas_store.workspace_belongs_to_org(payload.workspace_id, payload.org_id):
        _audit_event(
            request,
            event_type="AUTH_SWITCH_CONTEXT",
            outcome="DENIED",
            target_type="workspace",
            target_id=payload.workspace_id,
            details={"reason": "workspace_not_in_org", "org_id": payload.org_id},
        )
        raise HTTPException(status_code=400, detail="workspace does not belong to org")
    if not saas_store.project_belongs_to_workspace(payload.project_id, payload.workspace_id):
        _audit_event(
            request,
            event_type="AUTH_SWITCH_CONTEXT",
            outcome="DENIED",
            target_type="project",
            target_id=payload.project_id,
            details={"reason": "project_not_in_workspace", "workspace_id": payload.workspace_id},
        )
        raise HTTPException(status_code=400, detail="project does not belong to workspace")
    next_payload = dict(actor)
    next_payload["org_id"] = payload.org_id
    next_payload["workspace_id"] = payload.workspace_id
    next_payload["project_id"] = payload.project_id
    next_payload["permissions"] = sorted(_permissions_for_actor(next_payload))
    token = create_token(next_payload)
    _audit_event(
        request,
        event_type="AUTH_SWITCH_CONTEXT",
        outcome="SUCCESS",
        target_type="project",
        target_id=payload.project_id,
        details={"org_id": payload.org_id, "workspace_id": payload.workspace_id},
        actor_override=next_payload,
    )
    return {"access_token": token, "token_type": "bearer", "user": next_payload}


@app.get("/api/registration-requests")
def registration_requests(request: Request, status: Optional[str] = Query(default=None)):
    _require_permission(request, "registration.review")
    return {"rows": saas_store.list_registration_requests(status=status)}


@app.post("/api/registration-requests/{request_id}/approve")
def registration_approve(request_id: str, payload: RegistrationReviewRequest, request: Request):
    actor = _require_permission(request, "registration.review")
    try:
        result = saas_store.approve_registration(request_id=request_id, reviewer_user_id=str(actor.get("sub", "")), role=payload.role)
    except ValueError as ex:
        _audit_event(
            request,
            event_type="REGISTRATION_APPROVE",
            outcome="DENIED",
            target_type="registration_request",
            target_id=request_id,
            details={"reason": str(ex), "requested_role": payload.role},
        )
        raise HTTPException(status_code=400, detail=str(ex))
    _audit_event(
        request,
        event_type="REGISTRATION_APPROVE",
        outcome="SUCCESS",
        target_type="registration_request",
        target_id=request_id,
        details={"approved_user_id": str(result.get("user", {}).get("id", "")), "assigned_role": payload.role},
    )
    return {"status": "APPROVED", "result": result}


@app.post("/api/registration-requests/{request_id}/reject")
def registration_reject(request_id: str, payload: RegistrationReviewRequest, request: Request):
    actor = _require_permission(request, "registration.review")
    try:
        result = saas_store.reject_registration(request_id=request_id, reviewer_user_id=str(actor.get("sub", "")), reason=payload.reason or "")
    except ValueError as ex:
        _audit_event(
            request,
            event_type="REGISTRATION_REJECT",
            outcome="DENIED",
            target_type="registration_request",
            target_id=request_id,
            details={"reason": str(ex)},
        )
        raise HTTPException(status_code=400, detail=str(ex))
    _audit_event(
        request,
        event_type="REGISTRATION_REJECT",
        outcome="SUCCESS",
        target_type="registration_request",
        target_id=request_id,
        details={"review_reason": payload.reason or ""},
    )
    return {"status": "REJECTED", "result": result}


@app.get("/api/orgs")
def list_orgs(request: Request):
    actor = _require_permission(request, "project.design")
    user = {"id": actor.get("sub"), "is_super_admin": actor.get("role") == "super_admin"}
    return {"rows": saas_store.list_orgs_for_user(user)}


@app.post("/api/orgs")
def create_org(payload: CreateNameRequest, request: Request):
    _require_permission(request, "org.manage")
    try:
        row = saas_store.create_org(payload.name)
    except ValueError as ex:
        _audit_event(
            request,
            event_type="ORG_CREATE",
            outcome="DENIED",
            target_type="organization",
            target_id=payload.name,
            details={"reason": str(ex)},
        )
        raise HTTPException(status_code=400, detail=str(ex))
    _audit_event(
        request,
        event_type="ORG_CREATE",
        outcome="SUCCESS",
        target_type="organization",
        target_id=str(row.get("id", "")),
        details={"name": payload.name},
    )
    return {"row": row}


@app.get("/api/orgs/{org_id}/workspaces")
def list_workspaces(org_id: str, request: Request):
    _require_permission(request, "project.design")
    return {"rows": saas_store.list_workspaces_for_org(org_id)}


@app.post("/api/orgs/{org_id}/workspaces")
def create_workspace(org_id: str, payload: CreateNameRequest, request: Request):
    _require_permission(request, "workspace.manage")
    try:
        row = saas_store.create_workspace(org_id=org_id, name=payload.name)
    except ValueError as ex:
        _audit_event(
            request,
            event_type="WORKSPACE_CREATE",
            outcome="DENIED",
            target_type="workspace",
            target_id=payload.name,
            details={"reason": str(ex), "org_id": org_id},
        )
        raise HTTPException(status_code=400, detail=str(ex))
    _audit_event(
        request,
        event_type="WORKSPACE_CREATE",
        outcome="SUCCESS",
        target_type="workspace",
        target_id=str(row.get("id", "")),
        details={"name": payload.name, "org_id": org_id},
    )
    return {"row": row}


@app.get("/api/workspaces/{workspace_id}/projects")
def list_projects(workspace_id: str, request: Request):
    _require_permission(request, "project.design")
    return {"rows": saas_store.list_projects_for_workspace(workspace_id)}


@app.post("/api/workspaces/{workspace_id}/projects")
def create_project(workspace_id: str, payload: CreateNameRequest, request: Request):
    _require_permission(request, "project.manage")
    try:
        row = saas_store.create_project(workspace_id=workspace_id, name=payload.name)
    except ValueError as ex:
        _audit_event(
            request,
            event_type="PROJECT_CREATE",
            outcome="DENIED",
            target_type="project",
            target_id=payload.name,
            details={"reason": str(ex), "workspace_id": workspace_id},
        )
        raise HTTPException(status_code=400, detail=str(ex))
    _audit_event(
        request,
        event_type="PROJECT_CREATE",
        outcome="SUCCESS",
        target_type="project",
        target_id=str(row.get("id", "")),
        details={"name": payload.name, "workspace_id": workspace_id},
    )
    return {"row": row}


@app.get("/api/orgs/{org_id}/users")
def list_org_users(org_id: str, request: Request):
    _require_permission(request, "org.manage")
    return {"rows": saas_store.list_org_users(org_id)}


@app.get("/api/audit/events")
def list_audit_events(
    request: Request,
    limit: int = Query(default=200, ge=1, le=2000),
    event_type: Optional[str] = Query(default=None),
    outcome: Optional[str] = Query(default=None),
    org_id: Optional[str] = Query(default=None),
):
    actor = _require_permission(request, "org.manage")
    requested_org = (org_id or "").strip()
    if str(actor.get("role", "")) != "super_admin":
        requested_org = str(actor.get("org_id", "")).strip()

    rows = audit_store.list_events(
        limit=limit,
        event_type=(event_type or "").strip(),
        outcome=(outcome or "").strip(),
        actor_org_id=requested_org,
    )
    return {"row_count": len(rows), "limit": limit, "rows": rows}


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


@app.get("/api/mappings/workbench")
def mapping_workbench(
    target_table: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    mapping_class: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0, le=1000000),
    limit: int = Query(default=500, ge=1, le=5000),
):
    rows = _read_workbench()
    if target_table:
        rows = [r for r in rows if r.get("target_table") == target_table]
    if status:
        rows = [r for r in rows if str(r.get("status", "")).upper() == status.upper()]
    if mapping_class:
        rows = [r for r in rows if str(r.get("mapping_class", "")).upper() == mapping_class.upper()]
    status_counts: Dict[str, int] = {}
    for r in rows:
        s = str(r.get("status", "DRAFT")).upper()
        status_counts[s] = status_counts.get(s, 0) + 1
    total = len(rows)
    page_rows = rows[offset : offset + limit]
    return {"row_count": total, "offset": offset, "limit": limit, "rows": page_rows, "status_counts": status_counts}


@app.post("/api/mappings/workbench/upsert")
def mapping_workbench_upsert(payload: MappingWorkbenchUpdate, request: Request):
    _require_permission(request, "project.design")
    rows = _read_workbench()
    found = False
    now = datetime.now(timezone.utc).isoformat()
    for r in rows:
        if r.get("workbench_id") == payload.workbench_id:
            found = True
            if payload.mapping_class is not None:
                r["mapping_class"] = payload.mapping_class
            if payload.primary_source_table is not None:
                r["primary_source_table"] = payload.primary_source_table
            if payload.primary_source_field is not None:
                r["primary_source_field"] = payload.primary_source_field
            if payload.transformation_rule is not None:
                r["transformation_rule"] = payload.transformation_rule
            if payload.notes is not None:
                r["notes"] = payload.notes
            r["last_updated_by"] = payload.updated_by
            r["last_updated_at_utc"] = now
            break
    if not found:
        raise HTTPException(status_code=404, detail=f"workbench_id not found: {payload.workbench_id}")
    _write_workbench(rows)
    return {"status": "ok", "workbench_id": payload.workbench_id}


@app.post("/api/mappings/workbench/transition")
def mapping_workbench_transition(payload: MappingWorkbenchTransition, request: Request):
    _require_permission(request, "project.design")
    allowed = {"DRAFT", "IN_REVIEW", "APPROVED", "REJECTED"}
    next_status = payload.status.upper()
    if next_status not in allowed:
        raise HTTPException(status_code=400, detail=f"status must be one of {sorted(allowed)}")
    rows = _read_workbench()
    now = datetime.now(timezone.utc).isoformat()
    for r in rows:
        if r.get("workbench_id") == payload.workbench_id:
            r["status"] = next_status
            r["last_updated_by"] = payload.updated_by
            r["last_updated_at_utc"] = now
            if payload.notes is not None:
                r["notes"] = payload.notes
            _write_workbench(rows)
            return {"status": "ok", "workbench_id": payload.workbench_id, "new_status": next_status}
    raise HTTPException(status_code=404, detail=f"workbench_id not found: {payload.workbench_id}")


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


@app.get("/api/quality/trends")
def quality_trends(limit: int = Query(default=60, ge=1, le=300)):
    history = _read_quality_history()
    return {"points": history[-limit:]}


@app.post("/api/quality/trends/seed")
def quality_trends_seed(request: Request, weeks: int = Query(default=12, ge=4, le=104), replace: bool = Query(default=True)):
    _require_permission(request, "project.quality")
    now = datetime.now(timezone.utc)
    base = _snapshot_payload()
    rng = random.Random(f"quality_seed:{weeks}:{base.get('error_count', 0)}:{base.get('warning_count', 0)}")
    generated = []
    for i in range(weeks):
        dt = now.replace(microsecond=0) - timedelta(days=7 * (weeks - i - 1))
        err = max(0, int(float(base.get("error_count", 0)) + rng.randint(-3, 5) + (weeks - i) * 0.2))
        warn = max(0, int(float(base.get("warning_count", 0)) + rng.randint(-5, 8) + (weeks - i) * 0.35))
        rej = max(0, int(float(base.get("crosswalk_rejects", 0)) + rng.randint(-2, 4)))
        pop = max(0.0, min(1.0, float(base.get("population_ratio", 0)) + rng.uniform(-0.06, 0.04)))
        row = {
            "ts_utc": dt.isoformat(),
            "error_count": err,
            "warning_count": warn,
            "crosswalk_rejects": rej,
            "population_ratio": round(pop, 4),
            "tables_written": int(base.get("tables_written", 0) or 0),
            "unresolved_mapping": max(0, int(float(base.get("unresolved_mapping", 0)) + rng.randint(-2, 3))),
            "release_status": base.get("release_status", "UNKNOWN"),
            "event": "seed_quality_trend",
        }
        generated.append(row)
    history = generated if replace else (_read_quality_history() + generated)
    _write_quality_history(history)
    return {"status": "ok", "weeks": weeks, "points_written": len(generated), "replace": replace}


@app.get("/api/quality/kpis")
def quality_kpis():
    return {"rows": _read_quality_kpis()}


@app.post("/api/quality/kpis")
def quality_kpis_upsert(payload: Dict[str, object], request: Request):
    _require_permission(request, "project.quality")
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise HTTPException(status_code=400, detail="rows must be a list")
    cleaned = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id", "")).strip()
        label = str(row.get("label", "")).strip()
        if not rid or not label:
            continue
        direction = str(row.get("direction", "max")).lower()
        if direction not in {"max", "min"}:
            direction = "max"
        fmt = str(row.get("format", "int")).lower()
        if fmt not in {"int", "pct"}:
            fmt = "int"
        cleaned.append(
            {
                "id": rid,
                "label": label,
                "threshold": float(row.get("threshold", 0) or 0),
                "direction": direction,
                "enabled": bool(row.get("enabled", True)),
                "format": fmt,
            }
        )
    if not cleaned:
        raise HTTPException(status_code=400, detail="no valid KPI rows supplied")
    _write_quality_kpis(cleaned)
    return {"status": "ok", "row_count": len(cleaned)}


@app.get("/api/quality/kpi-widgets")
def quality_kpi_widgets(weeks: int = Query(default=12, ge=4, le=104)):
    latest = _snapshot_payload()
    history = _read_quality_history()
    config_rows = _read_quality_kpis()
    mapped = []
    for cfg in config_rows:
        kid = str(cfg.get("id", ""))
        current = float(_metric_from_point(latest, kid))
        hist_vals = [float(_metric_from_point(p, kid)) for p in history[-weeks:] if isinstance(p, dict)]
        if len(hist_vals) < weeks:
            hist_vals = _synthetic_trend(kid, current, weeks)
        pct = 0.0
        threshold = float(cfg.get("threshold", 0) or 0)
        direction = str(cfg.get("direction", "max"))
        if direction == "max":
            pct = 1.0 if threshold <= 0 and current <= 0 else (threshold / max(current, 0.0001) if threshold > 0 else 0.0)
        else:
            pct = current / max(threshold, 0.0001)
        mapped.append(
            {
                "id": kid,
                "label": cfg.get("label", kid),
                "value": current,
                "threshold": threshold,
                "direction": direction,
                "format": cfg.get("format", "int"),
                "enabled": bool(cfg.get("enabled", True)),
                "trend": hist_vals[-weeks:],
                "percentage_of_threshold": round(max(0.0, min(1.5, pct)), 4),
                "source": "migration_gate",
            }
        )

    source_rows = []
    for row in _compute_source_kpi_rows():
        current = float(row.get("value", 0) or 0)
        trend = _synthetic_trend(str(row.get("id")), current, weeks)
        threshold = float(row.get("threshold", 0) or 0)
        pct = 1.0 if threshold <= 0 and current <= 0 else (threshold / max(current, 0.0001) if threshold > 0 else 0.0)
        source_rows.append(
            {
                **row,
                "trend": trend,
                "percentage_of_threshold": round(max(0.0, min(1.5, pct)), 4),
                "enabled": True,
                "source": "source_runtime_profile",
            }
        )
    return {"weeks": weeks, "rows": mapped + source_rows}


@app.get("/api/gates/profiles")
def gate_profiles():
    return read_json(DATA_MIGRATION_ROOT / "pipeline" / "release_gate_profiles.json")


@app.get("/api/schema-graph/{domain}/relationships")
def schema_relationships(domain: str):
    try:
        return _infer_schema_relationships(domain.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="domain must be source or target")


@app.get("/api/schema-graph/{domain}/erd")
def schema_erd(domain: str, table_filter: str = Query(default="")):
    try:
        payload = _infer_schema_relationships(domain.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="domain must be source or target")
    if table_filter:
        tf = table_filter.lower()
        nodes = [n for n in payload["nodes"] if tf in n["id"].lower()]
        node_ids = {n["id"] for n in nodes}
        edges = [e for e in payload["edges"] if e["source"] in node_ids and e["target"] in node_ids]
        payload["nodes"] = nodes
        payload["edges"] = edges
    return payload


@app.post("/api/connectors/explore")
def connector_explore(spec: ConnectorSpec, request: Request):
    _require_permission(request, "project.design")
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


@app.post("/api/connectors/preview")
def connector_preview(payload: Dict[str, Any], request: Request):
    _require_permission(request, "project.design")
    connector_type = str(payload.get("connector_type", "")).strip()
    connection_string = str(payload.get("connection_string", "")).strip()
    schema_name = str(payload.get("schema_name", "")).strip()
    direction = str(payload.get("direction", "source")).strip() or "source"
    table_name = str(payload.get("table_name", "")).strip()
    options = payload.get("options") or {}
    limit = int(payload.get("limit", 20) or 20)
    if not connector_type or not connection_string or not table_name:
        raise HTTPException(status_code=400, detail="connector_type, connection_string, and table_name are required")
    limit = max(1, min(limit, 200))
    try:
        connector = build_connector(
            connector_type,
            connection_string,
            schema_name,
            direction=direction,
            options=options,
        )
    except ValueError as ex:
        raise HTTPException(status_code=400, detail=str(ex)) from ex
    except NotImplementedError as ex:
        raise HTTPException(status_code=501, detail=str(ex)) from ex

    tables = connector.list_tables()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"table not found: {table_name}")

    return {
        "table_name": table_name,
        "columns": connector.describe_table(table_name)[:200],
        "sample_rows": connector.sample_rows(table_name, limit=limit),
        "available_tables": len(tables),
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
            {"id": "odbc", "label": "ODBC Connector", "mode": "experimental", "direction": "source_or_target"},
            {"id": "jdbc", "label": "JDBC Connector", "mode": "experimental", "direction": "source_or_target"},
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
    request: Request,
    rows: int = Query(default=20, ge=1, le=100000),
    seed: int = Query(default=42, ge=0, le=999999),
    min_patients: int = Query(default=20, ge=1, le=100000),
    release_profile: str = Query(default="pre_production"),
):
    _require_permission(request, "project.execute")
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
    pre_snapshot = _create_snapshot("pre_run")
    proc = subprocess.run(cmd, cwd=str(DATA_MIGRATION_ROOT), capture_output=True, text=True)
    payload = read_json(REPORTS_DIR / "product_lifecycle_run.json")
    post_snapshot = _create_snapshot("post_run")
    quality_point = _record_quality_snapshot("run_execute")
    return {
        "command": " ".join(cmd),
        "return_code": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "report": payload,
        "snapshots": {"pre": pre_snapshot, "post": post_snapshot},
        "quality_point": quality_point,
    }


@app.get("/api/lifecycle/steps")
def lifecycle_steps(
    rows: int = Query(default=20, ge=1, le=100000),
    seed: int = Query(default=42, ge=0, le=999999),
    min_patients: int = Query(default=20, ge=1, le=100000),
    release_profile: str = Query(default="pre_production"),
):
    return {
        "rows": rows,
        "seed": seed,
        "min_patients": min_patients,
        "release_profile": release_profile,
        "steps": _lifecycle_steps(rows, seed, min_patients, release_profile),
    }


@app.post("/api/lifecycle/steps/{step_id}/execute")
def execute_lifecycle_step(
    request: Request,
    step_id: str,
    rows: int = Query(default=20, ge=1, le=100000),
    seed: int = Query(default=42, ge=0, le=999999),
    min_patients: int = Query(default=20, ge=1, le=100000),
    release_profile: str = Query(default="pre_production"),
):
    _require_permission(request, "project.execute")
    steps = {s["id"]: s for s in _lifecycle_steps(rows, seed, min_patients, release_profile)}
    if step_id not in steps:
        raise HTTPException(status_code=404, detail=f"Unknown lifecycle step: {step_id}")
    cmd = steps[step_id]["command"]
    proc = subprocess.run(cmd, cwd=str(DATA_MIGRATION_ROOT), capture_output=True, text=True)
    quality_point = _record_quality_snapshot(f"step_{step_id}")
    latest = {
        "contract_migration": read_json(REPORTS_DIR / "contract_migration_report.json"),
        "enterprise_quality": read_json(REPORTS_DIR / "enterprise_pipeline_report.json"),
        "release_gates": read_json(REPORTS_DIR / "release_gate_report.json"),
        "product_lifecycle": read_json(REPORTS_DIR / "product_lifecycle_run.json"),
    }
    return {
        "step_id": step_id,
        "command": " ".join(cmd),
        "return_code": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
        "latest_reports": latest,
        "quality_point": quality_point,
    }


@app.post("/api/lifecycle/execute-from/{step_id}")
def execute_lifecycle_from(
    request: Request,
    step_id: str,
    rows: int = Query(default=20, ge=1, le=100000),
    seed: int = Query(default=42, ge=0, le=999999),
    min_patients: int = Query(default=20, ge=1, le=100000),
    release_profile: str = Query(default="pre_production"),
):
    _require_permission(request, "project.execute")
    steps = _lifecycle_steps(rows, seed, min_patients, release_profile)
    ids = [s["id"] for s in steps]
    if step_id not in ids:
        raise HTTPException(status_code=404, detail=f"Unknown lifecycle step: {step_id}")
    start_idx = ids.index(step_id)
    selected = steps[start_idx:]

    pre_snapshot = _create_snapshot(f"pre_from_{step_id}")
    results = []
    for s in selected:
        proc = subprocess.run(s["command"], cwd=str(DATA_MIGRATION_ROOT), capture_output=True, text=True)
        results.append(
            {
                "step_id": s["id"],
                "command": " ".join(s["command"]),
                "return_code": proc.returncode,
                "stdout_tail": proc.stdout[-1200:],
                "stderr_tail": proc.stderr[-1200:],
            }
        )
        if proc.returncode != 0:
            break
    post_snapshot = _create_snapshot(f"post_from_{step_id}")
    quality_point = _record_quality_snapshot(f"run_from_{step_id}")
    return {
        "start_step": step_id,
        "steps_executed": results,
        "overall_status": "PASS" if all(r["return_code"] == 0 for r in results) else "FAIL",
        "snapshots": {"pre": pre_snapshot, "post": post_snapshot},
        "quality_point": quality_point,
    }


@app.get("/api/lifecycle/snapshots")
def lifecycle_snapshots(limit: int = Query(default=50, ge=1, le=200)):
    snaps = _list_snapshots()
    return {"count": len(snaps), "snapshots": snaps[:limit]}


@app.post("/api/lifecycle/snapshots/{snapshot_id}/restore")
def lifecycle_restore(snapshot_id: str, request: Request):
    _require_permission(request, "project.execute")
    try:
        _restore_snapshot(snapshot_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Snapshot not found: {snapshot_id}")
    quality_point = _record_quality_snapshot(f"restore_{snapshot_id}")
    return {"status": "ok", "snapshot_id": snapshot_id, "quality_point": quality_point}
