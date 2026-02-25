"""
generate_all_mock_data.py  (v2)
────────────────────────────────────────────────────────────────────────────────
Generates 20-patient mock data CSVs for:
  * All 38 PAS 18.4 target LOAD_ tables  ->  mock_data/target/
  * All 13 source tables                  ->  mock_data/source/

Design principles
─────────────────
1. 20 fictional NHS patients with consistent identities across ALL tables.
2. FK surrogate-key chains maintained (PMI -> RTT -> REFERRAL -> PERIOD ->
   EVENT / OPD / IWL -> ADT admissions -> episodes -> ward stays).
3. Source tables PATDATA, ADMITDISCH and HWSAPP derive columns dynamically
   from source_schema_catalog.csv (131, 69 and 90 fields respectively).
4. All dates in DD/MM/YYYY target format; source dates in CCYYMMDDHHMM
   where the source schema specifies internal integer format.

Run from the data_migration root:
    python pipeline/generate_all_mock_data.py
"""

import csv
import random
import argparse
from pathlib import Path
from datetime import date

# ────────────────────────────────────────────────────────────────────────────
# Paths
# ────────────────────────────────────────────────────────────────────────────
ROOT           = Path(__file__).resolve().parents[1]
TARGET_CATALOG = ROOT / "schemas" / "target_schema_catalog.csv"
SOURCE_CATALOG = ROOT / "schemas" / "source_schema_catalog.csv"
SOURCE_OUT     = ROOT / "mock_data" / "source"
TARGET_OUT     = ROOT / "mock_data" / "target"

ROWS = 20  # patients / rows per table

# Schema profile-driven target column supplements for key tables where PDF parsing
# loses columns due merged cells/artefacts.
TARGET_SCHEMA_OVERRIDES = {
    "LOAD_ADT_ADMISSIONS": [
        "source_of_admission",
        "method_of_admission",
        "method_of_discharge",
        "destination_on_discharge",
        "admission_outcome",
        "admission_type",
        "physical_discharge_date",
        "admit_type",
        "consultant_code",
        "consultant_name",
    ],
    "LOAD_ADT_EPISODES": [
        "episode_start",
        "episode_end",
        "episode_order",
        "duration_of_episode",
        "age_at_start_of_episode",
        "specialty",
        "consultant_code",
        "consultant_name",
        "patient_category",
        "actual_management",
    ],
    "LOAD_ADT_CODING": [
        "diagnosis_scheme",
        "primary_diagnosis_code",
        "primary_diagnosis_desc",
        "diagnosis_1_code",
        "diagnosis_1_desc",
        "diagnosis_2_code",
        "diagnosis_2_desc",
        "procedure_scheme",
        "primary_procedure_code",
        "primary_procedure_desc",
        "procedure_1_code",
        "procedure_1_desc",
        "hrg",
        "comments",
    ],
    "LOAD_IWL_DEFERRALS": [
        "deferral_end",
        "deferral_reason",
        "deferral_comment",
    ],
    "LOAD_PMIADDRS": [
        "date_of_birth",
        "main_crn_type",
        "main_crn",
        "address_5",
        "country_code",
    ],
}

SOURCE_PRIORITY_TABLES = [
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
]

# Additional non-13 reference/lookup/context source tables that are often needed
# to complete value translation and denormalized archive outputs.
EXTRA_SOURCE_REFERENCE_TABLES = [
    "CONSWARDSTAY",
    "CONSEPISODE",
    "CONSEPISDIAG",
    "CONSEPISPROC",
    "OCCANCEL",
    "LOCATIONCODES",
    "LOCN",
    "WARD",
    "CONSMAST",
    "CONSPEC",
    "GP",
    "GPHISTORY",
    "POSTCODE",
    "PSEUDOPCODE",
    "OPREFTKSTATUS",
    "OPREFTKSTATUSMF",
    "OPBOOKTYPEMF",
    "IPBOOKTYPEMF",
    "WLSUSPREASONMF",
    "WLREMOVALREASON",
    "CPFTEAMS",
    "CPFLOCATION",
    "CPFDISCHREASON",
    "LEGALSTATUSDETS",
    "ALLOCATEDCONTRACT",
]

# ────────────────────────────────────────────────────────────────────────────
# 20 fictional NHS patients  -  stable identity across every table
# ────────────────────────────────────────────────────────────────────────────
PATIENTS = [
    {"mrn":"MRN10001","nhs":"9434765901","name_1":"JAMES",    "family":"SMITH",    "dob":"14/03/1958","dob_int":"19580314","sex":"1","gp":"G1234567","practice":"P40001","pc":"SW1A 2AA","addr1":"14 High Street",     "addr2":"London",     "ethnic":"A"},
    {"mrn":"MRN10002","nhs":"9434765902","name_1":"SARAH",    "family":"JONES",    "dob":"22/07/1972","dob_int":"19720722","sex":"2","gp":"G2345678","practice":"P40002","pc":"E1 6AN", "addr1":"22 Church Lane",    "addr2":"Manchester", "ethnic":"B"},
    {"mrn":"MRN10003","nhs":"9434765903","name_1":"MOHAMMED", "family":"PATEL",    "dob":"05/11/1965","dob_int":"19651105","sex":"1","gp":"G3456789","practice":"P40003","pc":"N1 9GU", "addr1":"5 Oak Avenue",      "addr2":"Birmingham", "ethnic":"C"},
    {"mrn":"MRN10004","nhs":"9434765904","name_1":"EMILY",    "family":"WILLIAMS", "dob":"30/01/1981","dob_int":"19810130","sex":"2","gp":"G4567890","practice":"P40004","pc":"EC4M 5WT","addr1":"8 Station Road",    "addr2":"Leeds",      "ethnic":"D"},
    {"mrn":"MRN10005","nhs":"9434765905","name_1":"DAVID",    "family":"BROWN",    "dob":"18/09/1943","dob_int":"19430918","sex":"1","gp":"G5678901","practice":"P40005","pc":"WC2N 5DU","addr1":"3 The Green",       "addr2":"Sheffield",  "ethnic":"G"},
    {"mrn":"MRN10006","nhs":"9434765906","name_1":"PRIYA",    "family":"SHARMA",   "dob":"04/04/1979","dob_int":"19790404","sex":"2","gp":"G6789012","practice":"P40006","pc":"SE1 7PB", "addr1":"17 Rose Avenue",   "addr2":"Bristol",    "ethnic":"H"},
    {"mrn":"MRN10007","nhs":"9434765907","name_1":"ROBERT",   "family":"TAYLOR",   "dob":"27/12/1955","dob_int":"19551227","sex":"1","gp":"G7890123","practice":"P40007","pc":"W1A 1AA", "addr1":"9 Elm Close",      "addr2":"Liverpool",  "ethnic":"A"},
    {"mrn":"MRN10008","nhs":"9434765908","name_1":"FATIMA",   "family":"AHMED",    "dob":"11/06/1988","dob_int":"19880611","sex":"2","gp":"G8901234","practice":"P40008","pc":"SW1A 2AA","addr1":"33 Park Road",     "addr2":"London",     "ethnic":"C"},
    {"mrn":"MRN10009","nhs":"9434765909","name_1":"THOMAS",   "family":"DAVIS",    "dob":"03/08/1950","dob_int":"19500803","sex":"1","gp":"G9012345","practice":"P40009","pc":"E1 6AN", "addr1":"6 Victoria Street","addr2":"Nottingham", "ethnic":"Z"},
    {"mrn":"MRN10010","nhs":"9434765910","name_1":"LUCY",     "family":"WILSON",   "dob":"16/02/1993","dob_int":"19930216","sex":"2","gp":"G0123456","practice":"P40010","pc":"N1 9GU", "addr1":"2 Bridge Street",  "addr2":"Newcastle",  "ethnic":"A"},
    {"mrn":"MRN10011","nhs":"9434765911","name_1":"GEORGE",   "family":"HARRIS",   "dob":"29/10/1967","dob_int":"19671029","sex":"1","gp":"G1122334","practice":"P40011","pc":"EC4M 5WT","addr1":"45 Kings Lane",    "addr2":"Oxford",     "ethnic":"B"},
    {"mrn":"MRN10012","nhs":"9434765912","name_1":"AMELIA",   "family":"MARTIN",   "dob":"07/05/1975","dob_int":"19750507","sex":"2","gp":"G2233445","practice":"P40012","pc":"WC2N 5DU","addr1":"19 Queen Street",  "addr2":"Cambridge",  "ethnic":"D"},
    {"mrn":"MRN10013","nhs":"9434765913","name_1":"OLIVER",   "family":"THOMPSON", "dob":"20/03/1961","dob_int":"19610320","sex":"1","gp":"G3344556","practice":"P40013","pc":"SE1 7PB", "addr1":"88 Mill Road",     "addr2":"Coventry",   "ethnic":"G"},
    {"mrn":"MRN10014","nhs":"9434765914","name_1":"SOPHIA",   "family":"GARCIA",   "dob":"12/11/1984","dob_int":"19841112","sex":"2","gp":"G4455667","practice":"P40014","pc":"W1A 1AA", "addr1":"7 Meadow Way",     "addr2":"Leicester",  "ethnic":"H"},
    {"mrn":"MRN10015","nhs":"9434765915","name_1":"WILLIAM",  "family":"MARTINEZ", "dob":"08/07/1949","dob_int":"19490708","sex":"1","gp":"G5566778","practice":"P40015","pc":"SW1A 2AA","addr1":"52 Forest Road",   "addr2":"Norwich",    "ethnic":"Z"},
    {"mrn":"MRN10016","nhs":"9434765916","name_1":"ISABELLA", "family":"ROBINSON", "dob":"25/04/1991","dob_int":"19910425","sex":"2","gp":"G6677889","practice":"P40016","pc":"E1 6AN", "addr1":"11 Castle Hill",   "addr2":"Exeter",     "ethnic":"A"},
    {"mrn":"MRN10017","nhs":"9434765917","name_1":"HENRY",    "family":"CLARK",    "dob":"01/09/1956","dob_int":"19560901","sex":"1","gp":"G7788990","practice":"P40017","pc":"N1 9GU", "addr1":"29 Windmill Lane", "addr2":"Gloucester", "ethnic":"C"},
    {"mrn":"MRN10018","nhs":"9434765918","name_1":"MIA",      "family":"LEWIS",    "dob":"19/01/1977","dob_int":"19770119","sex":"2","gp":"G8899001","practice":"P40018","pc":"EC4M 5WT","addr1":"3 Harbour Close",  "addr2":"Portsmouth", "ethnic":"B"},
    {"mrn":"MRN10019","nhs":"9434765919","name_1":"CHARLES",  "family":"LEE",      "dob":"14/06/1969","dob_int":"19690614","sex":"1","gp":"G9900112","practice":"P40019","pc":"WC2N 5DU","addr1":"66 Priory Road",   "addr2":"Brighton",   "ethnic":"D"},
    {"mrn":"MRN10020","nhs":"9434765920","name_1":"GRACE",    "family":"WALKER",   "dob":"31/08/1986","dob_int":"19860831","sex":"2","gp":"G0011223","practice":"P40020","pc":"SE1 7PB", "addr1":"14 Orchard Gdns",  "addr2":"Southampton","ethnic":"G"},
]
ACTIVE_PATIENTS = list(PATIENTS)

