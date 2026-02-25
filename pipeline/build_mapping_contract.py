import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CATALOG = ROOT / "schemas" / "source_schema_catalog.csv"
TARGET_DIR = ROOT / "mock_data" / "target"
OUT_CSV = ROOT / "reports" / "mapping_contract.csv"
OUT_JSON = ROOT / "reports" / "mapping_contract_summary.json"
OUT_MD = ROOT / "analysis" / "mapping_contract.md"
POLICY_JSON = ROOT / "pipeline" / "mapping_resolution_policy.json"


REFERENCE_TABLES = {"LOAD_STAFF", "LOAD_USERS", "LOAD_SITES", "LOAD_IWL_PROFILES"}
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
LOOKUP_HINTS = {
    "code",
    "status",
    "type",
    "reason",
    "outcome",
    "specialty",
    "religion",
    "ethnic",
    "nationality",
    "language",
    "marital",
    "occupation",
    "priority",
    "urgency",
}
DERIVED_HINTS = {
    "age",
    "duration",
    "profile",
    "comments",
    "note",
    "summary",
}


TARGET_PRIMARY_SOURCES = {
    "LOAD_PMI": ["PATDATA", "ADTLADDCOR", "GPHISTORY", "GP", "POSTCODE"],
    "LOAD_PMIIDS": ["PATDATA"],
    "LOAD_PMIALIASES": ["PATDATA"],
    "LOAD_PMIADDRS": ["PATDATA", "ADTLADDCOR", "POSTCODE", "PSEUDOPCODE"],
    "LOAD_PMICONTACTS": ["PATDATA"],
    "LOAD_PMIALLERGIES": ["PATDATA"],
    "LOAD_PMISTAFFWARNINGS": ["PATDATA"],
    "LOAD_PMIGPAUDIT": ["PATDATA", "GPHISTORY", "GP"],
    "LOAD_CASENOTELOCS": ["LOCATIONCODES", "LOCN"],
    "LOAD_PMICASENOTEHISTORY": ["PATDATA", "GPHISTORY"],
    "LOAD_RTT_PATHWAYS": ["OPREFERRAL", "WLCURRENT", "WLENTRY", "OPREFTKSTATUS"],
    "LOAD_REFERRALS": ["OPREFERRAL", "OPA", "WLCURRENT", "WLENTRY"],
    "LOAD_RTT_PERIODS": ["OPREFERRAL", "WLCURRENT", "WLENTRY"],
    "LOAD_RTT_EVENTS": ["OPREFERRAL", "WLCURRENT", "WLENTRY", "WLACTIVITY"],
    "LOAD_OPDWAITLIST": ["OPA", "OPREFERRAL", "WLCURRENT", "WLENTRY", "WLACTIVITY"],
    "LOAD_OPDWAITLISTDEF": ["WLACTIVITY", "WLSUSPREASONMF"],
    "LOAD_OPD_APPOINTMENTS": ["OPA", "OPREFERRAL", "OCCANCEL", "HWSAPP"],
    "LOAD_OPD_CODING": ["OPA", "FCEEXT", "AEAUSERDIAG"],
    "LOAD_CMTY_APPOINTMENTS": ["CPSGREFERRAL", "HWSAPP", "OPA", "CPFTEAMS", "CPFLOCATION"],
    "LOAD_IWL": ["WLCURRENT", "WLENTRY", "WLACTIVITY"],
    "LOAD_IWL_DEFERRALS": ["WLACTIVITY", "WLSUSPREASONMF"],
    "LOAD_IWL_TCIS": ["WLACTIVITY", "WLCURRENT"],
    "LOAD_ADT_ADMISSIONS": ["ADMITDISCH", "WLCURRENT", "WLENTRY", "CONSWARDSTAY", "OCCANCEL"],
    "LOAD_ADT_EPISODES": ["FCEEXT", "ADMITDISCH", "SMREPISODE", "CONSEPISODE"],
    "LOAD_ADT_WARDSTAYS": ["ADMITDISCH", "FCEEXT", "WARDSTAY", "CONSWARDSTAY", "WARD"],
    "LOAD_ADT_CODING": ["FCEEXT", "OPA", "CONSEPISDIAG", "CONSEPISPROC", "AEAUSERDIAG"],
    "LOAD_MH_DETENTION_MASTER": ["SMREPISODE", "CPSGREFERRAL", "LEGALSTATUSDETS"],
    "LOAD_MH_DETENTION_TRANSFERS": ["SMREPISODE", "LEGALSTATUSDETS"],
    "LOAD_MH_CPA_MASTER": ["SMREPISODE", "CPFDISCHREASON", "CPFTEAMS"],
    "LOAD_MH_CPA_HISTORY": ["SMREPISODE", "CPFDISCHREASON", "CPFTEAMS"],
    "LOAD_OPD_ARCHIVE": ["OPA", "OPREFERRAL", "OCCANCEL", "HWSAPP"],
    "LOAD_ADT_ARCHIVE": ["ADMITDISCH", "FCEEXT", "CONSWARDSTAY", "WARD", "OCCANCEL"],
    "LOAD_DETENTION_ARCHIVE": ["SMREPISODE", "LEGALSTATUSDETS"],
    "LOAD_CPA_ARCHIVE": ["SMREPISODE", "CPFDISCHREASON"],
}


