import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple


ROOT = Path(__file__).resolve().parents[1]
SOURCE_CATALOG = ROOT / "schemas" / "source_schema_catalog.csv"
TARGET_DIR = ROOT / "mock_data" / "target"
REPORT_CSV = ROOT / "reports" / "semantic_mapping_matrix.csv"
REPORT_JSON = ROOT / "reports" / "semantic_mapping_summary.json"
REPORT_MD = ROOT / "analysis" / "source_target_semantic_mapping.md"


PRIORITY_SOURCE_TABLES = {
    "PATDATA",
    "ADMITDISCH",
    "OPA",
    "FCEEXT",
    "OPREFERRAL",
    "WLCURRENT",
    "WLENTRY",
    "WLACTIVITY",
    "CPSGREFERRAL",
    "SMREPISODE",
    "AEA",
    "HWSAPP",
    "ADTLADDCOR",
}


TARGET_HINT_TABLES = {
    "LOAD_PMI": {"PATDATA", "ADTLADDCOR"},
    "LOAD_PMIIDS": {"PATDATA"},
    "LOAD_PMIALIASES": {"PATDATA"},
    "LOAD_PMIADDRS": {"PATDATA", "ADTLADDCOR"},
    "LOAD_PMICONTACTS": {"PATDATA"},
    "LOAD_PMIALLERGIES": {"PATDATA"},
    "LOAD_PMISTAFFWARNINGS": {"PATDATA"},
    "LOAD_PMIGPAUDIT": {"PATDATA"},
    "LOAD_CASENOTELOCS": {"PATDATA"},
    "LOAD_PMICASENOTEHISTORY": {"PATDATA"},
    "LOAD_RTT_PATHWAYS": {"OPREFERRAL", "WLCURRENT", "WLENTRY"},
    "LOAD_REFERRALS": {"OPREFERRAL", "OPA", "WLCURRENT"},
    "LOAD_RTT_PERIODS": {"OPREFERRAL", "WLCURRENT", "WLENTRY"},
    "LOAD_RTT_EVENTS": {"OPREFERRAL", "WLCURRENT", "WLENTRY", "WLACTIVITY"},
    "LOAD_OPDWAITLIST": {"OPA", "OPREFERRAL", "WLCURRENT"},
    "LOAD_OPDWAITLISTDEF": {"WLACTIVITY", "WLCURRENT"},
    "LOAD_OPD_APPOINTMENTS": {"OPA", "OPREFERRAL"},
    "LOAD_OPD_CODING": {"OPA", "FCEEXT"},
    "LOAD_CMTY_APPOINTMENTS": {"CPSGREFERRAL", "HWSAPP", "OPA"},
    "LOAD_IWL_PROFILES": {"WLCURRENT", "WLENTRY"},
    "LOAD_IWL": {"WLCURRENT", "WLENTRY"},
    "LOAD_IWL_DEFERRALS": {"WLACTIVITY", "WLCURRENT"},
    "LOAD_IWL_TCIS": {"WLACTIVITY", "WLCURRENT"},
    "LOAD_ADT_ADMISSIONS": {"ADMITDISCH", "WLCURRENT", "WLENTRY"},
    "LOAD_ADT_EPISODES": {"FCEEXT", "ADMITDISCH", "SMREPISODE"},
    "LOAD_ADT_WARDSTAYS": {"ADMITDISCH", "FCEEXT"},
    "LOAD_ADT_CODING": {"FCEEXT", "OPA"},
    "LOAD_MH_DETENTION_MASTER": {"SMREPISODE", "CPSGREFERRAL"},
    "LOAD_MH_DETENTION_TRANSFERS": {"SMREPISODE"},
    "LOAD_MH_CPA_MASTER": {"SMREPISODE"},
    "LOAD_MH_CPA_HISTORY": {"SMREPISODE"},
    "LOAD_OPD_ARCHIVE": {"OPA", "OPREFERRAL"},
    "LOAD_ADT_ARCHIVE": {"ADMITDISCH", "FCEEXT"},
    "LOAD_DETENTION_ARCHIVE": {"SMREPISODE"},
    "LOAD_CPA_ARCHIVE": {"SMREPISODE"},
}