CONSULTANTS = [f"C{70000+i}" for i in range(10)]
WARDS       = ["3A","3B","4N","ICU","MAU","SAU","HDU","NICU","AMU","CCU"]
SPECIALTIES = ["GEN","CARD","ORTH","SURG","MED","PAED","OBS","PSYCH","OPHTH","ENT"]
DIAGNOSES   = ["I25.1","J18.9","M16.1","K80.2","N18.3","E11.9","F32.1","M79.3","L40.0","Z96.6"]
DIAG_ICD10  = ["I251","J189","M161","K802","N183","E119","F321","M793","L400","Z966"]
PROCEDURES  = ["W371","W381","W391","K444","H011","E411","C711","A111","T241","V544"]
SURNAMES    = ["SMITH","JONES","PATEL","WILLIAMS","BROWN","TAYLOR","AHMED","DAVIS","HARRIS","MARTIN"]


def p(i):
    """Return the patient dict for row index i (0-based, wraps at ROWS)."""
    return ACTIVE_PATIENTS[i % len(ACTIVE_PATIENTS)]


def _nhs_check_digit(base9: str):
    total = 0
    for idx, ch in enumerate(base9):
        total += int(ch) * (10 - idx)
    rem = total % 11
    chk = 11 - rem
    if chk == 11:
        return "0"
    if chk == 10:
        return None
    return str(chk)


def _make_nhs_number(seed_num: int):
    # Build a valid 10-digit NHS number.
    n = seed_num
    while True:
        base9 = "{:09d}".format(n % 1_000_000_000)
        check = _nhs_check_digit(base9)
        if check is not None:
            return base9 + check
        n += 1


def _build_patient_roster(rows):
    roster = list(PATIENTS[: min(rows, len(PATIENTS))])
    # Ensure first seed cohort also uses checksum-valid NHS numbers.
    for idx, rec in enumerate(roster, start=1):
        rec["nhs"] = _make_nhs_number(943476590 + idx)
    if rows <= len(roster):
        return roster

    first_names = [
        "ALICE", "BEN", "CATHERINE", "DANIEL", "EVA", "FRANK", "HANNAH", "IVAN", "JULIA", "KARIM",
        "LARA", "MASON", "NORA", "OWEN", "PAULA", "QUENTIN", "RUBY", "SAM", "TARA", "UMA",
    ]
    families = [
        "ADAMS", "BELL", "COOPER", "DIXON", "EDWARDS", "FOSTER", "GRAHAM", "HUGHES", "IRWIN", "JACKSON",
        "KELLY", "LONG", "MURPHY", "NASH", "ORTIZ", "PRICE", "QUINN", "REED", "STONE", "TURNER",
    ]
    pcs = ["SW1A 2AA", "E1 6AN", "N1 9GU", "EC4M 5WT", "WC2N 5DU", "SE1 7PB", "W1A 1AA"]
    ethnics = ["A", "B", "C", "D", "G", "H", "Z"]

    for idx in range(len(roster) + 1, rows + 1):
        mrn = "MRN{:05d}".format(10000 + idx)
        nhs = _make_nhs_number(943476590 + idx)
        sex = "1" if idx % 2 else "2"
        year = 1945 + (idx % 55)
        month = ((idx - 1) % 12) + 1
        day = ((idx - 1) % 28) + 1
        dob = "{:02d}/{:02d}/{:04d}".format(day, month, year)
        dob_int = "{:04d}{:02d}{:02d}".format(year, month, day)
        fname = first_names[(idx - 1) % len(first_names)]
        fam = families[(idx - 1) % len(families)]
        roster.append(
            {
                "mrn": mrn,
                "nhs": nhs,
                "name_1": fname,
                "family": fam,
                "dob": dob,
                "dob_int": dob_int,
                "sex": sex,
                "gp": "G{:07d}".format(1000000 + idx),
                "practice": "P{:05d}".format(50000 + idx),
                "pc": pcs[(idx - 1) % len(pcs)],
                "addr1": "{} Civic Road".format(10 + idx),
                "addr2": "Town {:02d}".format((idx % 40) + 1),
                "ethnic": ethnics[(idx - 1) % len(ethnics)],
            }
        )
    return roster


def _rand_date(start_yr=2020, end_yr=2024):
    d = date(random.randint(start_yr, end_yr),
             random.randint(1, 12), random.randint(1, 28))
    return d.strftime("%d/%m/%Y")


def _rand_dt_int(start_yr=2020, end_yr=2024):
    """CCYYMMDDHHMM format for source tables."""
    d = date(random.randint(start_yr, end_yr),
             random.randint(1, 12), random.randint(1, 28))
    hh = random.randint(8, 16)
    mm = random.choice([0, 15, 30, 45])
    return d.strftime("%Y%m%d") + "{:02d}{:02d}".format(hh, mm)


def _rand_time():
    return "{:02d}:{}".format(random.randint(8, 16), random.choice(["00","15","30","45"]))