FIELD_ALIAS = {
    "maincrn": "internalpatientnumber",
    "maincrntype": "idtype",
    "nhsnumber": "nhsnumber",
    "ofbirth": "dateofbirth",
    "dateofbirth": "dateofbirth",
    "patname1": "forenames",
    "patnamefamily": "surname",
    "postcode": "postcode",
    "gpnationalcode": "gpcode",
    "practicenationalcode": "practicecode",
    "admitdate": "admissiondate",
    "dischargedate": "dischargedate",
    "methodofadmission": "methodofadmission",
    "methodofdischarge": "methodofdischarge",
    "sourceofadmission": "sourceofadm",
    "destinationondischarge": "destinationondischarge",
    "consultantcode": "consultant",
    "consultantname": "consultant",
    "eventdate": "statusdt",
    "eventactioncode": "status",
    "eventreasoncode": "reason",
    "timecomplete": "apptendtime",
    "timearrived": "appttime",
    "timeseen": "appttime",
    "apptteam": "specialty",
    "waitlistprofile": "specialty",
    "waitlistdate": "dateonlist",
    "cancelleddate": "datecancelled",
    "refreceiveddate": "referraldate",
    "admitfrom": "sourceofadm",
    "admittedby": "consultant",
    "dischargedby": "consultant",
    "deferralstart": "deferralstartdate",
    "deferralend": "deferralenddate",
    "deferralreason": "deferralreason",
    "deferralcomment": "deferralcomment",
}


def norm(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]", "", name).lower()
    return FIELD_ALIAS.get(cleaned, cleaned)


def load_source() -> Dict[str, List[str]]:
    table_fields = defaultdict(list)
    with SOURCE_CATALOG.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            t = row["table_name"]
            f_name = row["field_name"]
            if f_name and f_name not in table_fields[t]:
                table_fields[t].append(f_name)
    return dict(table_fields)


def load_target() -> Dict[str, List[str]]:
    out = {}
    for p in sorted(TARGET_DIR.glob("*.csv")):
        with p.open("r", encoding="utf-8", newline="") as f:
            out[p.stem] = next(csv.reader(f), [])
    return out


def is_surrogate(field: str) -> bool:
    f = field.lower()
    if f in {"record_number", "system_code", "external_system_id"}:
        return True
    if "record_number" in f:
        return True
    if "recno" in f:
        return True
    if f.startswith("load") and ("record" in f or "recno" in f):
        return True
    return False


def find_source_field(target_field: str, candidates: List[str]) -> Optional[str]:
    tf = norm(target_field)
    # exact normalized
    for sf in candidates:
        if norm(sf) == tf:
            return sf
    # contains
    for sf in candidates:
        ns = norm(sf)
        if tf and (tf in ns or ns in tf):
            return sf
    return None


def classify_business(
    target_table: str,
    target_field: str,
    src_table: str,
    src_field: str,
) -> Tuple[str, str]:
    f = target_field.lower()
    if any(k in f for k in LOOKUP_HINTS):
        return "LOOKUP_TRANSLATION", "Code/value translation required against PAS code sets."
    if any(k in f for k in DERIVED_HINTS):
        return "DERIVED", "Derived/constructed field from source clinical context."
    if target_table.endswith("_ARCHIVE"):
        return "DERIVED", "Archive structure is denormalized and assembled from multiple source entities."
    return "DIRECT_SOURCE", "Direct field transfer from source with datatype/format normalization."