REFERENCE_TARGET_TABLES = {"LOAD_STAFF", "LOAD_USERS", "LOAD_SITES", "LOAD_IWL_PROFILES"}
UNIVERSAL_TARGET_FIELDS = {"record_number", "system_code", "external_system_id"}


TOKEN_EQUIV = {
    "mrn": "internalpatientnumber",
    "crn": "internalpatientnumber",
    "main": "",
    "pat": "patient",
    "pt": "patient",
    "dob": "dateofbirth",
    "of": "",
    "date10": "date",
    "dttime": "datetime",
    "dtime": "datetime",
    "dt": "date",
    "dtm": "datetime",
    "int": "internal",
    "gp": "gp",
    "gdp": "gdp",
    "nhs": "nhs",
    "wl": "waitlist",
    "appt": "appointment",
    "adm": "admission",
    "disch": "discharge",
    "cons": "consultant",
    "addr": "address",
    "postcd": "postcode",
    "post_code": "postcode",
    "sex": "sex",
    "ethnic": "ethnic",
    "diag": "diagnosis",
    "proc": "procedure",
    "rtt": "rtt",
    "hosp": "hospital",
}


def normalize_tokens(name: str) -> List[str]:
    raw = re.sub(r"[^A-Za-z0-9_]", "_", name)
    raw = re.sub(r"([a-z])([A-Z])", r"\1_\2", raw)
    tokens = [t.lower() for t in raw.split("_") if t]
    out = []
    for t in tokens:
        mapped = TOKEN_EQUIV.get(t, t)
        if mapped:
            out.extend(mapped.split("_"))
    return [t for t in out if t]


def score_match(target_field: str, source_field: str) -> float:
    t = normalize_tokens(target_field)
    s = normalize_tokens(source_field)
    if not t or not s:
        return 0.0

    tset = set(t)
    sset = set(s)
    inter = tset & sset
    union = tset | sset
    jaccard = len(inter) / len(union)

    bonus = 0.0
    if "".join(t) == "".join(s):
        bonus += 0.35
    if target_field.lower() == source_field.lower():
        bonus += 0.45
    if any(x in inter for x in ("nhs", "internalpatientnumber", "dateofbirth", "episodenumber")):
        bonus += 0.1
    if ("date" in tset and "date" in sset) or ("datetime" in tset and "datetime" in sset):
        bonus += 0.05

    return min(1.0, jaccard + bonus)


def score_match_tokens(target_field: str, target_tokens: List[str], source_field: str, source_tokens: List[str]) -> float:
    if not target_tokens or not source_tokens:
        return 0.0

    tset = set(target_tokens)
    sset = set(source_tokens)
    inter = tset & sset
    union = tset | sset
    jaccard = len(inter) / len(union)

    bonus = 0.0
    if "".join(target_tokens) == "".join(source_tokens):
        bonus += 0.35
    if target_field.lower() == source_field.lower():
        bonus += 0.45
    if any(x in inter for x in ("nhs", "internalpatientnumber", "dateofbirth", "episodenumber")):
        bonus += 0.1
    if ("date" in tset and "date" in sset) or ("datetime" in tset and "datetime" in sset):
        bonus += 0.05

    return min(1.0, jaccard + bonus)


def load_source_catalog() -> List[Dict[str, str]]:
    with SOURCE_CATALOG.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_target_headers() -> Dict[str, List[str]]:
    out = {}
    for csv_path in sorted(TARGET_DIR.glob("*.csv")):
        with csv_path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
        out[csv_path.stem] = header
    return out