# ────────────────────────────────────────────────────────────────────────────
# TARGET field value generator  (for all 38 LOAD_ tables)
# ────────────────────────────────────────────────────────────────────────────
def _field_value(field, row_idx, table):
    f  = field.lower()
    pt = p(row_idx)
    i  = row_idx + 1            # 1-based record number
    sp = SPECIALTIES[row_idx % 10]
    cn = CONSULTANTS[row_idx % 10]

    # Phantom / PDF artefact fields
    if f in ("must","before","ranges","table","indicates","acters","ged",
             "ge_date","ge_status","ge_typee","ge_toe","ge_methode",
             "ge_specialty","ge_consultant","appointments"):
        return ""

    # Universal columns
    if f == "record_number":            return str(i)
    if f == "system_code":              return "SRC_PAS_V83"
    if f == "external_system_id":       return pt["mrn"]

    # PMI - patient identity
    if f in ("main_crn_type",):         return "PAS"
    if f == "main_crn":                 return pt["mrn"]
    if f == "nhs_number":               return pt["nhs"]
    if f == "nhs_number_status":        return "01"
    if f == "sex":                      return pt["sex"]
    if f == "title":                    return "MR" if pt["sex"] == "1" else "MRS"
    if f == "pat_name_1":               return pt["name_1"]
    if f == "pat_name_family":          return pt["family"]
    if f in ("pat_name_2","pat_name_3"): return ""
    if f == "maiden_name":              return pt["family"] if pt["sex"] == "2" else ""
    if f == "date_of_birth":            return pt["dob"]
    if "place_born" in f:               return random.choice(["LONDON","BIRMINGHAM","ABROAD"])
    if "ethnic" in f:                   return pt["ethnic"]
    if "marital" in f:                  return random.choice(["S","M","D","W"])
    if "occupation" in f:               return random.choice(["10","20","30","40"])
    if "religion" in f:                 return random.choice(["C","M","J","H","N"])
    if "preferred_language" in f:       return "EN"
    if f == "pat_address_1":            return pt["addr1"]
    if f == "pat_address_2":            return pt["addr2"]
    if f in ("pat_address_3","pat_address_4","pat_address_5"): return ""
    if "post_code" in f or "postcode" in f: return pt["pc"]
    if "telephone_no" in f or f == "phone_no":
        return "020 7{} {}".format(700+row_idx, 3000+row_idx)
    if "email" in f and "address" in f:
        return "{}.{}@qvh.nhs.uk".format(pt["name_1"].lower(), pt["family"].lower())
    if "nationality" in f:              return "GBR"
    if "blood_group" in f:              return random.choice(["A+","B+","O+","AB+","O-"])
    if "nok_name" in f:                 return "MARY {}".format(pt["family"])
    if "nok_title" in f:                return "MRS"
    if "nok_relationship" in f:         return random.choice(["SPOUSE","CHILD","PARENT","SIBLING"])
    if "nok_address" in f:              return pt["addr1"]
    if "nok_post_code" in f:            return pt["pc"]
    if "nok_telephone" in f or "nok_phone" in f:
        return "07{}{}".format(700+row_idx, 100000+row_idx)
    if "nok_comments" in f:             return "Next of kin informed"
    if f == "comments":                 return "No clinical issues noted"
    if "gp_national_code" in f:        return pt["gp"]
    if "gdp_national_code" in f:       return pt["gp"]
    if "practice_national_code" in f:  return pt["practice"]
    if "practice_post_code" in f:      return pt["pc"]
    if "date_of_death" in f or "of_death" in f: return ""
    if "where_died" in f or "cause_of_death" in f: return ""
    if "death_" in f:                  return ""
    if "extra_info" in f:              return ""
    if "note_" in f:                   return ""
    if "where_heard" in f:             return ""
    if "pat_lives_alone" in f:         return random.choice(["Y","N"])
    if "pat_permission" in f:          return "Y"
    if "pat_address_from" in f:        return _rand_date(2000,2018)
    if "date_registered" in f:         return _rand_date(1980,2010)
    if "entered_country" in f:         return ""

    # PMI sub-tables
    if "loadpmi_record_number" in f:   return str(i)
    if "additional_id_type" in f:      return "PASSPORT"
    if f == "additional_id":           return "PP{}".format(900000+i)
    if f == "alias_type":              return "MAIDEN"
    if "alias_name" in f:              return pt["family"]
    if f == "volume":                  return str(i)
    if f == "address_type":            return "H"
    if f == "address_1":               return pt["addr1"]
    if f == "address_2":               return pt["addr2"]
    if f in ("address_3","address_4","address_5"): return ""
    if f == "contact_type":            return "NOK"
    if "parental_responsibility" in f: return "N"
    if "allergy_code" in f:            return random.choice(["PENICILLIN","ASPIRIN","LATEX","NONE"])
    if "allergy_comment" in f:         return "Documented in clinical notes"
    if "warning_code" in f:            return random.choice(["AGGR","VIP","LATEX","MRSA"])
    if "warning_comment" in f:         return "See clinical alert panel"
    if "country_code" in f:            return "GBR"
    if "id_type" in f:                 return "MRN"
    if "id_number" in f:               return pt["mrn"]
    if "applies_start" in f:           return _rand_date(2000,2018)
    if "applies_end" in f:             return "31/12/9999"
    if f == "location_type":           return "LIBRARY"
    if f == "location_code":           return "LOC{:02d}".format(i)
    if f == "user_code":               return "USR{:03d}".format(i)
    if f == "description":             return "Case note {} - {}".format(i, pt["family"])
    if f == "active_flag":             return "Y"
    if f == "short_note":              return "On shelf in medical records"
    if f == "start_date":              return _rand_date(2010,2020)
    if f == "end_date":                return "31/12/9999"
    if "hospital_code" in f:           return "RVK01"
    if "site_code" in f:               return "RVK01"

    # RTT Pathways
    if "loadrttpwy_record_number" in f: return str(i)
    if f == "pathway_id":              return "RTT{}".format(20000+i)
    if f == "ubrn":                    return "0{}".format(90000000000+i)
    if "pathway_start_date" in f:      return _rand_date(2022,2023)
    if "pathway_end_date" in f:        return _rand_date(2023,2024)
    if "pathway_end_event" in f:       return random.choice(["TREAT","DISCHARGE","DNA"])
    if "pathway_specialty" in f:       return sp
    if "pathway_status" in f:          return random.choice(["ACTIVE","CLOSED","SUSPENDED"])
    if "pathway_type" in f:            return "RTT"
    if "pathway_coded" in f:           return ""
    if "first_seen" in f:              return _rand_date(2022,2023)
    if "override_wait" in f:           return ""

    # Referrals
    if "loadref_record_number" in f:   return str(i)
    if "ref_new_followup" in f:        return random.choice(["N","F"])
    if "ref_received_date" in f:       return _rand_date(2022,2023)
    if "ref_date" in f:                return _rand_date(2022,2023)
    if "ref_source" in f:              return random.choice(["GP","SELF","CONS","AE"])
    if "ref_gp_code" in f:             return pt["gp"]
    if "ref_practice_code" in f:       return pt["practice"]
    if "ref_practice_postcode" in f:   return pt["pc"]
    if "ref_urgency" in f:             return random.choice(["ROUTINE","URGENT","2WW"])
    if "ref_type" in f:                return random.choice(["ELEC","EMER","URGENT"])
    if "ref_reason" in f:              return random.choice(["01","02","03","04"])
    if "ref_specialty" in f:           return sp
    if "ref_team" in f:                return sp
    if "ref_consultant" in f:          return cn
    if "ref_outcome" in f:             return random.choice(["TREAT","DISCHARGE","ONWARD"])
    if "ref_discharge_date" in f:      return _rand_date(2023,2024)
    if "encounter_type" in f:          return random.choice(["1","2"])
    if "patient_category" in f:        return random.choice(["OP","IP","DC","CMTY"])

    # RTT Periods
    if "loadrttprd_record_number" in f: return str(i)
    if "clock_start" in f:             return _rand_date(2022,2023)
    if "clock_stop" in f:              return _rand_date(2023,2024)
    if "start_event_reason" in f:      return "REFERRAL"
    if "stop_event_reason" in f:       return "TREATED"
    if "breach_reason_code" in f:      return ""
    if "breach_reason_text" in f:      return ""
    if "referral_as_start" in f:       return "Y"
    if "rtt_status" in f:              return random.choice(["P","S","R"])

    # RTT Events
    if "event_date" in f:              return _rand_date(2022,2024)
    if "event_action_code" in f:       return "STATUS_CHANGE"
    if "event_reason_code" in f:       return "01"
    if "event_text" in f:              return "RTT status updated by clinician"

    # OPD Waitlist
    if "loadowl_record_number" in f:   return str(i)
    if "rttpwy_recno" in f:            return str(i)
    if "loadrttprd_action" in f:       return "ADD"
    if "rttevent_recno" in f:          return str(i)
    if "list_code" in f:               return "WL{:03d}".format(i)
    if "list_name" in f:               return "Clinic {}".format(sp)
    if "new_followup_flag" in f:       return random.choice(["N","F"])
    if "short_notice_flag" in f:       return "N"
    if "status" in f:                  return random.choice(["A","S","R","W"])
    if "target_date" in f:             return _rand_date(2023,2024)
    if f == "consultant":              return cn
    if "outcome" in f:                 return random.choice(["TREAT","DISCHARGE","FUP"])
    if "removed" in f or "date_removed" in f: return ""
    if "wl_comment" in f:              return "Patient contacted by telephone"
    if "ios_usercode" in f:            return "USR{:03d}".format(i)
    if "transport_required" in f:      return "N"
    if "deferral_start" in f:          return _rand_date(2022,2023)
    if "deferral_end" in f:            return _rand_date(2023,2024)
    if "deferral_reason" in f:         return random.choice(["PATIENT","HOSPITAL","MEDICAL"])
    if "deferral_comment" in f:        return "Rescheduled at patient request"

    # OPD Appointments
    if "appt_date" in f:               return _rand_date(2023,2024)
    if "booked_date" in f or f == "booked": return _rand_date(2022,2023)
    if "booking_type" in f:            return random.choice(["ELEC","URGENT","CHOOSE"])
    if "clinic_code" in f:             return "CLI{:03d}".format(100+i)
    if "appt_type" in f:               return random.choice(["NEW","FU","POST"])
    if "appt_team" in f:               return sp
    if "consultant_in_charge" in f:    return cn
    if "consultant_taking" in f:       return cn
    if "walkin_flag" in f:             return "N"
    if "time_arrived" in f:            return _rand_time()
    if "time_seen" in f:               return _rand_time()
    if "time_complete" in f or "time_completed" in f: return _rand_time()
    if "appt_comment" in f or "appointment_comment" in f:
        return "Patient attended punctually. Reviewed by clinician."
    if "cancelled_date" in f:          return ""
    if "cab_ubrn" in f:                return ""
    if "cab_service" in f:             return ""
    if "cab_usrn" in f:                return ""
    if "service_group" in f:           return random.choice(["CMHT","CRISIS","AOT","EIS"])
    if "service_type" in f:            return "CMTY"

    # Coding (OPD + ADT)
    if "load_opd_record_number" in f:  return str(i)
    if "diagnosis_division" in f:      return "1"
    if "note_type" in f:               return "D"
    if f == "diagnosis":               return DIAGNOSES[row_idx % 10]
    if "diagnosis_note" in f:          return "Coded by clinician post-encounter"
    if "diagnosed_by" in f:            return cn
    if "diagnosis_date" in f:          return _rand_date(2022,2024)
    if "procedure_scheme" in f:        return "OPCS4"
    if "diagnosis_scheme" in f:        return "ICD10"
    if "primary_procedure_code" in f:  return PROCEDURES[row_idx % 10]
    if "primary_procedure_desc" in f:  return "Primary surgical procedure"
    if "primary_diagnosis_code" in f:  return DIAGNOSES[row_idx % 10]
    if "primary_diagnosis_desc" in f:  return "Primary diagnosis confirmed"
    if "procedure_" in f and "_code" in f: return ""
    if "procedure_" in f and "_desc" in f: return ""
    if "diagnosis_" in f and "_code" in f: return ""
    if "diagnosis_" in f and "_desc" in f: return ""

    # IWL Profiles
    if "profile_code" in f:            return "PRF{:02d}".format(i)
    if "profile_name" in f:            return "{} Elective Profile".format(sp)

    # IWL
    if "loadiwl_record_number" in f:   return str(i)
    if "waitlist_date" in f:           return _rand_date(2022,2023)
    if "urgency" in f:                 return random.choice(["E","U","R"])
    if "waitlist_type" in f:           return random.choice(["E","D","DC"])
    if "waitlist_profile" in f:        return "PRF{:02d}".format(i)
    if f == "specialty":               return sp
    if "intended_management" in f or "actual_management" in f:
        return random.choice(["E","D","DC"])
    if "provisional_diagnosis" in f:   return "Joint pain - awaiting pre-op assessment"
    if "provisional_procedure" in f:   return "Total hip replacement"
    if "intended_procedure_code" in f: return PROCEDURES[row_idx % 10]
    if "est_theatre_time" in f:        return str(random.randint(60,180))
    if "admission_duration" in f:      return str(random.randint(1,7))
    if "last_review_date" in f:        return _rand_date(2023,2024)
    if "last_review_response" in f:    return "Y"
    if "wl_outcome" in f:              return random.choice(["ADMIT","REMOVE","DEFER"])
    if "wl_entry_comment" in f:        return "Reviewed by WL coordinator"
    if "offer_date" in f:              return _rand_date(2023,2024)
    if "agreed_date" in f:             return _rand_date(2023,2024)
    if "agreed_flag" in f:             return "Y"
    if "preassessment_date" in f:      return _rand_date(2023,2024)
    if "tci_date" in f:                return _rand_date(2023,2024)
    if "operation_date" in f:          return _rand_date(2023,2024)
    if "estimated_discharge_date" in f: return _rand_date(2023,2024)
    if "list_no" in f:                 return str(i)
    if "consultant_code" in f:         return cn
    if "treatment_type" in f:          return random.choice(["P","D"])
    if "admit_type" in f:              return random.choice(["E","D"])
    if "max_wait_months" in f:         return "18"
    if "avg_length_stay" in f:         return "3"
    if "admit_duration_hours" in f:    return "2"
    if "operation_duration_mins" in f: return "90"

    # ADT Admissions
    if "adt_adm_record_number" in f:   return str(i)
    if "admit_date" in f:              return _rand_date(2022,2023)
    if "discharge_date" in f:          return _rand_date(2023,2024)
    if "ward" in f:                    return WARDS[row_idx % 10]
    if "admit_from" in f:              return random.choice(["19","51","52","99"])
    if "admitted_by" in f:             return cn
    if "wl_date" in f:                 return _rand_date(2021,2022)
    if "tci_outcome" in f:             return random.choice(["01","02","03"])
    if "discharged_by" in f:           return cn
    if "discharge_method" in f:        return random.choice(["1","2","3","4"])
    if "admission_outcome" in f:       return random.choice(["01","02","03"])
    if "source_of_admission" in f:     return random.choice(["19","51","52","99"])
    if "method_of_admission" in f:     return random.choice(["11","12","21","22"])
    if "method_of_discharge" in f:     return random.choice(["1","2","3","4"])
    if "destination_on_discharge" in f: return random.choice(["19","51","52","99"])

    # ADT Episodes
    if "adt_eps_record_number" in f:   return str(i)
    if "episode_order" in f:           return "1"
    if "episode_start" in f:           return _rand_date(2022,2023)
    if "episode_end" in f:             return _rand_date(2023,2024)
    if "duration_of_episode" in f:     return str(random.randint(1,30))
    if "age_at_start_of_episode" in f: return str(random.randint(18,90))

    # ADT Ward Stays
    if "bed_sex" in f:                 return "M" if pt["sex"] == "1" else "F"
    if "bed_location" in f:            return "BED{:02d}".format(random.randint(1,30))
    if "is_home_stay" in f:            return "N"
    if "is_awol" in f:                 return "N"
    if "leave_location_code" in f:     return ""
    if "transfer_reason" in f:         return random.choice(["SPECIALTY","BED","CLINICAL"])
    if "team" in f:                    return sp
    if "hrg" in f:                     return "AA{}A".format(random.randint(10,99))

    # Mental Health
    if "mh_dm_record_number" in f:     return str(i)
    if "mh_cm_record_number" in f:     return str(i)
    if "legal_status" in f:            return random.choice(["02","03","07","17"])
    if "mental_category" in f:         return "MENTAL ILLNESS"
    if "caseholder" in f:              return cn
    if "section_review_date" in f:     return _rand_date(2023,2025)
    if "consent_reminder_date" in f:   return _rand_date(2023,2025)
    if "consent_due_date" in f:        return _rand_date(2023,2025)
    if "cpa_type" in f:                return random.choice(["STANDARD","ENHANCED"])
    if "key_worker" in f:              return cn
    if "key_worker_staff_id" in f:     return "S{:04d}".format(i)
    if "care_coordinator" in f:        return cn
    if "next_review_date" in f:        return _rand_date(2024,2025)
    if "cpa_start" in f:               return _rand_date(2020,2023)
    if "cpa_end" in f:                 return _rand_date(2023,2024)
    if "cpa_notes" in f:               return "CPA review completed. Care plan updated."
    if "detention_start" in f:         return _rand_date(2020,2023)
    if "detention_end" in f:           return _rand_date(2023,2024)
    if "detention_location" in f:      return "PICU Ward 5"
    if "detention_notes" in f:         return "Section 3 MHA 1983 - see legal file"
    if "institution" in f:             return "QUEEN VICTORIA HOSPITAL"
    if "transfer_date" in f:           return _rand_date(2022,2023)
    if "transfer_from" in f:           return "QVH"
    if "transfer_to" in f:             return "QVH"
    if "section_expiry" in f:          return _rand_date(2024,2025)

    # Staff / Users / Sites
    if f == "user_name":               return "USER{:03d}".format(i)
    if f == "first_name":              return pt["name_1"]
    if f == "middle_name":             return ""
    if f == "family_name":             return pt["family"]
    if f == "job_id":                  return str(random.randint(1,50))
    if f == "password":                return "HASHED_PLACEHOLDER"
    if "psswd_life_months" in f:       return "12"
    if "psswd_expiry_date" in f:       return "31/12/2026"
    if "language_id" in f:            return "1"
    if f == "staff_id":                return "S{:04d}".format(i)
    if "default_parts_entity" in f:    return "QVH"
    if "default_tools_entity" in f:    return "QVH"
    if "default_labour_entity" in f:   return "QVH"
    if "employee_flag" in f:           return "Y"
    if "default_stock_entity" in f:    return "QVH"
    if "staff_security_level" in f:    return "STANDARD"
    if "extension_no" in f:            return str(1000+i)
    if "default_login_entity" in f:    return "QVH"
    if "eoasis_user" in f:             return "Y"
    if "allow_logon" in f:             return "Y"
    if "default_executable" in f:      return ""
    if "type_of_user" in f:            return random.choice(["CLINICAL","ADMIN","MANAGER"])
    if "login_from_date" in f:         return "01/04/2024"
    if "login_to_date" in f:           return "31/12/9999"
    if "email_address" in f:
        return "{}.{}@qvh.nhs.uk".format(pt["name_1"].lower(), pt["family"].lower())
    if "can_log_support_calls" in f:   return "N"
    if "ask_review_warnings" in f:     return "Y"
    if "from_time" in f:               return "800"
    if "to_time" in f:                 return "1800"
    if "mon_allowed" in f:             return "Y"
    if "tue_allowed" in f:             return "Y"
    if "wed_allowed" in f:             return "Y"
    if "thu_allowed" in f:             return "Y"
    if "fri_allowed" in f:             return "Y"
    if "sat_allowed" in f:             return "N"
    if "sun_allowed" in f:             return "N"
    if "default_team" in f:            return sp
    if "client_user" in f:             return "CLI{:03d}".format(i)
    if "provider_prefix" in f:         return "RVK"
    if f == "site_code":               return "RVK{:02d}".format(i)
    if "site_description" in f:        return "Queen Victoria Hospital - East Grinstead"
    if "site_link_applies_start" in f: return "01/04/2010"
    if "site_link_applies_end" in f:   return "31/12/9999"
    if "phone_1" in f or "phone_2" in f: return "01342 414141"

    # Archive tables
    if f == "crn":                     return pt["mrn"]
    if "district" in f:                return "QVH"
    if "pct_code" in f:                return "09H"
    if "contract_number" in f:         return "CTR{:05d}".format(30000+i)
    if "purchaser_ref" in f:           return str(5000+i)
    if "provider_code" in f:           return "RVK"
    if "purchaser_code" in f:          return "09H"
    if "gp_registration_code" in f:    return pt["gp"]
    if "gp_name" in f:                 return "DR {}".format(SURNAMES[row_idx % 10])
    if "gp_fundholder_code" in f:      return pt["gp"]
    if "gp_practice_code" in f:        return pt["practice"]
    if "practice_name" in f:           return "{} Medical Practice".format(SURNAMES[row_idx % 10])
    if "referring_consultant_gmc" in f: return "GMC{}".format(7000000+i)
    if "referring_consultant_name" in f: return "DR {}".format(SURNAMES[row_idx % 10])
    if "referral_request_date" in f:   return _rand_date(2022,2023)
    if "referral_reason" in f:         return "Chest pain investigation"
    if "referral_discharge_date" in f: return _rand_date(2023,2024)
    if "first_attendance" in f:        return _rand_date(2022,2023)
    if "clinic_name" in f:             return "{} Clinic {}".format(sp, i)
    if "consultant_team" in f:         return sp
    if "consultant_gmc" in f:          return "GMC{}".format(7000000+i)
    if "consultant_name" in f:         return "DR {}".format(SURNAMES[row_idx % 10])
    if "transport" in f:               return "N"
    if "appointment_priority" in f:    return "ROUTINE"
    if "appointment_purpose" in f:     return "ASSESSMENT"
    if "appointment_status" in f:      return "ATT"
    if "appointment_date" in f:        return _rand_date(2023,2024)
    if "appointment_time" in f:        return "{:02d}:00".format(random.randint(8,16))
    if "forced_booking_flag" in f:     return "N"
    if "cancellation_reason" in f:     return ""
    if "cancelled_by" in f:            return ""
    if "waiting_list_name" in f:       return "{} Elective WL".format(sp)
    if "decided_to_admit_date" in f:   return _rand_date(2021,2022)
    if "inpatient_wait_days" in f:     return str(random.randint(10,180))
    if "admitting_specialty" in f:     return sp
    if "admitting_consultant_gmc" in f: return "GMC{}".format(7000000+i)
    if "admitting_consultant_name" in f: return "DR {}".format(SURNAMES[row_idx % 10])
    if "discharging_specialty" in f:   return sp
    if "discharging_consultant_gmc" in f: return "GMC{}".format(7000001+i)
    if "discharging_consultant_name" in f:
        return "DR {}".format(SURNAMES[(row_idx+1) % 10])

    # Catch-all
    return ""


