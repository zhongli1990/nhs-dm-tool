import csv
import json
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple
import xml.etree.ElementTree as ET

import pypdf

from io_utils import write_json


def _read_xlsx_rows(xlsx_path: Path) -> List[Dict[str, str]]:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    with zipfile.ZipFile(xlsx_path, "r") as zf:
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        nss = {
            "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        }
        sheet = wb.find('.//a:sheets/a:sheet[@name="Columns"]', nss)
        if sheet is None:
            sheet = wb.find(".//a:sheets/a:sheet", nss)
        rid = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]

        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rns = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
        target = {r.attrib["Id"]: r.attrib["Target"] for r in rels.findall(".//r:Relationship", rns)}[rid]

        shared_strings = []
        if "xl/sharedStrings.xml" in zf.namelist():
            sst = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in sst.findall(f".//{ns}si"):
                text = "".join(t.text or "" for t in si.findall(f".//{ns}t"))
                shared_strings.append(text)

        sheet_xml = ET.fromstring(zf.read("xl/" + target))
        rows: Dict[int, Dict[str, str]] = {}
        for cell in sheet_xml.findall(f".//{ns}c"):
            ref = cell.attrib.get("r", "")
            row_num = int("".join(ch for ch in ref if ch.isdigit()) or "0")
            col = "".join(ch for ch in ref if ch.isalpha())
            v = cell.find(f"{ns}v")
            if v is None or v.text is None:
                continue
            value = v.text
            if cell.attrib.get("t") == "s":
                value = shared_strings[int(value)]
            rows.setdefault(row_num, {})[col] = value

        headers = rows.get(1, {})
        out: List[Dict[str, str]] = []
        for row_num in sorted(k for k in rows if k > 1):
            r = rows[row_num]
            out.append(
                {
                    "table_name": r.get("A", "").strip(),
                    "field_name": r.get("B", "").strip(),
                    "size": r.get("C", "").strip(),
                    "data_element": r.get("D", "").strip(),
                    "description": r.get("E", "").strip(),
                    "logical_delete_flag": r.get("F", "").strip(),
                    "released_at": r.get("G", "").strip(),
                }
            )
        return out


def _clean_table(token: str) -> str:
    token = "".join(ch for ch in token.strip() if ch.isalnum() or ch == "_")
    lower_idx = next((i for i, ch in enumerate(token) if ch.islower()), None)
    if lower_idx is not None:
        cut = lower_idx - 1 if lower_idx > 0 and token[lower_idx - 1].isupper() else lower_idx
        token = token[:cut]
    return token.upper()


def _clean_field(token: str) -> Tuple[str, float]:
    raw = token
    token = "".join(ch for ch in token.strip() if ch.isalnum() or ch == "_")
    if not token:
        return "", 0.0

    confidence = 1.0
    token = re.sub(r"^(varchar2|number|date|char|clob|timestamp)\d*", "", token, flags=re.IGNORECASE)

    for i in range(1, len(token)):
        if token[i].isupper() and token[i - 1].islower():
            token = token[:i]
            confidence -= 0.15
            break

    lower_idx = next((i for i, ch in enumerate(token) if ch.islower()), None)
    if lower_idx is not None and lower_idx > 0 and token[lower_idx - 1].isupper():
        if token[: lower_idx - 1].upper() == token[: lower_idx - 1]:
            token = token[: lower_idx - 1]
            confidence -= 0.2

    field = token.lower().strip("_")
    for suffix in (
        "must",
        "loaded",
        "maps",
        "next",
        "patient",
        "practice",
        "unique",
        "controls",
        "permission",
        "only",
    ):
        if field.endswith(suffix) and len(field) > len(suffix) + 2:
            field = field[: -len(suffix)]
            confidence -= 0.1
            break

    if field.startswith("date10"):
        field = field.replace("date10", "", 1)
        confidence -= 0.25
    if field.startswith("varchar2"):
        field = field.replace("varchar2", "", 1)
        confidence -= 0.25

    if field in {"for", "to", "of", "the", "and", "or", "if", "is", "on", "in", "at", "an", "as", "by"}:
        return "", 0.0
    if len(field) < 3:
        return "", 0.0

    if field != raw.lower():
        confidence = max(0.35, confidence)
    return field, max(0.0, min(confidence, 1.0))


