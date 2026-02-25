import csv
from pathlib import Path
from typing import Dict, Optional


def load_crosswalks(crosswalk_dir: Path) -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    if not crosswalk_dir.exists():
        return out
    for p in sorted(crosswalk_dir.glob("*.csv")):
        table = p.stem.lower()
        mapping: Dict[str, str] = {}
        with p.open("r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                src = (row.get("source_value") or "").strip()
                tgt = (row.get("target_value") or "").strip()
                if src:
                    mapping[src] = tgt
        out[table] = mapping
    return out


def infer_crosswalk_name(target_table: str, target_field: str) -> Optional[str]:
    tt = target_table.lower()
    tf = target_field.lower()

    if "sex" in tf:
        return "sex"
    if "ethnic" in tf:
        return "ethnicity"
    if "rtt" in tt and ("status" in tf or "pathway_status" in tf):
        return "rtt_status"
    if "method_of_admission" in tf:
        return "admission_method"
    if "method_of_discharge" in tf:
        return "discharge_method"
    if tf in {"source_of_admission", "destination_on_discharge", "admit_from"}:
        return "source_destination"
    return None


def apply_crosswalk(
    value: str,
    crosswalk_name: str,
    crosswalks: Dict[str, Dict[str, str]],
) -> Optional[str]:
    v = (value or "").strip()
    if not v:
        return ""
    table = crosswalks.get(crosswalk_name.lower())
    if not table:
        return None
    if v in table:
        return table[v]
    return "__REJECT__"