# ────────────────────────────────────────────────────────────────────────────
# SOURCE field value generator  (shared by all 13 source tables)
# ────────────────────────────────────────────────────────────────────────────
def _src(field, row_idx):
    """Map a source catalog field name (lowercased) to a realistic mock value."""
    f  = field.lower()
    pt = p(row_idx)
    i  = row_idx + 1
    sp = SPECIALTIES[row_idx % 10]
    cn = CONSULTANTS[row_idx % 10]

    # Patient identity
    if "internalpatientnumber" in f:   return pt["mrn"]
    if "episodenumber" in f:           return str(20000+i)
    if "nhsnumber" in f:               return pt["nhs"]
    if f in ("forenames",):            return pt["name_1"]
    if f in ("surname",):              return pt["family"]
    if f == "dob" or f == "dateofbirth": return pt["dob"]
    if "internaldateofbirth" in f or (f == "dobint"): return pt["dob_int"]
    if f == "sex":                     return pt["sex"]
    if f == "currentgender":           return pt["sex"]
    if f == "currentgenderdesc":       return "Male" if pt["sex"] == "1" else "Female"
    if f == "currentgenderint":        return pt["sex"]
    if "districtnumber" in f:          return "DN{:05d}".format(10000+i)
    if "casenotenum" in f or "casenotenumber" in f or "casenoteno" in f:
        return "CN{:05d}".format(20000+i)

    # Address
    if "extaddressaddline1" in f or "extaddressline1" in f: return pt["addr1"]
    if "extaddressline2" in f:         return pt["addr2"]
    if "extaddressline" in f:          return ""
    if "postcode" in f or "pseudopostcode" in f: return pt["pc"]
    if "homephone" in f:               return "020 7{} {}".format(700+row_idx, 3000+row_idx)

    # GP / practice
    if f in ("gpcode","epigp","reggpcode","gp_code"):  return pt["gp"]
    if "gpcode" in f and "gp_code" not in f:           return pt["gp"]
    if "epigpcode" in f or "epigppracticecode" in f:
        return pt["gp"] if "practice" not in f else pt["practice"]
    if "practicecode" in f:            return pt["practice"]
    if "gdpcode" in f:                 return pt["gp"]
    if "hacode" in f:                  return "09H"

    # Ethnicity / demographics
    if "ethnictype" in f:              return pt["ethnic"]
    if "marital" in f:                 return random.choice(["S","M","D","W"])
    if "religion" in f:                return random.choice(["C","M","J","H","N"])
    if "bloodgroup" in f:              return random.choice(["A+","B+","O+","AB+"])
    if "allergies" in f:               return random.choice(["PENICILLIN","NONE","ASPIRIN"])
    if "birthname" in f:               return pt["family"]
    if "countryofbirth" in f:          return "GBR"

    # Clinical staff
    if f == "consultant":              return cn
    if "consultant" in f and "ref" not in f and "joint" not in f: return cn
    if "refconsultant" in f:           return cn
    if "jointcons" in f:               return CONSULTANTS[(row_idx+1) % 10]
    if "specialty" in f:               return sp
    if "jointspec" in f:               return SPECIALTIES[(row_idx+1) % 10]

    # Admission / discharge dates
    if "admissiondate" in f and "int" not in f:  return _rand_date(2022,2023)
    if "dischargedate" in f and "int" not in f:  return _rand_date(2023,2024)
    if "admissiontime" in f:           return "09:00"
    if "dischtime" in f:               return "14:00"
    if "admward" in f:                 return WARDS[row_idx % 10]
    if "dischward" in f:               return WARDS[row_idx % 10]
    if "bed" in f:                     return "BED{:02d}".format(row_idx+1)
    if "room" in f:                    return "RM{:02d}".format(row_idx+1)
    if "methodofadmission" in f:       return random.choice(["11","12","21","22"])
    if "methodofdischarge" in f:       return random.choice(["1","2","3","4"])
    if "sourceofadm" in f:             return random.choice(["19","51","52","99"])
    if "destinationondischarge" in f:  return random.choice(["19","51","52","99"])
    if "intdmgmt" in f:                return random.choice(["E","D","DC"])
    if "admreason" in f:               return "Elective admission for planned surgery"
    if "operation" in f and "date" not in f: return "Total hip replacement"
    if "epscurractysts" in f:          return "COMPLETE"
    if "hospcode" in f or "hospcda" in f or "hospcdend" in f: return "RVK"
    if "category" in f:                return random.choice(["01","02","03"])
    if "benefitcode" in f:             return "N"
    if "outlier" in f:                 return "N"
    if "lodger" in f:                  return "N"
    if "livestillbirth" in f:          return "N"
    if "theatretime" in f:             return str(random.randint(60,180))
    if "expectedlos" in f:             return str(random.randint(1,10))
    if "expdate" in f:                 return _rand_date(2023,2024)
    if "dateonwl" in f or "wldateccyy" in f: return _rand_date(2021,2022)
    if "accidentcode" in f:            return ""
    if f == "referral":                return "N"
    if "reasonforreferral" in f:       return "02"
    if "datebr409sent" in f:           return ""
    if "br409required" in f:           return "N"
    if "decisiontorefer" in f:         return _rand_date(2022,2023)
    if "transfrom" in f:               return ""
    if "transto" in f:                 return ""

    # Datetime integer fields (CCYYMMDDHHMM)
    if f.endswith("int") and ("date" in f or "dtime" in f or "dtm" in f or "dttime" in f):
        return _rand_dt_int(2022,2024)
    if "ipadmdtimeint" in f or "ipdschdtimeint" in f: return _rand_dt_int(2022,2024)
    if "opdischargedtimeint" in f:     return _rand_dt_int(2023,2024)

    # RTT
    if "rttperiodstatus" in f:         return random.choice(["P","S","R"])
    if "breachdate" in f:              return ""
    if "breachreasoncode" in f:        return ""
    if "breachreasondesc" in f:        return ""

    # HRG
    if "hrgcode" in f or f == "hrg":   return "AA{}A".format(random.randint(10,99))
    if "hrgoutlierflag" in f:          return "N"

    # OPD / HWSAPP appointment fields
    if "apptdate" in f:                return _rand_date(2023,2024)
    if "appttime" in f:                return _rand_time()
    if "apptbookeddate" in f:          return _rand_date(2022,2023)
    if "apptbookedtime" in f:          return _rand_time()
    if "apptcancdate" in f:            return ""
    if "apptcanctime" in f or "apptcancdtime" in f: return ""
    if "apptendtime" in f:             return _rand_time()
    if "apptcategory" in f:            return random.choice(["NEW","FOL"])
    if "apptclass" in f:               return random.choice(["1","2"])
    if "appttype" in f:                return random.choice(["NEW","FU","POST"])
    if "apptstatus" in f:              return random.choice(["ATT","WLK","NATT","SATT"])
    if "apptcomment" in f:             return "Patient attended. Reviewed."
    if "apptpurchaser" in f:           return "09H"
    if "apptpurchref" in f:            return "PR{:04d}".format(5000+i)
    if "apptconractid" in f:           return "CTR{:04d}".format(3000+i)
    if "apptprimaryprocedurecode" in f: return PROCEDURES[row_idx % 10]
    if "bookingtype" in f:             return random.choice(["ELEC","URGENT","CHOOSE"])
    if "cancelby" in f:                return ""
    if "cancelcomment" in f:           return ""
    if "cliniccode" in f:              return "CLI{:03d}".format(100+i)
    if "clinicconsultant" in f:        return cn
    if "clinicspecialty" in f or "clinicianspecialty" in f: return sp
    if "cliniciansubspec" in f:        return ""
    if "disposal" in f:                return random.choice(["TREAT","DISCHARGE","FUP","DNA"])
    if "dischdate" in f:               return _rand_date(2023,2024)
    if "transport" in f:               return "N"
    if "reasonforcanc" in f:           return ""
    if "referraldate" in f:            return _rand_date(2022,2023)
    if "referraltime" in f:            return _rand_time()
    if "refby" in f:                   return random.choice(["GP","SELF","CONS","AE"])
    if "refconsultant" in f:           return cn
    if "refspecialty" in f:            return sp
    if "reasonforref" in f:            return random.choice(["01","02","03","04"])
    if "prioritytype" in f or "refpriority" in f: return random.choice(["1","2","3"])
    if "attpridiagcode" in f or "refprimarydiagnosiscode" in f: return DIAG_ICD10[row_idx % 10]
    if "attsubdiagcode" in f or "refsubsiddiag" in f: return ""
    if "osvstatus" in f:               return "N"
    if "bookfromwl" in f:              return "WL{:03d}".format(i)
    if "cabservicecode" in f or "ebooking" in f: return ""
    if "ptcategory" in f or "patcategory" in f: return random.choice(["OP","IP","DC"])
    if "ptchoice" in f:                return "YES"
    if "ptvertical" in f:              return "1"
    if "referralpurchaser" in f:       return "09H"
    if "offeraccepted" in f:           return "YES"
    if "a2nddateoffered" in f:         return ""
    if "reasonableoffer" in f:         return "YES"
    if "interpreter" in f and "language" not in f: return "N"
    if "interpreterlanguage" in f:     return "EN"
    if "progofcare" in f and "desc" not in f: return "1"
    if "progofcaredesc" in f:          return "Outpatient"
    if "primaryprocgroup" in f:        return "OPCS4"
    if "readprimary" in f:             return ""
    if f.startswith("sgreasonforref"): return ""
    if "erod" in f and "int" not in f: return _rand_date(2023,2024)
    if "erod" in f and "int" in f:     return _rand_dt_int(2023,2024)
    if "waitingguarantee" in f:        return "N"
    if "rescode" in f or "userid" in f: return "USR{:03d}".format(i)
    if "referralcontractid" in f:      return "CTR{:04d}".format(3000+i)

    # FCE / episode coding
    if "fcestartdate" in f:            return _rand_date(2022,2023)
    if "fceenddate" in f:              return _rand_date(2023,2024)
    if "fcestarttime" in f:            return "09:00"
    if "fceendtime" in f:              return "14:00"
    if "fcesequenceno" in f:           return str(row_idx+1)
    if "ageatstart" in f:              return str(random.randint(18,90))
    if "kornerep" in f and "diag" in f: return DIAG_ICD10[row_idx % 10]
    if "kornerep" in f and "proc" in f: return PROCEDURES[row_idx % 10]
    if "kornerep" in f and "date" in f: return _rand_date(2022,2023)
    if "subsid" in f:                  return ""
    if "sourceof" in f:                return random.choice(["19","51","52","99"])
    if "destina" in f:                 return random.choice(["19","51","52","99"])
    if "providercode" in f:            return "RVK"
    if "purchasercode" in f:           return "09H"
    if "wardcda" in f or "wardcdadmit" in f: return WARDS[row_idx % 10]
    if "wardcdend" in f:               return WARDS[row_idx % 10]
    if "daysonwl" in f:                return str(random.randint(10,365))
    if "dateonlist" in f:              return _rand_date(2021,2022)
    if "los" in f:                     return str(random.randint(1,30))

    # WL fields
    if "urgency" in f:                 return random.choice(["E","U","R"])
    if "lastreviewdate" in f:          return _rand_date(2023,2024)
    if "wardprocedure" in f:           return "Total hip replacement"
    if "diagnosis" in f and "code" not in f and len(f) < 12:
        return "Hip osteoarthritis"
    if "procedurecode" in f:           return PROCEDURES[row_idx % 10]
    if "wlstatus" in f:                return random.choice(["A","S","R"])
    if "wltype" in f:                  return random.choice(["E","D","DC"])
    if "removaldate" in f:             return ""
    if "wlcomment" in f:               return "Awaiting pre-op assessment"

    # TCI / Deferral
    if "activitytype" in f:            return random.choice(["TCI","DEFER","REMOVE"])
    if "deferral" in f and "start" in f: return _rand_date(2022,2023)
    if "deferral" in f and "end" in f: return _rand_date(2023,2024)
    if "deferral" in f and "reason" in f: return random.choice(["PATIENT","HOSPITAL","MEDICAL"])
    if "deferral" in f and "comment" in f: return "Patient requested reschedule"
    if "operationtext" in f:           return "Hip replacement - left"
    if "admissionreasoncomment" in f:  return "Elective admission as planned"
    if "offerdate" in f:               return _rand_date(2023,2024)
    if "agreeddate" in f:              return _rand_date(2023,2024)
    if "agreedflag" in f:              return "Y"
    if "preassessmentdate" in f:       return _rand_date(2023,2024)
    if "tcidate" in f:                 return _rand_date(2023,2024)
    if "operationdate" in f:           return _rand_date(2023,2024)
    if "estimateddischargedate" in f:  return _rand_date(2023,2024)
    if "tcistatus" in f:               return random.choice(["A","C","D"])

    # Community / MH referral
    if "referralpriority" in f:        return random.choice(["ROUTINE","URGENT","EMERGENCY"])
    if "source" in f:                  return random.choice(["GP","SELF","AE","CONS"])
    if "leadclinician" in f:           return cn
    if "servgroup" in f:               return random.choice(["CMHT","CRISIS","AOT","EIS"])
    if "dischargereason" in f:         return random.choice(["01","02","03"])
    if "refdttmint" in f or "refdtimint" in f: return _rand_dt_int(2022,2023)
    if "primdiag" in f and "severity" not in f: return DIAG_ICD10[row_idx % 10]
    if "primDiagSeverity" in f.lower() or "primDiagseverity" in f.lower():
        return random.choice(["MILD","MOD","SEVERE"])
    if f == "type":                    return "CMTY"
    if f == "status":                  return "SG"
    if f == "statusint":               return "1"
    if "clinicalcategory" in f:        return random.choice(["MH","CMTY","LD"])
    if "diagcomment" in f:             return "Assessment completed. Care plan agreed."
    if "referrerid" in f:              return pt["gp"]
    if "referrername" in f:            return "DR {}".format(SURNAMES[row_idx % 10])
    if "referrerspecialty" in f:       return "GP"
    if "referrertype" in f:            return "GP"
    if f == "priority":                return random.choice(["ROUTINE","URGENT"])

    # SMR / MH episode
    if "legalstatus" in f and "desc" not in f: return random.choice(["02","03","07","17","01"])
    if "legalstatusdesc" in f:         return "Informal"
    if "mentalcategory" in f:          return "MENTAL ILLNESS"
    if "caseholder" in f:              return cn
    if "cpatype" in f:                 return random.choice(["STANDARD","ENHANCED"])
    if "nextreviewdate" in f:          return _rand_date(2024,2025)
    if "institution" in f:             return "QUEEN VICTORIA HOSPITAL"
    if "detentionlocation" in f:       return "PICU Ward 5"
    if "admissionfrom" in f:           return random.choice(["COURT","HOME","AE"])
    if "sectionreviewdate" in f:       return _rand_date(2023,2025)
    if "consentduedate" in f:          return _rand_date(2023,2025)
    if "keyworker" in f:               return cn
    if "carecoordinator" in f:         return CONSULTANTS[(row_idx+1) % 10]

    # Address corrections
    if "seqno" in f:                   return str(row_idx+1)
    if "transactdate" in f:            return _rand_date(2022,2023)
    if "transactuserid" in f:          return "USR{:03d}".format(i)
    if "transacttype" in f:            return "AC"
    if "newaddline1" in f:             return pt["addr1"]
    if "newaddline2" in f:             return pt["addr2"]
    if "newaddline" in f:              return ""
    if "newpostcode" in f:             return pt["pc"]
    if "newpseudo" in f:               return ""
    if "oldaddline1" in f:             return "{} Old Road".format(5+i)
    if "oldaddline2" in f:             return "London"
    if "oldaddline" in f:              return ""
    if "oldpostcode" in f:             return "SW1A 1AA"
    if "oldpseudo" in f:               return ""
    if "pmipatientaddressnew" in f and "from" in f: return "202201010000"
    if "pmipatientaddressnew" in f and "to" in f:   return "999912312359"
    if "pmipatientaddressold" in f and "from" in f: return "201001010000"
    if "pmipatientaddressold" in f and "to" in f:   return "202112312359"

    # NHS staff
    if "nhsemployee" in f and "role" not in f and "org" not in f: return "N"
    if "nhsemployeerole" in f:         return ""
    if "nhsemployerorg" in f:          return ""
    if "contoinfemployer" in f:        return "N"

    # Misc
    if "generalcomments" in f:         return "No additional comments"
    if "comments" in f:                return "No issues noted"
    if "careraddress" in f:            return pt["addr1"]
    if "careremail" in f:              return ""
    if "carername" in f:               return "CARER {}".format(pt["family"])
    if "carersupport" in f:            return "N"
    if "facilid" in f:                 return ""
    if "iscpisexists" in f:            return "N"
    if "accommodationstatus" in f:     return ""
    if "datetimemodified" in f and "int" not in f: return _rand_date(2023,2024)
    if "districtofresidencecode" in f: return "09H"
    if "healthauthoritycode" in f:     return "09H"
    if "reportdelay" in f:             return ""
    if "reportdisp" in f:              return ""
    if "reportreason" in f:            return ""
    if "reportrequired" in f and "int" not in f: return "N"
    if "reportrequiredint" in f:       return "0"

    # Catch-all
    return ""