def build() -> None:
    source_tables = load_source()
    target_tables = load_target()

    rows = []
    summary = defaultdict(int)
    table_summary = defaultdict(lambda: defaultdict(int))

    for target_table, target_fields in target_tables.items():
        primary_sources = [s for s in TARGET_PRIMARY_SOURCES.get(target_table, []) if s in source_tables]
        if not primary_sources:
            primary_sources = list(source_tables.keys())

        for target_field in target_fields:
            f_l = target_field.lower()
            mapping_class = ""
            source_table = ""
            source_field = ""
            rule = ""
            confidence = "HIGH"
            notes = ""

            if f_l in PHANTOM_FIELDS:
                mapping_class = "OUT_OF_SCOPE"
                rule = "Exclude: parse artefact field from non-authoritative PDF conversion."
                confidence = "HIGH"
            elif is_surrogate(target_field):
                mapping_class = "SURROGATE_ETL"
                rule = "Generate during ETL sequencing and key orchestration."
                confidence = "HIGH"
            elif target_table in REFERENCE_TABLES:
                mapping_class = "REFERENCE_MASTER_FEED"
                rule = "Populate from operational master/reference datasets (not patient transaction extract)."
                confidence = "HIGH"
            else:
                # semantic mapping search within curated source tables for this target.
                found = False
                for s_tbl in primary_sources:
                    sf = find_source_field(target_field, source_tables[s_tbl])
                    if sf:
                        source_table = s_tbl
                        source_field = sf
                        mapping_class, notes = classify_business(target_table, target_field, s_tbl, sf)
                        rule = f"{s_tbl}.{sf} -> {target_table}.{target_field}"
                        found = True
                        break

                if not found:
                    # limited fallback to all source tables by semantic aliasing.
                    for s_tbl, s_fields in source_tables.items():
                        sf = find_source_field(target_field, s_fields)
                        if sf:
                            source_table = s_tbl
                            source_field = sf
                            mapping_class, notes = classify_business(target_table, target_field, s_tbl, sf)
                            rule = f"{s_tbl}.{sf} -> {target_table}.{target_field}"
                            confidence = "MEDIUM"
                            found = True
                            break

                if not found:
                    if target_table.endswith("_ARCHIVE") or "archive" in target_table.lower():
                        mapping_class = "DERIVED"
                        rule = "Assemble from multi-table joins (transactional + lookup + historical contexts)."
                        notes = "Explicit archive synthesis mapping required."
                        confidence = "MEDIUM"
                    elif any(h in f_l for h in DERIVED_HINTS):
                        mapping_class = "DERIVED"
                        rule = "Derived from clinical workflow context and/or defaults when direct source absent."
                        notes = "No single-source equivalent; ETL derivation rule required."
                        confidence = "MEDIUM"
                    else:
                        mapping_class = "OUT_OF_SCOPE"
                        rule = "No trusted source field in current source catalog; requires SME decision/default."
                        notes = "Business mapping unresolved."
                        confidence = "LOW"

            rows.append(
                {
                    "target_table": target_table,
                    "target_field": target_field,
                    "mapping_class": mapping_class,
                    "primary_source_table": source_table,
                    "primary_source_field": source_field,
                    "mapping_rule": rule,
                    "confidence": confidence,
                    "notes": notes,
                }
            )
            summary[mapping_class] += 1
            table_summary[target_table][mapping_class] += 1

    # Apply explicit policy overrides for unresolved high-priority business fields.
    policy_overrides = []
    if POLICY_JSON.exists():
        with POLICY_JSON.open("r", encoding="utf-8") as f:
            policy_overrides = json.load(f).get("overrides", [])

    override_index = {(o["target_table"], o["target_field"]): o for o in policy_overrides if o.get("target_table") and o.get("target_field")}
    for row in rows:
        key = (row["target_table"], row["target_field"])
        override = override_index.get(key)
        if not override:
            continue
        prev = row["mapping_class"]
        row["mapping_class"] = override.get("mapping_class", row["mapping_class"])
        row["mapping_rule"] = override.get("mapping_rule", row["mapping_rule"])
        row["confidence"] = override.get("confidence", row["confidence"])
        row["notes"] = override.get("notes", row["notes"])
        if override.get("primary_source_table"):
            row["primary_source_table"] = override["primary_source_table"]
        if override.get("primary_source_field"):
            row["primary_source_field"] = override["primary_source_field"]
        if prev != row["mapping_class"]:
            summary[prev] -= 1
            table_summary[row["target_table"]][prev] -= 1
            summary[row["mapping_class"]] += 1
            table_summary[row["target_table"]][row["mapping_class"]] += 1

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "target_table",
                "target_field",
                "mapping_class",
                "primary_source_table",
                "primary_source_field",
                "mapping_rule",
                "confidence",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "target_table_count": len(target_tables),
        "target_field_count": len(rows),
        "mapping_class_counts": dict(summary),
        "policy_override_count": len(override_index),
        "target_table_class_breakdown": {k: dict(v) for k, v in table_summary.items()},
    }
    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    md_lines = [
        "# Mapping Contract",
        "",
        "Date: 2026-02-25",
        "",
        "Strict mapping contract categories:",
        "- `DIRECT_SOURCE`",
        "- `DERIVED`",
        "- `LOOKUP_TRANSLATION`",
        "- `SURROGATE_ETL`",
        "- `REFERENCE_MASTER_FEED`",
        "- `OUT_OF_SCOPE`",
        "",
        f"Target tables: {payload['target_table_count']}",
        f"Target fields: {payload['target_field_count']}",
        "",
        "## Class Counts",
        "",
        "| Class | Count |",
        "|---|---:|",
    ]
    for cls, cnt in sorted(payload["mapping_class_counts"].items(), key=lambda kv: kv[0]):
        md_lines.append(f"| {cls} | {cnt} |")
    md_lines.extend(
        [
            "",
            "Full contract:",
            "- `reports/mapping_contract.csv`",
            "- `reports/mapping_contract_summary.json`",
        ]
    )
    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")


if __name__ == "__main__":
    build()
    print(OUT_CSV)
    print(OUT_JSON)
    print(OUT_MD)