def best_match(
    target_table: str,
    target_field: str,
    source_rows: List[Dict[str, str]],
    source_tokens_cache: Dict[Tuple[str, str], List[str]],
    target_tokens_cache: Dict[str, List[str]],
    source_by_table: Dict[str, List[Dict[str, str]]],
) -> Tuple[Dict[str, str], float]:
    hint_tables = TARGET_HINT_TABLES.get(target_table, set())
    best_row = {}
    best_score = -1.0

    t_tokens = target_tokens_cache.setdefault(target_field, normalize_tokens(target_field))

    candidate_rows: List[Dict[str, str]] = []
    for t in hint_tables:
        candidate_rows.extend(source_by_table.get(t, []))
    if not candidate_rows:
        candidate_rows = source_rows

    for row in candidate_rows:
        st = row["table_name"]
        sf = row["field_name"]
        s_tokens = source_tokens_cache[(st, sf)]
        s = score_match_tokens(target_field, t_tokens, sf, s_tokens)

        if hint_tables and st in hint_tables:
            s += 0.08
        if st in PRIORITY_SOURCE_TABLES:
            s += 0.03
        s = min(1.0, s)

        if s > best_score:
            best_score = s
            best_row = row

    # If hint tables fail to produce a usable candidate, expand search globally.
    if best_score < 0.55 and candidate_rows is not source_rows:
        for row in source_rows:
            st = row["table_name"]
            sf = row["field_name"]
            s_tokens = source_tokens_cache[(st, sf)]
            s = score_match_tokens(target_field, t_tokens, sf, s_tokens)
            if hint_tables and st in hint_tables:
                s += 0.08
            if st in PRIORITY_SOURCE_TABLES:
                s += 0.03
            s = min(1.0, s)
            if s > best_score:
                best_score = s
                best_row = row
    return best_row, best_score


def classify_score(score: float, target_table: str, target_field: str) -> str:
    if target_field in UNIVERSAL_TARGET_FIELDS:
        return "SYSTEM_FIELD"
    if target_table in REFERENCE_TARGET_TABLES:
        return "REFERENCE_REQUIRED"
    if score >= 0.86:
        return "HIGH_CONFIDENCE"
    if score >= 0.70:
        return "PROBABLE"
    if score >= 0.55:
        return "LOW_CONFIDENCE"
    return "UNMAPPED"