# ────────────────────────────────────────────────────────────────────────────
# Target table generator  (columns read from catalog)
# ────────────────────────────────────────────────────────────────────────────
def _read_target_catalog():
    tables = {}
    with TARGET_CATALOG.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            t  = row["table_name"]
            fn = row["field_name"]
            if fn:
                tables.setdefault(t, [])
                if fn not in tables[t]:
                    tables[t].append(fn)
    return tables


def generate_target_mocks(tables):
    TARGET_OUT.mkdir(parents=True, exist_ok=True)
    for table, fields in tables.items():
        if table in TARGET_SCHEMA_OVERRIDES:
            for extra_col in TARGET_SCHEMA_OVERRIDES[table]:
                if extra_col not in fields:
                    fields.append(extra_col)
        path = TARGET_OUT / "{}.csv".format(table)
        with path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
            for i in range(ROWS):
                row = {field: _field_value(field, i, table) for field in fields}
                writer.writerow(row)
        print("  [TARGET] {:<45}  {:>3} cols  {} rows".format(table, len(fields), ROWS))


# ────────────────────────────────────────────────────────────────────────────
# Source table generator  (columns from catalog for PATDATA/ADMITDISCH/HWSAPP)
# ────────────────────────────────────────────────────────────────────────────
def _read_source_catalog_fields(table_name):
    fields = []
    with SOURCE_CATALOG.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["table_name"] == table_name:
                fn = row["field_name"]
                if fn and fn not in fields:
                    fields.append(fn)
    return fields


