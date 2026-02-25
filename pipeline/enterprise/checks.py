from collections import Counter
from pathlib import Path
from typing import Dict, List, Set

from .io import read_csv
from .models import DataIssue
from .validators import is_valid_date_ddmmyyyy, is_valid_nhs_number


PHANTOM_FIELDS = {
    "must",
    "indicates",
    "ged",
    "ge_date",
    "ge_toe",
    "ge_typee",
    "appointments",
    "acters",
    "before",
    "ranges",
    "table",
    "ge_status",
    "ge_methode",
    "ge_specialty",
    "ge_consultant",
}


def _issue(sev: str, cat: str, table: str, field: str, rec: str, msg: str) -> DataIssue:
    return DataIssue(severity=sev, category=cat, table_name=table, field_name=field, record_id=rec, message=msg)


def check_source_quality(source_dir: Path, min_rows: int) -> List[DataIssue]:
    issues: List[DataIssue] = []

    patdata_path = source_dir / "PATDATA.csv"
    admit_path = source_dir / "ADMITDISCH.csv"
    required = ["PATDATA.csv", "ADMITDISCH.csv", "HWSAPP.csv", "AEA.csv"]
    for name in required:
        p = source_dir / name
        if not p.exists():
            issues.append(_issue("ERROR", "SOURCE_MISSING_TABLE", name.replace(".csv", ""), "", "", "Required source table is missing."))

    for p in sorted(source_dir.glob("*.csv")):
        rows = read_csv(p)
        if len(rows) < min_rows:
            issues.append(
                _issue(
                    "ERROR",
                    "SOURCE_ROW_COUNT",
                    p.stem,
                    "",
                    "",
                    f"Row count {len(rows)} is below required minimum {min_rows}.",
                )
            )

    if patdata_path.exists():
        rows = read_csv(patdata_path)
        mrn_counts = Counter((r.get("InternalPatientNumber") or "").strip() for r in rows)
        for mrn, cnt in mrn_counts.items():
            if mrn and cnt > 1:
                issues.append(_issue("WARN", "SOURCE_DUPLICATE_MRN", "PATDATA", "InternalPatientNumber", mrn, f"Duplicate MRN appears {cnt} times."))

        for idx, r in enumerate(rows, start=1):
            nhs = (r.get("NhsNumber") or "").strip()
            if nhs and not is_valid_nhs_number(nhs):
                issues.append(_issue("ERROR", "SOURCE_INVALID_NHS", "PATDATA", "NhsNumber", str(idx), f"Invalid NHS number '{nhs}'"))
            dob = (r.get("PtDoB") or "").strip()
            if dob and not is_valid_date_ddmmyyyy(dob):
                issues.append(_issue("ERROR", "SOURCE_INVALID_DATE", "PATDATA", "PtDoB", str(idx), f"Invalid DOB '{dob}'"))

    if patdata_path.exists() and admit_path.exists():
        p_rows = read_csv(patdata_path)
        a_rows = read_csv(admit_path)
        p_mrn = {(r.get("InternalPatientNumber") or "").strip() for r in p_rows}
        for idx, r in enumerate(a_rows, start=1):
            mrn = (r.get("InternalPatientNumber") or "").strip()
            if mrn and mrn not in p_mrn:
                issues.append(
                    _issue(
                        "ERROR",
                        "SOURCE_REF_INTEGRITY",
                        "ADMITDISCH",
                        "InternalPatientNumber",
                        str(idx),
                        f"MRN '{mrn}' not found in PATDATA.",
                    )
                )
    return issues


def check_mapping_contract(contract_csv: Path) -> List[DataIssue]:
    issues: List[DataIssue] = []
    rows = read_csv(contract_csv)
    for r in rows:
        t = r["target_table"]
        f = r["target_field"]
        cls = r["mapping_class"]
        if cls == "OUT_OF_SCOPE" and f.lower() not in PHANTOM_FIELDS:
            issues.append(
                _issue(
                    "WARN",
                    "MAPPING_UNRESOLVED",
                    t,
                    f,
                    "",
                    "Business field remains OUT_OF_SCOPE and needs explicit SME/default decision.",
                )
            )
    return issues


def check_target_referential_integrity(target_dir: Path) -> List[DataIssue]:
    issues: List[DataIssue] = []

    def load(name: str) -> List[Dict[str, str]]:
        p = target_dir / f"{name}.csv"
        return read_csv(p) if p.exists() else []

    def colset(rows: List[Dict[str, str]], col: str) -> Set[str]:
        return {(r.get(col) or "").strip() for r in rows if (r.get(col) or "").strip()}

    pmi = load("LOAD_PMI")
    pmi_ids = load("LOAD_PMIIDS")
    rtt_pathways = load("LOAD_RTT_PATHWAYS")
    rtt_periods = load("LOAD_RTT_PERIODS")
    rtt_events = load("LOAD_RTT_EVENTS")
    opd_wl = load("LOAD_OPDWAITLIST")
    opd_appt = load("LOAD_OPD_APPOINTMENTS")
    iwl = load("LOAD_IWL")
    adt_adm = load("LOAD_ADT_ADMISSIONS")
    adt_eps = load("LOAD_ADT_EPISODES")
    adt_ward = load("LOAD_ADT_WARDSTAYS")

    checks = [
        ("LOAD_PMIIDS", "loadpmi_record_number", "LOAD_PMI", "record_number", colset(pmi_ids, "loadpmi_record_number"), colset(pmi, "record_number")),
        ("LOAD_RTT_PERIODS", "loadrttpwy_record_number", "LOAD_RTT_PATHWAYS", "record_number", colset(rtt_periods, "loadrttpwy_record_number"), colset(rtt_pathways, "record_number")),
        ("LOAD_RTT_EVENTS", "loadrttprd_record_number", "LOAD_RTT_PERIODS", "record_number", colset(rtt_events, "loadrttprd_record_number"), colset(rtt_periods, "record_number")),
        ("LOAD_OPDWAITLIST", "loadrttprd_record_number", "LOAD_RTT_PERIODS", "record_number", colset(opd_wl, "loadrttprd_record_number"), colset(rtt_periods, "record_number")),
        ("LOAD_OPD_APPOINTMENTS", "loadowl_record_number", "LOAD_OPDWAITLIST", "record_number", colset(opd_appt, "loadowl_record_number"), colset(opd_wl, "record_number")),
        ("LOAD_ADT_ADMISSIONS", "loadiwl_record_number", "LOAD_IWL", "record_number", colset(adt_adm, "loadiwl_record_number"), colset(iwl, "record_number")),
        ("LOAD_ADT_EPISODES", "adt_adm_record_number", "LOAD_ADT_ADMISSIONS", "record_number", colset(adt_eps, "adt_adm_record_number"), colset(adt_adm, "record_number")),
        ("LOAD_ADT_WARDSTAYS", "adt_eps_record_number", "LOAD_ADT_EPISODES", "record_number", colset(adt_ward, "adt_eps_record_number"), colset(adt_eps, "record_number")),
    ]

    for c_table, c_field, p_table, p_field, c_set, p_set in checks:
        missing = sorted(c_set - p_set)
        for m in missing[:200]:
            issues.append(
                _issue(
                    "ERROR",
                    "TARGET_REF_INTEGRITY",
                    c_table,
                    c_field,
                    m,
                    f"Key '{m}' not found in parent {p_table}.{p_field}.",
                )
            )
    return issues