def _extract_target_pdf(pdf_path: Path) -> List[Dict[str, str]]:
    reader = pypdf.PdfReader(str(pdf_path))
    current_table = "UNKNOWN"
    rows: List[Dict[str, str]] = []

    table_pattern = re.compile(r"TABLE NAME:\s*([^\s]+)", re.IGNORECASE)
    field_pattern = re.compile(
        r"(VARCHAR2|NUMBER|DATE|CHAR|CLOB|TIMESTAMP)\s*([0-9]{0,4})\s*([A-Za-z][A-Za-z0-9_]*)",
        re.IGNORECASE,
    )

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        for m in table_pattern.finditer(text):
            table = _clean_table(m.group(1))
            if table.startswith("LOAD_"):
                current_table = table

        for m in field_pattern.finditer(text):
            data_type = m.group(1).upper()
            length = m.group(2).strip()
            raw_field = m.group(3).strip()
            cleaned_field, confidence = _clean_field(raw_field)
            if not cleaned_field:
                continue
            if current_table == "UNKNOWN":
                continue
            rows.append(
                {
                    "table_name": current_table,
                    "field_name": cleaned_field,
                    "raw_field_name": raw_field,
                    "data_type": data_type,
                    "length": length,
                    "mandatory_hint": "Y" if "MUST" in raw_field.upper() else "N",
                    "parse_confidence": f"{confidence:.2f}",
                    "source_page": str(page_num),
                }
            )

    dedup: Dict[Tuple[str, str, str, str], Dict[str, str]] = {}
    for row in rows:
        key = (row["table_name"], row["field_name"], row["data_type"], row["length"])
        existing = dedup.get(key)
        if existing is None or float(row["parse_confidence"]) > float(existing["parse_confidence"]):
            dedup[key] = row
    return list(dedup.values())


def _extract_target_md_table_sections(md_path: Path) -> List[str]:
    if not md_path.exists():
        return []
    text = md_path.read_text(encoding="utf-8", errors="ignore").replace("\\_", "_")
    names = [m.group(1).upper() for m in re.finditer(r"TABLE NAME:\s*(LOAD_[A-Z0-9_]+)", text, flags=re.IGNORECASE)]

    def normalize(name: str) -> str:
        out = name
        for suffix in ("INPATIENT", "PATIENT", "HOSPITAL", "ALTERA"):
            if out.endswith(suffix) and out != f"LOAD_{suffix}":
                out = out[: -len(suffix)]
        return out

    normalized = sorted({normalize(n) for n in names})
    return normalized


def _write_csv(path: Path, rows: List[Dict[str, str]], headers: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})


def extract_all(project_root: Path) -> Dict[str, int]:
    req = project_root / "requirement_spec"
    source_xlsx = req / "Source PAS - Data Dictionary V83 INQuire DD PC83.xlsx"
    target_pdf = req / "Target PAS - PAS 18.4 Data Migration Technical Guide - FOR REF ONLY NOT TO BE USED.pdf"
    target_md = req / "Copy of Target PAS - PAS 18.4 Data Migration Technical Guide - FOR REF ONLY NOT TO BE USED.md"
    source_docx_md = req / "Source PAS - PAS_PC60_DataDictionary.docx.md"

    source_rows = _read_xlsx_rows(source_xlsx)
    target_rows = _extract_target_pdf(target_pdf)

    source_catalog = project_root / "schemas" / "source_schema_catalog.csv"
    target_catalog = project_root / "schemas" / "target_schema_catalog.csv"

    _write_csv(
        source_catalog,
        source_rows,
        ["table_name", "field_name", "size", "data_element", "description", "logical_delete_flag", "released_at"],
    )
    _write_csv(
        target_catalog,
        target_rows,
        ["table_name", "field_name", "raw_field_name", "data_type", "length", "mandatory_hint", "parse_confidence", "source_page"],
    )

    source_table_counts = Counter(r["table_name"] for r in source_rows if r["table_name"])
    target_table_counts = Counter(r["table_name"] for r in target_rows if r["table_name"])
    target_conf_avg = (
        sum(float(r["parse_confidence"]) for r in target_rows) / max(1, len(target_rows))
    )
    md_tables = _extract_target_md_table_sections(target_md)
    pdf_tables = sorted(target_table_counts.keys())

    summary = {
        "source_total_fields": len(source_rows),
        "source_total_tables": len(source_table_counts),
        "target_total_fields": len(target_rows),
        "target_total_tables": len(target_table_counts),
        "target_parse_confidence_avg": round(target_conf_avg, 3),
        "target_md_table_section_count": len(md_tables),
        "source_docx_md_bytes": source_docx_md.stat().st_size if source_docx_md.exists() else -1,
        "source_top_tables": source_table_counts.most_common(20),
        "target_top_tables": target_table_counts.most_common(20),
        "target_tables_from_md_not_in_pdf_catalog": sorted(set(md_tables) - set(pdf_tables)),
        "target_tables_from_pdf_catalog_not_in_md_sections": sorted(set(pdf_tables) - set(md_tables)),
    }
    write_json(project_root / "schemas" / "schema_catalog_summary.json", summary)
    return summary


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    stats = extract_all(root)
    print(json.dumps(stats, indent=2))