def _write_source_csv(name, headers, rows):
    SOURCE_OUT.mkdir(parents=True, exist_ok=True)
    path = SOURCE_OUT / "{}.csv".format(name)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print("  [SOURCE] {:<45}  {:>3} cols  {} rows".format(name, len(headers), len(rows)))


def _catalog_driven_source(table_name):
    """Generate ROWS rows for a source table using columns from source catalog."""
    headers = _read_source_catalog_fields(table_name)
    rows = [{h: _src(h, i) for h in headers} for i in range(ROWS)]
    return headers, rows


def generate_source_mocks():
    # Catalog-driven generation for all 13 priority source tables.
    # This ensures column sets stay aligned with source schema profiles.
    for tbl in SOURCE_PRIORITY_TABLES:
        headers, rows = _catalog_driven_source(tbl)
        _write_source_csv(tbl, headers, rows)

    # Add non-priority but semantically important reference/context tables.
    for tbl in EXTRA_SOURCE_REFERENCE_TABLES:
        headers = _read_source_catalog_fields(tbl)
        if not headers:
            continue
        rows = [{h: _src(h, i) for h in headers} for i in range(ROWS)]
        _write_source_csv(tbl, headers, rows)
    return

    # --- OPA: Outpatient Attendance -------------------------------------------
    opa_h = [
        "InternalPatientNumber","EpisodeNumber","NhsNumber","Forenames","Surname","Dob","Sex",
        "ApptDate","ApptTime","ApptBookedDate","BookingType","ClinicCode","ClinicConsultant",
        "ClinicSpecialty","ApptCategory","ApptClass","ApptType","ApptStatus","ApptComment",
        "Disposal","DischDate","DischTime","Transport","CancelBy","ApptCancDate","ReasonForCanc",
        "CancelComment","ReferralDate","RefBy","RefConsultant","RefSpecialty","ReasonForRef",
        "PriorityType","AttPriDiagCode","AttSubDiagCode","RefPrimaryDiagnosisCode","RefSubsidDiag",
        "ApptPrimaryProcedureCode","Postcode","PracticeCode","EpiGp","HaCode","CABServiceCode",
        "EbookingReferenceNumber","BookFromWL","RttPeriodStatus","BreachDate","BreachReasonCode",
        "HRGCode","OsvStatus","DateApptBookedInt","PtApptStartDtimeInt","OpDischargeDTimeInt",
    ]
    opa_rows = []
    for i in range(ROWS):
        pt = p(i)
        opa_rows.append({
            "InternalPatientNumber": pt["mrn"],       "EpisodeNumber": str(20000+i+1),
            "NhsNumber": pt["nhs"],                   "Forenames": pt["name_1"],
            "Surname": pt["family"],                  "Dob": pt["dob"],
            "Sex": pt["sex"],                         "ApptDate": _rand_date(2023,2024),
            "ApptTime": _rand_time(),                 "ApptBookedDate": _rand_date(2022,2023),
            "BookingType": random.choice(["ELEC","URGENT","CHOOSE"]),
            "ClinicCode": "CLI{:03d}".format(100+i+1),
            "ClinicConsultant": CONSULTANTS[i % 10],
            "ClinicSpecialty": SPECIALTIES[i % 10],
            "ApptCategory": random.choice(["NEW","FOL"]),
            "ApptClass": random.choice(["1","2"]),
            "ApptType": random.choice(["NEW","FU","POST"]),
            "ApptStatus": random.choice(["ATT","WLK","NATT","SATT"]),
            "ApptComment": "Patient attended. Reviewed by clinician.",
            "Disposal": random.choice(["TREAT","DISCHARGE","FUP","DNA"]),
            "DischDate": _rand_date(2023,2024),       "DischTime": _rand_time(),
            "Transport": "N",                         "CancelBy": "",
            "ApptCancDate": "",                       "ReasonForCanc": "",
            "CancelComment": "",                      "ReferralDate": _rand_date(2022,2023),
            "RefBy": random.choice(["GP","SELF","CONS"]),
            "RefConsultant": CONSULTANTS[i % 10],
            "RefSpecialty": SPECIALTIES[i % 10],
            "ReasonForRef": random.choice(["01","02","03"]),
            "PriorityType": random.choice(["1","2","3"]),
            "AttPriDiagCode": DIAG_ICD10[i % 10],    "AttSubDiagCode": "",
            "RefPrimaryDiagnosisCode": DIAG_ICD10[i % 10], "RefSubsidDiag": "",
            "ApptPrimaryProcedureCode": PROCEDURES[i % 10],
            "Postcode": pt["pc"],                     "PracticeCode": pt["practice"],
            "EpiGp": pt["gp"],                        "HaCode": "09H",
            "CABServiceCode": "",                     "EbookingReferenceNumber": "",
            "BookFromWL": "WL{:03d}".format(i+1),
            "RttPeriodStatus": random.choice(["P","S","R"]),
            "BreachDate": "",                         "BreachReasonCode": "",
            "HRGCode": "AA{}A".format(random.randint(10,99)), "OsvStatus": "N",
            "DateApptBookedInt": _rand_dt_int(2022,2023),
            "PtApptStartDtimeInt": _rand_dt_int(2023,2024),
            "OpDischargeDTimeInt": _rand_dt_int(2023,2024),
        })
    _write_source_csv("OPA", opa_h, opa_rows)

    # --- OPREFERRAL: Outpatient Referral --------------------------------------
    opr_h = [
        "InternalPatientNumber","EpisodeNumber","ReferralDate","ReferralTime","RefBy",
        "ConsCode","Specialty","ReasonForRef","PriorityType","EpiGPCode","EpiGPPracticeCode",
        "DischargeTm","DischargeDt","RefComment","KornerEpisodePrimaryDiagnosisCode","Subsid",
        "OpRegDtimeInt","RTTPeriodStatus","RTTPeriodStatusInt","StatusDT","StatusDTInt",
        "CurrentStatus","CurrentStatusDescription","BreachDate","BreachReasonCode",
        "BreachReasonDesc","DistrictNumber","CaseNoteNumber","HospitalCode",
        "DecisionToRefer","ReasonForReferral","OpEROD","OpERODInt",
    ]
    opr_rows = []
    for i in range(ROWS):
        pt = p(i)
        opr_rows.append({
            "InternalPatientNumber": pt["mrn"],       "EpisodeNumber": str(20000+i+1),
            "ReferralDate": _rand_date(2022,2023),    "ReferralTime": _rand_time(),
            "RefBy": random.choice(["GP","SELF","CONS","AE"]),
            "ConsCode": CONSULTANTS[i % 10],          "Specialty": SPECIALTIES[i % 10],
            "ReasonForRef": random.choice(["01","02","03","04"]),
            "PriorityType": random.choice(["1","2","3"]),
            "EpiGPCode": pt["gp"],                    "EpiGPPracticeCode": pt["practice"],
            "DischargeTm": _rand_time(),              "DischargeDt": _rand_date(2023,2024),
            "RefComment": "Referral letter attached. Patient aware.",
            "KornerEpisodePrimaryDiagnosisCode": DIAG_ICD10[i % 10],
            "Subsid": "",                             "OpRegDtimeInt": _rand_dt_int(2022,2023),
            "RTTPeriodStatus": random.choice(["P","S","R"]),
            "RTTPeriodStatusInt": "1",                "StatusDT": _rand_date(2023,2024),
            "StatusDTInt": _rand_dt_int(2023,2024),
            "CurrentStatus": random.choice(["OPEN","CLOSED","SUSPENDED"]),
            "CurrentStatusDescription": "Active referral in progress",
            "BreachDate": "",                         "BreachReasonCode": "",
            "BreachReasonDesc": "",                   "DistrictNumber": "DN{:05d}".format(10000+i+1),
            "CaseNoteNumber": "CN{:05d}".format(20000+i+1), "HospitalCode": "RVK",
            "DecisionToRefer": _rand_date(2022,2023),
            "ReasonForReferral": random.choice(["01","02","03"]),
            "OpEROD": _rand_date(2023,2024),          "OpERODInt": _rand_dt_int(2023,2024),
        })
    _write_source_csv("OPREFERRAL", opr_h, opr_rows)

    # --- WLCURRENT: Inpatient WL snapshot ------------------------------------
    wlc_h = [
        "InternalPatientNumber","EpisodeNumber","NhsNumber","Forenames","Surname","Dob","Sex",
        "DateOnList","LastReviewDate","Urgency","IntdMgmt","Specialty","Consultant",
        "WardProcedure","Diagnosis","ProcedureCode","TheatreTime","WlStatus","WlType",
        "RemovalDate","WlComment","HospCode","Transport","DistrictNumber",
        "RttPeriodStatus","BreachDate","AdmEROD","AdmERODInt","DateOnListInt",
    ]
    wlc_rows = []
    for i in range(ROWS):
        pt = p(i)
        wlc_rows.append({
            "InternalPatientNumber": pt["mrn"],       "EpisodeNumber": str(20000+i+1),
            "NhsNumber": pt["nhs"],                   "Forenames": pt["name_1"],
            "Surname": pt["family"],                  "Dob": pt["dob"],
            "Sex": pt["sex"],                         "DateOnList": _rand_date(2022,2023),
            "LastReviewDate": _rand_date(2023,2024),
            "Urgency": random.choice(["E","U","R"]),
            "IntdMgmt": random.choice(["E","D","DC"]),
            "Specialty": SPECIALTIES[i % 10],         "Consultant": CONSULTANTS[i % 10],
            "WardProcedure": "Total hip replacement", "Diagnosis": "Hip osteoarthritis",
            "ProcedureCode": PROCEDURES[i % 10],
            "TheatreTime": str(random.randint(60,180)),
            "WlStatus": random.choice(["A","S","R"]),
            "WlType": random.choice(["E","D","DC"]),  "RemovalDate": "",
            "WlComment": "Awaiting pre-op assessment",
            "HospCode": "RVK",                        "Transport": "N",
            "DistrictNumber": "DN{:05d}".format(10000+i+1),
            "RttPeriodStatus": random.choice(["P","S","R"]),
            "BreachDate": "",                         "AdmEROD": _rand_date(2023,2024),
            "AdmERODInt": _rand_dt_int(2023,2024),    "DateOnListInt": _rand_dt_int(2022,2023),
        })
    _write_source_csv("WLCURRENT", wlc_h, wlc_rows)

    # --- WLENTRY: WL entry snapshot ------------------------------------------
    wle_h = [
        "InternalPatientNumber","EpisodeNumber","NhsNumber","DateOnList","Urgency",
        "IntdMgmt","Specialty","Consultant","ProcedureCode","WlStatus","WlType",
        "HospCode","DistrictNumber","RttPeriodStatus","DateOnListInt",
    ]
    wle_rows = []
    for i in range(ROWS):
        pt = p(i)
        wle_rows.append({
            "InternalPatientNumber": pt["mrn"],       "EpisodeNumber": str(20000+i+1),
            "NhsNumber": pt["nhs"],                   "DateOnList": _rand_date(2021,2022),
            "Urgency": random.choice(["E","U","R"]),
            "IntdMgmt": random.choice(["E","D","DC"]),
            "Specialty": SPECIALTIES[i % 10],         "Consultant": CONSULTANTS[i % 10],
            "ProcedureCode": PROCEDURES[i % 10],      "WlStatus": "A",
            "WlType": random.choice(["E","D","DC"]),  "HospCode": "RVK",
            "DistrictNumber": "DN{:05d}".format(10000+i+1),
            "RttPeriodStatus": random.choice(["P","S","R"]),
            "DateOnListInt": _rand_dt_int(2021,2022),
        })
    _write_source_csv("WLENTRY", wle_h, wle_rows)

    # --- WLACTIVITY: TCI / deferral activity ---------------------------------
    wla_h = [
        "InternalPatientNumber","EpisodeNumber","ActivityType","DeferralStartDate",
        "DeferralEndDate","DeferralReason","DeferralComment","OperationText",
        "AdmissionReasonComment","BookingType","Consultant","OfferDate","AgreedDate",
        "AgreedFlag","PreassessmentDate","TciDate","OperationDate","EstimatedDischargeDate",
        "TciStatus","Specialty","HospCode","DistrictNumber",
    ]
    wla_rows = []
    for i in range(ROWS):
        pt = p(i)
        wla_rows.append({
            "InternalPatientNumber": pt["mrn"],       "EpisodeNumber": str(20000+i+1),
            "ActivityType": random.choice(["TCI","DEFER","REMOVE"]),
            "DeferralStartDate": _rand_date(2022,2023),
            "DeferralEndDate": _rand_date(2023,2024),
            "DeferralReason": random.choice(["PATIENT","HOSPITAL","MEDICAL"]),
            "DeferralComment": "Patient requested reschedule of admission",
            "OperationText": "Total hip replacement - left",
            "AdmissionReasonComment": "Elective admission as planned",
            "BookingType": random.choice(["ELEC","URGENT"]),
            "Consultant": CONSULTANTS[i % 10],        "OfferDate": _rand_date(2023,2024),
            "AgreedDate": _rand_date(2023,2024),      "AgreedFlag": "Y",
            "PreassessmentDate": _rand_date(2023,2024),
            "TciDate": _rand_date(2023,2024),         "OperationDate": _rand_date(2023,2024),
            "EstimatedDischargeDate": _rand_date(2023,2024),
            "TciStatus": random.choice(["A","C","D"]),
            "Specialty": SPECIALTIES[i % 10],         "HospCode": "RVK",
            "DistrictNumber": "DN{:05d}".format(10000+i+1),
        })
    _write_source_csv("WLACTIVITY", wla_h, wla_rows)

    # --- FCEEXT: Finished Consultant Episodes --------------------------------
    fce_h = [
        "InternalPatientNumber","EpisodeNumber","NhsNumber","Forenames","Surname","Dob","Sex",
        "AdmissionDatetime","DischargeDatetime","FCEStartDate","FCEStartTime","FCEEndDate",
        "FCEEndTime","FceSequenceNo","Specialty","Consultant","PatientCategory","IntdMgmt",
        "AgeAtStartOfEpisode","KornerEpisodePrimaryDiagnosisCode","Subsid",
        "KornerEpisodePrimaryProcedureCode","KornerEpisodePrimaryProcedureDateExternal",
        "HrgCode","HrgOutlierFlag","SourceOfAdmission","DestinationOnDischarge",
        "MethodOfAdmission","MethodOfDischarge","GpCode","PracticeCode","ProviderCode",
        "PurchaserCode","Postcode","HospCdadmit","HospCdend","WardCdadmit","WardCdend",
        "DaysOnWl","DateOnList","Los","LosForConsEps","DistrictNumber","CaseNoteNo",
        "IpAdmDtimeInt","IpDschDtimeInt","FCEStartDateInt","FCEEndDateInt",
    ]
    fce_rows = []
    for i in range(ROWS):
        pt = p(i)
        fce_rows.append({
            "InternalPatientNumber": pt["mrn"],       "EpisodeNumber": str(20000+i+1),
            "NhsNumber": pt["nhs"],                   "Forenames": pt["name_1"],
            "Surname": pt["family"],                  "Dob": pt["dob"],
            "Sex": pt["sex"],                         "AdmissionDatetime": _rand_date(2022,2023),
            "DischargeDatetime": _rand_date(2023,2024),
            "FCEStartDate": _rand_date(2022,2023),    "FCEStartTime": "09:00",
            "FCEEndDate": _rand_date(2023,2024),      "FCEEndTime": "14:00",
            "FceSequenceNo": str(i+1),                "Specialty": SPECIALTIES[i % 10],
            "Consultant": CONSULTANTS[i % 10],        "PatientCategory": random.choice(["01","02","03"]),
            "IntdMgmt": random.choice(["E","D","DC"]),
            "AgeAtStartOfEpisode": str(random.randint(18,90)),
            "KornerEpisodePrimaryDiagnosisCode": DIAG_ICD10[i % 10],
            "Subsid": "",
            "KornerEpisodePrimaryProcedureCode": PROCEDURES[i % 10],
            "KornerEpisodePrimaryProcedureDateExternal": _rand_date(2022,2023),
            "HrgCode": "AA{}A".format(random.randint(10,99)), "HrgOutlierFlag": "N",
            "SourceOfAdmission": random.choice(["19","51","52","99"]),
            "DestinationOnDischarge": random.choice(["19","51","52","99"]),
            "MethodOfAdmission": random.choice(["11","12","21","22"]),
            "MethodOfDischarge": random.choice(["1","2","3","4"]),
            "GpCode": pt["gp"],                       "PracticeCode": pt["practice"],
            "ProviderCode": "RVK",                    "PurchaserCode": "09H",
            "Postcode": pt["pc"],                     "HospCdadmit": "RVK",
            "HospCdend": "RVK",                       "WardCdadmit": WARDS[i % 10],
            "WardCdend": WARDS[i % 10],               "DaysOnWl": str(random.randint(10,365)),
            "DateOnList": _rand_date(2021,2022),      "Los": str(random.randint(1,30)),
            "LosForConsEps": str(random.randint(1,30)),
            "DistrictNumber": "DN{:05d}".format(10000+i+1),
            "CaseNoteNo": "CN{:05d}".format(20000+i+1),
            "IpAdmDtimeInt": _rand_dt_int(2022,2023), "IpDschDtimeInt": _rand_dt_int(2023,2024),
            "FCEStartDateInt": _rand_dt_int(2022,2023),"FCEEndDateInt": _rand_dt_int(2023,2024),
        })
    _write_source_csv("FCEEXT", fce_h, fce_rows)

    # --- CPSGREFERRAL: Community / MH Referral --------------------------------
    cpsg_h = [
        "InternalPatientNumber","EpisodeNumber","NhsNumber","Forenames","Surname","Dob","Sex",
        "ReferralDate","ReferralTime","ReferralPriority","Source","LeadClinician","ServGroup",
        "DischargeDate","DischargeReason","Outcome","RefDtTmInt","PrimDiag","PrimDiagSeverity",
        "SubsDiag","Type","Status","StatusInt","Casenote","ClinicalCategory","DiagComment1",
        "DiagComment2","ReferrerId","ReferrerName","ReferrerSpecialty","ReferrerType","Priority",
        "DistrictNumber","HospitalCode","Specialty","Consultant",
    ]
    cpsg_rows = []
    for i in range(ROWS):
        pt = p(i)
        cpsg_rows.append({
            "InternalPatientNumber": pt["mrn"],       "EpisodeNumber": str(20000+i+1),
            "NhsNumber": pt["nhs"],                   "Forenames": pt["name_1"],
            "Surname": pt["family"],                  "Dob": pt["dob"],
            "Sex": pt["sex"],                         "ReferralDate": _rand_date(2022,2023),
            "ReferralTime": _rand_time(),
            "ReferralPriority": random.choice(["ROUTINE","URGENT","EMERGENCY"]),
            "Source": random.choice(["GP","SELF","AE","CONS"]),
            "LeadClinician": CONSULTANTS[i % 10],
            "ServGroup": random.choice(["CMHT","CRISIS","AOT","EIS"]),
            "DischargeDate": _rand_date(2023,2024),
            "DischargeReason": random.choice(["01","02","03"]),
            "Outcome": random.choice(["DISCHARGE","TRANSFER","ONGOING"]),
            "RefDtTmInt": _rand_dt_int(2022,2023),
            "PrimDiag": DIAG_ICD10[i % 10],
            "PrimDiagSeverity": random.choice(["MILD","MOD","SEVERE"]),
            "SubsDiag": "",                           "Type": "CMTY",
            "Status": random.choice(["SG","SG DSCH"]), "StatusInt": "1",
            "Casenote": "CN{:05d}".format(20000+i+1),
            "ClinicalCategory": random.choice(["MH","CMTY","LD"]),
            "DiagComment1": "Assessment completed by lead clinician",
            "DiagComment2": "Care plan agreed with patient",
            "ReferrerId": pt["gp"],
            "ReferrerName": "DR {}".format(SURNAMES[i % 10]),
            "ReferrerSpecialty": "GP",                "ReferrerType": "GP",
            "Priority": random.choice(["ROUTINE","URGENT"]),
            "DistrictNumber": "DN{:05d}".format(10000+i+1), "HospitalCode": "RVK",
            "Specialty": SPECIALTIES[i % 10],         "Consultant": CONSULTANTS[i % 10],
        })
    _write_source_csv("CPSGREFERRAL", cpsg_h, cpsg_rows)

    # --- SMREPISODE: MH / SMR Episode ----------------------------------------
    smr_h = [
        "InternalPatientNumber","EpisodeNumber","NhsNumber","Forenames","Surname","Sex",
        "DateOfBirth","Address1","Address2","Address3","Address4","Postcode",
        "AdmissionDate","DischargeDate","AdmissionSource","AdmissionMethod","Consultant",
        "Specialty","LegalStatus","LegalStatusDesc","MentalCategory","Caseholder",
        "LeadClinician","PrimDiag","CpaType","NextReviewDate","Institution",
        "DetentionLocation","DiagComment1","DiagComment2","AdmissionFrom",
        "SectionReviewDate","ConsentDueDate","KeyWorker","CareCoordinator",
        "DistrictNumber","CaseNoteNumber","HospitalCode",
    ]
    smr_rows = []
    for i in range(ROWS):
        pt = p(i)
        smr_rows.append({
            "InternalPatientNumber": pt["mrn"],       "EpisodeNumber": str(20000+i+1),
            "NhsNumber": pt["nhs"],                   "Forenames": pt["name_1"],
            "Surname": pt["family"],                  "Sex": pt["sex"],
            "DateOfBirth": pt["dob"],                 "Address1": pt["addr1"],
            "Address2": pt["addr2"],                  "Address3": "",
            "Address4": "",                           "Postcode": pt["pc"],
            "AdmissionDate": _rand_date(2020,2023),   "DischargeDate": _rand_date(2023,2024),
            "AdmissionSource": random.choice(["51","19","52"]),
            "AdmissionMethod": random.choice(["11","12","21","22"]),
            "Consultant": CONSULTANTS[i % 10],        "Specialty": "PSYCH",
            "LegalStatus": random.choice(["02","03","07","17","01"]),
            "LegalStatusDesc": "Informal",            "MentalCategory": "MENTAL ILLNESS",
            "Caseholder": CONSULTANTS[i % 10],        "LeadClinician": CONSULTANTS[i % 10],
            "PrimDiag": DIAG_ICD10[i % 10],
            "CpaType": random.choice(["STANDARD","ENHANCED"]),
            "NextReviewDate": _rand_date(2024,2025),
            "Institution": "QUEEN VICTORIA HOSPITAL", "DetentionLocation": "PICU Ward 5",
            "DiagComment1": "CPA review completed",
            "DiagComment2": "Care plan active and reviewed",
            "AdmissionFrom": random.choice(["COURT","HOME","AE"]),
            "SectionReviewDate": _rand_date(2023,2025),
            "ConsentDueDate": _rand_date(2023,2025),
            "KeyWorker": CONSULTANTS[i % 10],
            "CareCoordinator": CONSULTANTS[(i+1) % 10],
            "DistrictNumber": "DN{:05d}".format(10000+i+1),
            "CaseNoteNumber": "CN{:05d}".format(20000+i+1), "HospitalCode": "RVK",
        })
    _write_source_csv("SMREPISODE", smr_h, smr_rows)

    # --- ADTLADDCOR: Patient Address Corrections -----------------------------
    adr_h = [
        "Intpatno","Districtnumber","SeqNo","TransactDate","Transactuserid","TransactType",
        "Newaddline1","Newaddline2","Newaddline3","Newaddline4","Newpostcode","Newpseudopostcode",
        "Oldaddline1","Oldaddline2","Oldaddline3","Oldaddline4","Oldpostcode","Oldpseudopostcode",
        "PmiPatientAddressNewEffectiveDateFromInt","PmiPatientAddressNewEffectiveDateToInt",
        "PmiPatientAddressOldEffectiveDateFromInt","PmiPatientAddressOldEffectiveDateToInt",
        "NhsNumber",
    ]
    adr_rows = []
    for i in range(ROWS):
        pt = p(i)
        adr_rows.append({
            "Intpatno": pt["mrn"],
            "Districtnumber": "DN{:05d}".format(10000+i+1),
            "SeqNo": str(i+1),
            "TransactDate": _rand_date(2022,2023),
            "Transactuserid": "USR{:03d}".format(i+1),
            "TransactType": "AC",
            "Newaddline1": pt["addr1"],               "Newaddline2": pt["addr2"],
            "Newaddline3": "",                         "Newaddline4": "",
            "Newpostcode": pt["pc"],                   "Newpseudopostcode": "",
            "Oldaddline1": "{} Old Road".format(5+i+1),
            "Oldaddline2": "London",                   "Oldaddline3": "",
            "Oldaddline4": "",                         "Oldpostcode": "SW1A 1AA",
            "Oldpseudopostcode": "",
            "PmiPatientAddressNewEffectiveDateFromInt": "202201010000",
            "PmiPatientAddressNewEffectiveDateToInt":  "999912312359",
            "PmiPatientAddressOldEffectiveDateFromInt": "201001010000",
            "PmiPatientAddressOldEffectiveDateToInt":  "202112312359",
            "NhsNumber": pt["nhs"],
        })
    _write_source_csv("ADTLADDCOR", adr_h, adr_rows)


