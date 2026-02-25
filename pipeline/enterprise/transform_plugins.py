from datetime import datetime, timedelta
from typing import Dict


def _upper(v: str) -> str:
    return (v or "").strip().upper()


def _parse_date(v: str):
    s = (v or "").strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%d/%m/%Y")
    except ValueError:
        return None


def _fmt_date(d: datetime) -> str:
    return d.strftime("%d/%m/%Y")


def _default_title(sex: str) -> str:
    s = (sex or "").strip().upper()
    if s in {"1", "M"}:
        return "MR"
    if s in {"2", "F"}:
        return "MRS"
    return "MX"


def apply_domain_plugins(target_table: str, row: Dict[str, str], source_row: Dict[str, str], row_num: int) -> None:
    tt = target_table.upper()
    _apply_pmi_plugins(tt, row, source_row, row_num)
    _apply_adt_plugins(tt, row, source_row, row_num)
    _apply_opd_plugins(tt, row, source_row, row_num)


def _apply_pmi_plugins(target_table: str, row: Dict[str, str], source_row: Dict[str, str], row_num: int) -> None:
    if not target_table.startswith("LOAD_PMI"):
        return

    if "main_crn_type" in row and not row["main_crn_type"]:
        row["main_crn_type"] = "PAS"

    if "main_crn" in row and not row["main_crn"]:
        row["main_crn"] = (source_row.get("InternalPatientNumber") or source_row.get("Intpatno") or "").strip()

    if "nhs_number" in row:
        row["nhs_number"] = "".join(ch for ch in row["nhs_number"] if ch.isdigit())

    if "title" in row and not row["title"]:
        row["title"] = _default_title(row.get("sex", ""))

    if "date_registered" in row and not row["date_registered"]:
        row["date_registered"] = "01/01/2000"

    if "pat_name_1" in row:
        row["pat_name_1"] = _upper(row["pat_name_1"])
    if "pat_name_family" in row:
        row["pat_name_family"] = _upper(row["pat_name_family"])
    if "post_code" in row:
        row["post_code"] = _upper(row["post_code"])

    if target_table == "LOAD_PMIADDRS":
        if "address_type" in row and not row["address_type"]:
            row["address_type"] = "H"
        if "applies_start" in row and not row["applies_start"]:
            row["applies_start"] = "01/01/2000"
        if "applies_end" in row and not row["applies_end"]:
            row["applies_end"] = "31/12/9999"

    if target_table == "LOAD_PMICONTACTS":
        if "contact_type" in row and not row["contact_type"]:
            row["contact_type"] = "NOK"
        if "applies_start" in row and not row["applies_start"]:
            row["applies_start"] = "01/01/2000"
        if "applies_end" in row and not row["applies_end"]:
            row["applies_end"] = "31/12/9999"


def _apply_adt_plugins(target_table: str, row: Dict[str, str], source_row: Dict[str, str], row_num: int) -> None:
    if not target_table.startswith("LOAD_ADT"):
        return

    if target_table == "LOAD_ADT_ADMISSIONS":
        adm = _parse_date(row.get("admit_date", ""))
        if adm and "estimated_discharge_date" in row and not row["estimated_discharge_date"]:
            row["estimated_discharge_date"] = _fmt_date(adm + timedelta(days=3))
        if adm and "discharge_date" in row and not row["discharge_date"]:
            row["discharge_date"] = _fmt_date(adm + timedelta(days=3))
        if "admission_type" in row and not row["admission_type"]:
            row["admission_type"] = "ELEC"
        if "admit_type" in row and not row["admit_type"]:
            row["admit_type"] = "E"

    if target_table == "LOAD_ADT_EPISODES":
        if "episode_order" in row and not row["episode_order"]:
            row["episode_order"] = "1"
        if "duration_of_episode" in row and not row["duration_of_episode"]:
            row["duration_of_episode"] = "3"

    if target_table == "LOAD_ADT_WARDSTAYS":
        if "is_home_stay" in row and not row["is_home_stay"]:
            row["is_home_stay"] = "N"
        if "is_awol" in row and not row["is_awol"]:
            row["is_awol"] = "N"
        if "bed_location" in row and not row["bed_location"]:
            row["bed_location"] = f"BED{row_num:03d}"


def _apply_opd_plugins(target_table: str, row: Dict[str, str], source_row: Dict[str, str], row_num: int) -> None:
    if not target_table.startswith("LOAD_OPD"):
        return

    if target_table == "LOAD_OPD_APPOINTMENTS":
        if "walkin_flag" in row and not row["walkin_flag"]:
            row["walkin_flag"] = "N"
        if "time_arrived" in row and not row["time_arrived"]:
            row["time_arrived"] = "09:00"
        if "time_seen" in row and not row["time_seen"]:
            row["time_seen"] = "09:20"
        if "time_complete" in row and not row["time_complete"]:
            row["time_complete"] = "09:40"

    if target_table == "LOAD_OPDWAITLISTDEF":
        if "deferral_start" in row and not row["deferral_start"]:
            row["deferral_start"] = "01/01/2024"
        if "deferral_end" in row and not row["deferral_end"]:
            row["deferral_end"] = "08/01/2024"