def run() -> None:
    source_rows = load_source_catalog()
    target_headers = load_target_headers()
    source_tokens_cache = {
        (row["table_name"], row["field_name"]): normalize_tokens(row["field_name"]) for row in source_rows
    }
    target_tokens_cache: Dict[str, List[str]] = {}
    source_by_table = defaultdict(list)
    for row in source_rows:
        source_by_table[row["table_name"]].append(row)

    matrix_rows: List[Dict[str, str]] = []
    used_source_fields: Set[Tuple[str, str]] = set()
    stats = defaultdict(int)
    per_target_table = defaultdict(lambda: defaultdict(int))

    for target_table, fields in target_headers.items():
        for target_field in fields:
            match_row, raw_score = best_match(
                target_table,
                target_field,
                source_rows,
                source_tokens_cache,
                target_tokens_cache,
                source_by_table,
            )
            status = classify_score(raw_score, target_table, target_field)

            source_table = match_row.get("table_name", "")
            source_field = match_row.get("field_name", "")
            in_priority = "Y" if source_table in PRIORITY_SOURCE_TABLES else "N"
            hinted = "Y" if source_table in TARGET_HINT_TABLES.get(target_table, set()) else "N"

            notes = ""
            if status in {"HIGH_CONFIDENCE", "PROBABLE"}:
                used_source_fields.add((source_table, source_field))
            elif status == "REFERENCE_REQUIRED":
                notes = "Target table is likely mastered from PAS setup/reference datasets, not V83 transactional extracts."
            elif status == "UNMAPPED":
                notes = "No reliable semantic candidate in source catalog; requires manual mapping decision."
            elif in_priority == "N":
                notes = "Best candidate is outside the 13 priority source tables."

            matrix_rows.append(
                {
                    "target_table": target_table,
                    "target_field": target_field,
                    "best_source_table": source_table,
                    "best_source_field": source_field,
                    "score": f"{raw_score:.3f}",
                    "status": status,
                    "source_in_13_priority": in_priority,
                    "source_in_target_hint_tables": hinted,
                    "notes": notes,
                }
            )
            stats[status] += 1
            per_target_table[target_table][status] += 1

    REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "target_table",
                "target_field",
                "best_source_table",
                "best_source_field",
                "score",
                "status",
                "source_in_13_priority",
                "source_in_target_hint_tables",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(matrix_rows)

    source_by_table = defaultdict(set)
    for row in source_rows:
        source_by_table[row["table_name"]].add(row["field_name"])

    used_by_table = defaultdict(set)
    for t, f in used_source_fields:
        used_by_table[t].add(f)

    priority_unused = {}
    for t in sorted(PRIORITY_SOURCE_TABLES):
        total = len(source_by_table[t])
        used = len(used_by_table[t])
        priority_unused[t] = {
            "total_fields": total,
            "mapped_fields": used,
            "unmapped_fields": total - used,
            "coverage_pct": round((used / total) * 100, 1) if total else 0.0,
        }

    summary = {
        "target_table_count": len(target_headers),
        "target_field_count": sum(len(v) for v in target_headers.values()),
        "source_table_count": len(source_by_table),
        "source_field_count": sum(len(v) for v in source_by_table.values()),
        "status_counts": dict(stats),
        "priority_source_coverage": priority_unused,
    }
    with REPORT_JSON.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    top_unmapped_tables = sorted(
        per_target_table.items(),
        key=lambda kv: kv[1].get("UNMAPPED", 0),
        reverse=True,
    )[:15]

    lines = [
        "# Source-Target Semantic Mapping Re-check",
        "",
        "Date: 2026-02-25",
        "",
        "This mapping was generated by semantic matching between:",
        "- source catalog: `schemas/source_schema_catalog.csv` (417 tables, 5,387 fields)",
        "- target schema actually generated: `mock_data/target/*.csv` (38 tables)",
        "",
        "## Why previous work focused on 13 source tables",
        "",
        "The 13 tables are the priority transactional extract set identified in `source_schema_profile.md` for core migration flows.",
        "They do not represent the full source estate (417 tables), and some target tables are reference/setup or archive-oriented.",
        "",
        "## Summary",
        "",
        f"- Target tables: {summary['target_table_count']}",
        f"- Target fields evaluated: {summary['target_field_count']}",
        f"- High-confidence semantic matches: {stats.get('HIGH_CONFIDENCE', 0)}",
        f"- Probable matches: {stats.get('PROBABLE', 0)}",
        f"- Low-confidence matches: {stats.get('LOW_CONFIDENCE', 0)}",
        f"- Unmapped fields (manual decisions required): {stats.get('UNMAPPED', 0)}",
        f"- Reference-required fields (not expected from V83 transactional source): {stats.get('REFERENCE_REQUIRED', 0)}",
        "",
        "## Tables With Most Unmapped Fields",
        "",
        "| Target Table | Unmapped Field Count |",
        "|---|---:|",
    ]
    for t, cnts in top_unmapped_tables:
        lines.append(f"| {t} | {cnts.get('UNMAPPED', 0)} |")

    lines.extend(
        [
            "",
            "## 13 Priority Source Tables Coverage",
            "",
            "| Source Table | Total Fields | Mapped Fields | Unmapped Fields | Coverage % |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for t in sorted(PRIORITY_SOURCE_TABLES):
        s = priority_unused[t]
        lines.append(
            f"| {t} | {s['total_fields']} | {s['mapped_fields']} | {s['unmapped_fields']} | {s['coverage_pct']} |"
        )

    lines.extend(
        [
            "",
            "## Outputs",
            "",
            "- Full field-level matrix: `reports/semantic_mapping_matrix.csv`",
            "- Summary metrics: `reports/semantic_mapping_summary.json`",
        ]
    )
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run()
    print(REPORT_CSV)
    print(REPORT_JSON)
    print(REPORT_MD)