# ────────────────────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────────────────────
def _parse_args():
    parser = argparse.ArgumentParser(description="Generate source/target mock CSVs for PAS migration testing.")
    parser.add_argument("--rows", type=int, default=20, help="Number of patient-linked records to generate per table.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation.")
    return parser.parse_args()


def main():
    global ROWS, ACTIVE_PATIENTS
    args = _parse_args()
    if args.rows < 1:
        raise ValueError("--rows must be >= 1")

    ROWS = int(args.rows)
    ACTIVE_PATIENTS = _build_patient_roster(ROWS)
    random.seed(args.seed)   # reproducible output
    print("=" * 70)
    print("NHS PAS Data Migration - Full Mock Data Generator  (v2)")
    print("Patients: {}  |  Target tables: 38  |  Source base tables: 13 (+ reference expansion)".format(ROWS))
    print("=" * 70)

    print("\nReading target schema catalog...")
    tables = _read_target_catalog()
    print("  Found {} target LOAD_ tables.\n".format(len(tables)))

    print("Generating TARGET mock CSVs...")
    generate_target_mocks(tables)

    print("\nGenerating SOURCE mock CSVs...")
    generate_source_mocks()

    print("\n" + "=" * 70)
    print("Done. Files written to mock_data/target/ and mock_data/source/")
    print("=" * 70)


if __name__ == "__main__":
    main()
