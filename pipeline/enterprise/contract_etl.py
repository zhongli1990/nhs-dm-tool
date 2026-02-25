import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from .crosswalks import apply_crosswalk, infer_crosswalk_name, load_crosswalks
from .io import read_csv
from .transform_plugins import apply_domain_plugins


FK_FIELDS = {
    "loadpmi_record_number",
    "loadrttpwy_record_number",
    "loadref_record_number",
    "loadrttprd_record_number",
    "loadowl_record_number",
    "loadiwl_record_number",
    "adt_adm_record_number",
    "adt_eps_record_number",
    "mh_dm_record_number",
    "mh_cm_record_number",
}

SOURCE_ID_CANDIDATES = [
    "InternalPatientNumber",
    "Intpatno",
    "main_crn",
    "DistrictNumber",
    "NhsNumber",
]


@dataclass
class TableRunStats:
    target_table: str
    source_table: str
    rows_written: int
    columns_total: int
    columns_populated: int
    mapped_fields: int


def _normalize_date(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return ""
    if len(v) == 12 and v.isdigit():
        # CCYYMMDDHHMM -> DD/MM/YYYY
        return f"{v[6:8]}/{v[4:6]}/{v[0:4]}"
    if len(v) == 8 and v.isdigit():
        # CCYYMMDD -> DD/MM/YYYY
        return f"{v[6:8]}/{v[4:6]}/{v[0:4]}"
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(v, fmt)
            return d.strftime("%d/%m/%Y")
        except ValueError:
            continue
    return v


def _target_headers(target_catalog_path: Path) -> Dict[str, List[str]]:
    headers: Dict[str, List[str]] = {}
    for r in read_csv(target_catalog_path):
        t = r["table_name"]
        f = r["field_name"]
        if not t or not f:
            continue
        headers.setdefault(t, [])
        if f not in headers[t]:
            headers[t].append(f)
    return headers


def _group_contract_rows(contract_rows: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for r in contract_rows:
        grouped.setdefault(r["target_table"], []).append(r)
    return grouped


def _choose_base_source(rows: List[Dict[str, str]], source_dir: Path) -> str:
    ranked: Dict[str, int] = {}
    for r in rows:
        src = (r.get("primary_source_table") or "").strip()
        cls = (r.get("mapping_class") or "").strip()
        if not src or cls in {"SURROGATE_ETL", "OUT_OF_SCOPE", "REFERENCE_MASTER_FEED"}:
            continue
        ranked[src] = ranked.get(src, 0) + 1
    choices = sorted(ranked.items(), key=lambda x: (-x[1], x[0]))
    for src, _ in choices:
        if (source_dir / f"{src}.csv").exists():
            return src
    return ""


def _find_source_id(source_row: Dict[str, str]) -> str:
    for key in SOURCE_ID_CANDIDATES:
        if key in source_row and str(source_row.get(key, "")).strip():
            return str(source_row[key]).strip()
    return ""


def _get_case_insensitive(source_row: Dict[str, str], field: str) -> str:
    if field in source_row:
        return source_row.get(field, "")
    lower_map = {k.lower(): k for k in source_row.keys()}
    actual = lower_map.get(field.lower())
    if actual:
        return source_row.get(actual, "")
    return ""


def _field_value(
    target_field: str,
    mapping_class: str,
    source_field: str,
    source_row: Dict[str, str],
    row_num: int,
) -> str:
    tf = target_field.lower()
    sc = mapping_class.strip()
    sf = (source_field or "").strip()

    if sc in {"DIRECT_SOURCE", "LOOKUP_TRANSLATION", "DERIVED"} and sf:
        return _normalize_date(_get_case_insensitive(source_row, sf))

    if sc == "SURROGATE_ETL":
        if tf == "record_number":
            return str(row_num)
        if tf == "system_code":
            return "SRC_PAS_V83"
        if tf == "external_system_id":
            return _find_source_id(source_row)
        if tf in FK_FIELDS:
            return str(row_num)
        return str(row_num)

    if sc == "REFERENCE_MASTER_FEED":
        if "code" in tf:
            return f"REF{row_num:04d}"
        if "name" in tf or "description" in tf:
            return f"Reference Value {row_num}"
        return ""

    if sc == "OUT_OF_SCOPE":
        return ""

    return ""


def _fallback_value(target_table: str, target_field: str, source_row: Dict[str, str], row_num: int) -> str:
    tf = target_field.lower()
    if "date" in tf:
        return "01/01/2024"
    if "time" in tf:
        return "09:00"
    if tf.endswith("_flag") or tf.startswith("is_") or tf.startswith("allow_") or "permission" in tf:
        return "N"
    if "status" in tf:
        return "ACTIVE"
    if "code" in tf or tf.endswith("_id") or "number" in tf or tf.endswith("_no"):
        return f"AUTO{row_num:04d}"
    if "name" in tf:
        for k in ("Forenames", "Surname", "name_1", "pat_name_1"):
            if k in source_row and str(source_row.get(k, "")).strip():
                return str(source_row[k]).strip().upper()
        return f"AUTO_NAME_{row_num:03d}"
    if "comment" in tf or "note" in tf or "text" in tf or "description" in tf:
        return "Auto-derived value"
    if "type" in tf:
        return "GEN"
    if "post_code" in tf or "postcode" in tf:
        return "ZZ1 1ZZ"
    if "email" in tf:
        return f"user{row_num:03d}@example.nhs.uk"
    if "phone" in tf or "telephone" in tf:
        return "00000000000"
    if "gender" in tf or tf == "sex":
        return "U"
    return ""


def _write_csv(path: Path, headers: List[str], rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in rows:
            w.writerow({h: row.get(h, "") for h in headers})


def build_contract_targets(
    root: Path,
    source_dir: Path,
    output_dir: Path,
    contract_csv: Path,
    target_catalog_csv: Path,
    crosswalk_dir: Path,
    impute_mode: str = "strict",
) -> Tuple[List[TableRunStats], List[Dict[str, str]], List[Dict[str, str]]]:
    contract_rows = read_csv(contract_csv)
    grouped = _group_contract_rows(contract_rows)
    target_headers = _target_headers(target_catalog_csv)
    crosswalks = load_crosswalks(crosswalk_dir)
    stats: List[TableRunStats] = []
    run_issues: List[Dict[str, str]] = []
    rejects: List[Dict[str, str]] = []

    for target_table, rows in sorted(grouped.items()):
        headers = target_headers.get(target_table, [])
        if not headers:
            run_issues.append(
                {
                    "severity": "WARN",
                    "category": "TARGET_HEADER_MISSING",
                    "table_name": target_table,
                    "field_name": "",
                    "record_id": "",
                    "message": "Target table headers not found in target schema catalog.",
                }
            )
            continue

        base_source = _choose_base_source(rows, source_dir)
        source_rows = read_csv(source_dir / f"{base_source}.csv") if base_source else []
        if not source_rows:
            # Keep deterministic output even for reference-only/no-source tables.
            source_rows = [{} for _ in range(20)]
            run_issues.append(
                {
                    "severity": "WARN",
                    "category": "SOURCE_BASE_UNRESOLVED",
                    "table_name": target_table,
                    "field_name": "",
                    "record_id": "",
                    "message": f"No available base source table found. Using synthetic rows for {target_table}.",
                }
            )

        field_rules: Dict[str, Dict[str, str]] = {}
        for r in rows:
            f = r["target_field"]
            # Prefer higher-confidence rows if duplicate target fields exist in contract.
            if f not in field_rules:
                field_rules[f] = r
            elif (r.get("confidence") or "").upper() == "HIGH":
                field_rules[f] = r

        out_rows: List[Dict[str, str]] = []
        for i, src in enumerate(source_rows, start=1):
            row = {h: "" for h in headers}
            for h in headers:
                rule = field_rules.get(h)
                if not rule:
                    continue
                row[h] = _field_value(
                    target_field=h,
                    mapping_class=rule.get("mapping_class", ""),
                    source_field=rule.get("primary_source_field", ""),
                    source_row=src,
                    row_num=i,
                )
                mapping_class = (rule.get("mapping_class") or "").strip()
                if mapping_class == "LOOKUP_TRANSLATION":
                    cw_name = infer_crosswalk_name(target_table, h)
                    if cw_name:
                        translated = apply_crosswalk(row[h], cw_name, crosswalks)
                        if translated is None:
                            # no crosswalk loaded for inferred type; keep value as-is
                            pass
                        elif translated == "__REJECT__" and row[h].strip():
                            rejects.append(
                                {
                                    "severity": "WARN",
                                    "category": "CROSSWALK_REJECT",
                                    "table_name": target_table,
                                    "field_name": h,
                                    "record_id": str(i),
                                    "source_value": row[h],
                                    "crosswalk_name": cw_name,
                                    "message": f"Value '{row[h]}' not found in crosswalk '{cw_name}'.",
                                }
                            )
                            row[h] = ""
                        else:
                            row[h] = translated
                if impute_mode.lower() != "strict" and not str(row[h]).strip():
                    row[h] = _fallback_value(target_table, h, src, i)
            apply_domain_plugins(target_table, row, src, i)
            out_rows.append(row)

        _write_csv(output_dir / f"{target_table}.csv", headers, out_rows)
        populated = sum(1 for h in headers if any(str(r.get(h, "")).strip() for r in out_rows))
        mapped = sum(1 for h in headers if h in field_rules)
        stats.append(
            TableRunStats(
                target_table=target_table,
                source_table=base_source or "SYNTHETIC",
                rows_written=len(out_rows),
                columns_total=len(headers),
                columns_populated=populated,
                mapped_fields=mapped,
            )
        )

    return stats, run_issues, rejects
