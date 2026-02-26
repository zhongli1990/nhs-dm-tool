# NHS PAS 18.4 Target Data Schema Profile
**Project:** Queen Victoria Hospital NHS Trust — EPR/PAS Data Migration (V83 → PAS 18.4)
**Document version:** 1.0
**Date:** 2026-02-25
**Source:** `PAS 18.4 Data Migration Technical Guide (FOR REF ONLY).pdf` → `schemas/target_schema_catalog.csv`
**Vendor:** Altera Digital Health Inc. — PAS v18.4

---

## 1. Executive Summary

The target system is **Altera PAS v18.4**, a modern patient administration system. The migration target defines **38 staging tables** (prefixed `LOAD_`) covering 880 fields across 10 clinical domains. These staging tables are loaded by Altera's generic migration loader packages (`oasloadstaff_package`, `oasloadpmi_package`, etc.) which validate, transform and populate the live PAS transaction tables.

**Critical caveat:** The target specification PDF is explicitly marked **"FOR REF ONLY NOT TO BE USED"** — the authoritative contract data dictionary has not yet been provided to the Trust. All field definitions in this document must be re-verified against the confirmed delivery version before go-live.

---

## 2. Catalog Metadata & Parse Quality

### 2.1 Catalog Column Schema

The `target_schema_catalog.csv` has 8 columns:

| Column | Description |
|--------|-------------|
| `table_name` | LOAD_ staging table name |
| `field_name` | Clean extracted field name |
| `raw_field_name` | Raw text from PDF (often contains parse artefacts) |
| `data_type` | SQL data type: VARCHAR2 / NUMBER / DATE / CHAR |
| `length` | Maximum column length (blank = variable or not specified) |
| `mandatory_hint` | `Y` = mandatory / `N` = optional |
| `parse_confidence` | PDF parse confidence score: 1.00 (verified) to 0.80 (extracted) |
| `source_page` | PDF page number the field was extracted from |

### 2.2 Parse Confidence Distribution

| Score | Count | Interpretation |
|-------|-------|----------------|
| 1.00 | ~120 fields | High confidence — exact text match or manually verified |
| 0.85 | ~15 fields | Medium confidence — known artefact in raw_field_name |
| 0.80 | ~745 fields | Standard PDF extraction — field name clean, description may be embedded in raw_field_name |

### 2.3 PDF Parse Artefacts Identified

The `raw_field_name` column frequently contains concatenated text due to PDF table-cell merging:

| Artefact Pattern | Example | Root Cause |
|------------------|---------|------------|
| `fieldnameMust` | `job_idMust` | Mandatory hint "Must" merged into field name |
| `fieldnameFore` | `first_nameFore` | Description word "Fore name" merged |
| `DATE10fieldname` | `DATE10PATHWAY_END_DATEMust` | Datatype+length prefix merged |
| `VARCHAR2NNfieldname` | `VARCHAR210SYSTEM_CODEUnique` | Type+length prefix merged |
| `NUMBER42fieldname` | `NUMBER42RTTPWY_RECNO_OUT_ENCOUNTER` | Type+length prefix merged |
| Phantom fields | `must`, `before`, `ranges`, `table`, `indicates`, `ged`, `ge_date`, `ge_toe`, `ge_typee`, `ge_methode`, `ge_specialty`, `ge_consultant`, `acters`, `ge_status` | PDF artifact rows — NOT real fields |

**Phantom field count:** 14 phantom fields identified across multiple tables. These must be excluded from all ETL pipelines.

---

## 3. Universal Column Patterns

Every LOAD_ table contains a standard set of system fields. These are defined once here and not repeated in each table section below.

| Field | Type | Len | Mandatory | Description |
|-------|------|-----|-----------|-------------|
| `record_number` | NUMBER | 42 | N | Unique identifier for this extracted row (ETL-generated surrogate) |
| `system_code` | VARCHAR2 | 10 | N | Source system code — maps to code type 10599 "Dataload System" |
| `external_system_id` | VARCHAR2 | 100 | N | Unique patient/entity ID from source system |

Most tables also carry:
- `main_crn_type` (VARCHAR2 80) — Main hospital number ID type; maps to code type 9
- `main_crn` (VARCHAR2 30) — Main hospital number value; loaded into PATIENT_IDS.id_number
- FK fields (`loadpmi_record_number`, `loadref_record_number`, etc.) — surrogate keys linking to parent tables

---

## 4. Table Load Order & Referential Integrity

The migration process **must** be executed in the following strict order:

```
1. LOAD_STAFF           → staff_master, staff_ids, staff_names, staff_hospitals
2. LOAD_USERS           → maps006, eoasis_page_links
3. LOAD_SITES           → codes, provider_site_codes, site_code_contacts
4. LOAD_PMI             → patient_master, patient_ids, patient_names, patient_contacts
   ├── LOAD_PMIIDS      → patient_ids (additional identifiers)
   ├── LOAD_PMIALIASES  → patient_names (historical names)
   ├── LOAD_PMIADDRS    → patient_contacts (address history)
   ├── LOAD_PMICONTACTS → patient_contacts (NOK/carer contacts)
   ├── LOAD_PMIALLERGIES→ patient_allergies
   ├── LOAD_PMISTAFFWARNINGS → patient_warnings
   ├── LOAD_PMIGPAUDIT  → gp_audit
   ├── LOAD_CASENOTELOCS→ case_note_locations
   └── LOAD_PMICASENOTEHISTORY → case_note_history
5. LOAD_RTT_PATHWAYS    → rtt_pathways
   └── LOAD_REFERRALS   → referrals
       └── LOAD_RTT_PERIODS → rtt_periods
           ├── LOAD_RTT_EVENTS    → rtt_events
           ├── LOAD_OPDWAITLIST   → opd_wait_list
           │   ├── LOAD_OPDWAITLISTDEF → opd_wl_deferrals
           │   └── LOAD_OPD_APPOINTMENTS → opd_appointments
           │       └── LOAD_OPD_CODING → opd_coding
           └── LOAD_IWL           → ip_wait_list
               ├── LOAD_IWL_DEFERRALS → iwl_deferrals
               └── LOAD_IWL_TCIS      → iwl_tcis
                   └── LOAD_ADT_ADMISSIONS → admissions
                       ├── LOAD_ADT_EPISODES  → episodes
                       │   ├── LOAD_ADT_WARDSTAYS → ward_stays
                       │   └── LOAD_ADT_CODING    → coding
                       └── LOAD_MH_DETENTION_MASTER → mh_detentions
                           └── LOAD_MH_DETENTION_TRANSFERS
6. LOAD_MH_CPA_MASTER   → mh_cpa
   └── LOAD_MH_CPA_HISTORY
7. LOAD_CMTY_APPOINTMENTS → community_appointments
8. Archives (independently):
   LOAD_OPD_ARCHIVE / LOAD_ADT_ARCHIVE / LOAD_DETENTION_ARCHIVE / LOAD_CPA_ARCHIVE
9. LOAD_IWL_PROFILES    → iwl_profiles (reference data — any time)
```

---

## 5. Complete Table-by-Table Schema

---

### 5.1 LOAD_STAFF — Hospital Staff Data
**Pages:** 6–10 | **Fields:** 43 | **Loads into:** staff_master, staff_ids, staff_names, staff_hospitals, team_staff, staff_specialty, staff_depts
**Package:** `oasloadstaff_package.load_staff`
**Source:** Reference data (not migrated from V83 patient records — requires manual population)

| Field | Type | Len | Mand | Description / Validation |
|-------|------|-----|------|--------------------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Maps to code type 10599 "Dataload System" |
| user_name | VARCHAR2 | 20 | N | Login username — uppercase; loaded into maps006.user_name |
| first_name | VARCHAR2 | 40 | N | Forename — uppercase; → maps006.first_name |
| middle_name | VARCHAR2 | 40 | N | Middle name — uppercase; → maps006.middle_name |
| family_name | VARCHAR2 | 40 | N | Family name — uppercase; → maps006.family_name |
| acters | CHAR | — | N | **PHANTOM FIELD** — PDF artefact of word "characters"; ignore |
| job_id | NUMBER | 6 | Y | Must be valid PAS Job Group ID (MAPJOBS form); → maps006.job_id |
| password | VARCHAR2 | 80 | N | User account password; → maps006.password |
| psswd_life_months | NUMBER | 6 | Y | Non-negative integer ≤1200; → maps006.psswd_life_months |
| psswd_expiry_date | DATE | — | N | Date logon disallowed; → maps006.psswd_expiry_date |
| language_id | NUMBER | 2 | N | Valid PAS Language ID (MAPFLANG form); → maps006.language_id |
| staff_id | VARCHAR2 | 10 | Y | Must match PAS Staff Master (STFFSCRN form); required if employee_flag=Y |
| default_parts_entity | VARCHAR2 | 10 | Y | Valid Work Entity code (ADTWORKE form); → maps006.default_parts_entity |
| default_tools_entity | VARCHAR2 | 10 | Y | Valid Work Entity code; → maps006.default_tools_entity |
| default_labour_entity | VARCHAR2 | 10 | Y | Valid Work Entity code; → maps006.default_labour_entity |
| employee_flag | VARCHAR2 | 1 | Y | Must be Y or N; if Y then staff_id is required |
| default_stock_entity | VARCHAR2 | 10 | Y | Valid Work Entity code; → maps006.default_stock_entity |
| staff_security_level | VARCHAR2 | 80 | N | Maps to code type 10018 "SECURITY REQUIRED" |
| phone_no | VARCHAR2 | 20 | N | Direct dial telephone; → maps006.phone_no |
| extension_no | VARCHAR2 | 5 | N | Telephone extension; → maps006.extension_no |
| default_login_entity | VARCHAR2 | 10 | N | Default work entity for login restriction; → maps006.default_login_entity |
| eoasis_user | VARCHAR2 | 1 | Y | Y/N/Null (Null=N); if Y, enables Java Web App access; → maps006.sqlplus_user |
| allow_logon | VARCHAR2 | 1 | N | Y or N — controls PAS application login; → maps006.allow_logon |
| default_executable | VARCHAR2 | 10 | N | Default PAS Forms executable (MAPFUNCT form); → maps006.default_executable |
| gp_national_code | VARCHAR2 | 10 | N | National GP code (e.g. C0000048); → GP_MASTER.registration_code |
| type_of_user | VARCHAR2 | 80 | N | Maps to code type 10495 "EOASIS USER TYPES" |
| login_from_date | DATE | 10 | N | Date user permitted to log on (default: 1 hour after creation) |
| login_to_date | DATE | — | N | Date user may NOT log on after |
| practice_national_code | VARCHAR2 | 10 | N | National GP practice code (e.g. A81006); → GP_PRACTICE_MASTER.gp_practice_code |
| email_address | VARCHAR2 | 80 | N | User email address; → maps006.email_address |
| can_log_support_calls | VARCHAR2 | 1 | N | Legacy field — must be Y or N (Null→N) |
| ask_review_warnings | VARCHAR2 | 1 | Y | Y or N; if Y, prompts user to review clinical warnings on login |
| from_time | NUMBER | 4 | N | Login permitted from (minutes after midnight, 0–1439; default 0=00:00) |
| to_time | NUMBER | 4 | N | Login not permitted after (0–1439; default 1439=23:59) |
| mon_allowed | VARCHAR2 | 1 | Y | Y/N/Null (Null→Y) — Monday login permitted |
| tue_allowed | VARCHAR2 | 1 | Y | Y/N/Null (Null→Y) — Tuesday login permitted |
| wed_allowed | VARCHAR2 | 1 | Y | Y/N/Null (Null→Y) — Wednesday login permitted |
| thu_allowed | VARCHAR2 | 1 | Y | Y/N/Null (Null→Y) — Thursday login permitted |
| fri_allowed | VARCHAR2 | 1 | Y | Y/N/Null (Null→Y) — Friday login permitted |
| sat_allowed | VARCHAR2 | 1 | Y | Y/N/Null (Null→Y) — Saturday login permitted |
| sun_allowed | VARCHAR2 | 1 | Y | Y/N/Null (Null→Y) — Sunday login permitted |

> **Note:** `default_team` (Maps to code type 10721 "TEAMS FOR DATALOAD MAPPING") is defined in LOAD_USERS but also applies here.

---

### 5.2 LOAD_USERS — Altera PAS Application Users
**Pages:** 11–15 | **Fields:** 44 | **Loads into:** maps006, eoasis_page_links
**Package:** `oasloaduser_package.load_user`
**Note:** Creates an Oracle user account for each application user. Structurally identical to LOAD_STAFF plus two additional fields.

| Field | Type | Len | Mand | Description / Validation |
|-------|------|-----|------|--------------------------|
| default_team | VARCHAR2 | 80 | N | Maps to code type 10721 "TEAMS FOR DATALOAD MAPPING"; → maps006.default_team_id |
| client_user | VARCHAR2 | 80 | N | Maps to code type 10768 "SUPPORT CATEGORIES"; → maps006.client_user |
| *[All other fields identical to LOAD_STAFF — see §5.1]* | | | | |

> **Key difference from LOAD_STAFF:** LOAD_USERS creates an Oracle database user account in addition to the application user record. `eoasis_user=Y` enables both Java Web App and Oracle Forms access.

---

### 5.3 LOAD_SITES — Site Codes & Addresses
**Pages:** 16–17 | **Fields:** 18 | **Loads into:** codes, provider_site_codes, site_code_contacts
**Package:** `oasloadsite_package.load_sites`

| Field | Type | Len | Mand | Description / Validation |
|-------|------|-----|------|--------------------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source system site identifier |
| provider_prefix | VARCHAR2 | 6 | N | Provider prefix as in MAPSHEAD; resolves hospital_id from MAPS010 via site_prefix match |
| site_code | VARCHAR2 | 15 | N | User site code linked to provider — must be unique and uppercase; → CODES.user_code (type 10454) |
| site_description | VARCHAR2 | 80 | N | Site description — uppercase; → CODES.description |
| site_link_applies_start | DATE | 10 | N | Start date of site-provider link (DD/MM/YYYY, cannot be future); → PROVIDER_SITE_CODES.applies_start |
| site_link_applies_end | DATE | 10 | N | End date of link (DD/MM/YYYY, if provided must be > start and not future); → PROVIDER_SITE_CODES.applies_end |
| address_1 | VARCHAR2 | 80 | N | Site address line 1; → SITE_CODE_CONTACTS.address_1 |
| address_2 | VARCHAR2 | 80 | N | Site address line 2; → SITE_CODE_CONTACTS.address_2 |
| address_3 | VARCHAR2 | 80 | N | Site address line 3; → SITE_CODE_CONTACTS.address_3 |
| address_4 | VARCHAR2 | 80 | N | Site address line 4; → SITE_CODE_CONTACTS.address_4 |
| post_code | VARCHAR2 | 20 | N | Site postcode; → SITE_CODE_CONTACTS.post_code |
| phone_1 | VARCHAR2 | 20 | N | Site phone 1; → SITE_SITE_CONTACTS.phone_1 |
| phone_2 | VARCHAR2 | 20 | N | Site phone 2; → SITE_SITE_CONTACTS.phone_2 |
| email | VARCHAR2 | 80 | N | Site email; → SITE_SITE_CONTACTS.EMAIL |
| applies_start | DATE | 10 | Y | Contact record applies from (DD/MM/YYYY, cannot be before site_link_applies_start); → SITE_CODE_CONTACTS.applies_start |
| applies_end | DATE | 10 | Y | Contact record applies to (DD/MM/YYYY, must be > applies_start if provided); → SITE_CODE_CONTACTS.applies_end |

---

### 5.4 LOAD_PMI — Patient Master Index
**Pages:** 18–25 | **Fields:** 89 | **Loads into:** patient_ids, patient_master, patient_names, patient_contacts, patient_xtra_info
**Package:** `oasloadpmi_package.load_patient`

#### 5.4.1 Identity Fields

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| system_code | VARCHAR2 | 10 | N | Source system identifier |
| external_system_id | VARCHAR2 | 100 | N | Source patient ID (InternalPatientNumber from V83) |
| main_crn_type | VARCHAR2 | 80 | N | Main hospital number type; maps to code type 9; → PATIENT_IDS.id_type_code |
| main_crn | VARCHAR2 | 30 | N | Main hospital number value; → PATIENT_IDS.id_number |
| date_registered | NUMBER | — | Y | Patient registration date (DD/MM/YYYY); if not held use date_of_birth; → PATIENT_MASTER.date_registered |
| nhs_number | VARCHAR2 | 30 | N | NHS Number; → PATIENT_IDS.ID_NUMBER (code type 9, prog code 4) |
| nhs_number_statusnhs | VARCHAR2 | 80 | N | NHS Number tracing status; maps to code type 10366 "NHS Number Status Code"; → PATIENT_IDS.status_code |

#### 5.4.2 Demographics

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| sex | VARCHAR2 | 80 | N | Maps to code type 3 "Sex"; → PATIENT_MASTER.sex |
| title | VARCHAR2 | 80 | N | Maps to code type 29 "Title"; → PATIENT_MASTER.title |
| pat_name_1 | VARCHAR2 | 40 | N | Given name 1; → PATIENT_MASTER.pat_name_1 |
| pat_name_2 | VARCHAR2 | 40 | N | Given name 2; → PATIENT_MASTER.pat_name_2 |
| pat_name_3 | VARCHAR2 | 40 | N | Given name 3; → PATIENT_MASTER.pat_name_3 |
| pat_name_family | VARCHAR2 | 40 | N | Family/surname; → PATIENT_MASTER.pat_name_family |
| maiden_name | VARCHAR2 | 40 | N | Maiden name; → PATIENT_MASTER.maiden_name + triggers PATIENT_NAMES record |
| of_birth | DATE | 10 | Y | Date of birth (DD/MM/YYYY); → PATIENT_MASTER.date_of_birth |
| place_born | VARCHAR2 | 80 | N | Maps to code type 333 "Country Codes"; → PATIENT_MASTER.place_born_code |
| entered_country | DATE | 10 | Y | Date entered country (DD/MM/YYYY); → PATIENT_MASTER.date_entered_country |
| nationality | VARCHAR2 | 80 | N | Maps to code type 5 "Nationality"; → PATIENT_MASTER.nationality_code |
| ethnic_group | VARCHAR2 | 80 | N | Maps to code type 10028 "Ethnic Origin"; → PATIENT_MASTER.ethnic_origin |
| preferred_language | VARCHAR2 | 80 | N | Maps to code type 10658 "Preferred Language"; → PATIENT_MASTER.preferred_language_id |
| religion_code | VARCHAR2 | 80 | N | Maps to code type 1 "Religion"; → PATIENT_MASTER.religion_code |
| marital_status | VARCHAR2 | 80 | N | Maps to code type 2 "Marital Status"; → PATIENT_MASTER.marital_status |
| occupation_code | VARCHAR2 | 80 | N | Maps to code type 4 "Occupation"; → PATIENT_MASTER.occupation_code |
| where_heard_of_service | VARCHAR2 | 80 | N | Maps to code type 10753 "Where Heard Of Service"; → PATIENT_MASTER.where_heard_of_code |

#### 5.4.3 Patient Address (Permanent)

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| pat_address_1 | VARCHAR2 | 80 | N | Address line 1; → PATIENT_CONTACTS.address_1 |
| pat_address_2 | VARCHAR2 | 80 | N | Address line 2; → PATIENT_CONTACTS.address_2 |
| pat_address_3 | VARCHAR2 | 80 | N | Address line 3; → PATIENT_CONTACTS.address_3 |
| pat_address_4 | VARCHAR2 | 80 | N | Address line 4; → PATIENT_CONTACTS.address_4 |
| post_code | VARCHAR2 | 20 | N | Postcode; → PATIENT_CONTACTS.post_code |
| telephone_no | VARCHAR2 | 20 | N | Phone 1; → PATIENT_CONTACTS.phone_1 |
| telephone_no_2 | VARCHAR2 | 20 | N | Phone 2; → PATIENT_CONTACTS.phone_2 |
| telephone_no_3 | VARCHAR2 | 20 | N | Phone 3; → PATIENT_CONTACTS.phone_3 |
| pat_email_address | VARCHAR2 | 80 | N | Email address; → PATIENT_MASTER.email_address |
| pat_lives_alone | VARCHAR2 | 1 | N | Y or N; → PATIENT_CONTACTS.lives_alone_flag |
| pat_permission_to_contact | VARCHAR2 | 1 | N | Y or N — permission to send correspondence; → PATIENT_CONTACTS.permission_to_contact_flag |
| pat_permission_to_phone | VARCHAR2 | 1 | N | Y or N — permission to phone; → PATIENT_CONTACTS.permission_to_phone_flag |
| pat_address_from | DATE | 10 | N | Address applies from (DD/MM/YYYY); → PATIENT_CONTACTS.applies_start |

#### 5.4.4 Death Information

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| of_death | DATE | 10 | Y | Date of death (DD/MM/YYYY HH24:MI); → PATIENT_MASTER.date_of_death |
| where_died | VARCHAR2 | 80 | N | Maps to code type 274 "Where Died" (e.g. Ward, Operating Theatre); → DEATHS.where_died |
| cause_of_death | VARCHAR2 | 80 | N | Maps to code type 10752 "Causes of Death" (e.g. Cardiac Failure); → DEATHS.cause_of_death |
| death_treatment_related | VARCHAR2 | 1 | N | Y or N; → DEATHS.death_treatment_related |
| death_hiv_related | VARCHAR2 | 1 | N | Y or N; → DEATHS.death_hiv_related |

#### 5.4.5 Extra Information (10 pairs)

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| extra_info_1_type | VARCHAR2 | 80 | N | Maps to code type 23 "Extra Information (Patient)" (e.g. Smoker?, Orthoptic Printing Required?) |
| extra_info_1 | VARCHAR2 | 80 | N | Value for extra info 1; → PATIENT_XTRA_INFO.description |
| extra_info_2_type through extra_info_10_type | VARCHAR2 | 80 | N | Additional extra information types (× 9 more pairs) |
| extra_info_2 through extra_info_10 | VARCHAR2 | 80 | N | Values for extra info 2–10 |

#### 5.4.6 Notes

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| comments | VARCHAR2 | 2000 | N | General patient comments |
| note_1_subject | VARCHAR2 | 80 | N | Note 1 subject heading |
| note_1_text | VARCHAR2 | 2000 | N | Note 1 free text |
| note_2_subject | VARCHAR2 | 80 | N | Note 2 subject heading |
| note_2_text | VARCHAR2 | 2000 | N | Note 2 free text |

#### 5.4.7 Next of Kin

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| nok_relationship | VARCHAR2 | 80 | N | Next of kin relationship |
| nok_title | VARCHAR2 | 80 | N | NOK title |
| nok_name_1 | VARCHAR2 | 40 | N | NOK given name |
| nok_name_family | VARCHAR2 | 40 | N | NOK family name |
| nok_address_1 | VARCHAR2 | 80 | N | NOK address line 1 |
| nok_address_2 | VARCHAR2 | 80 | N | NOK address line 2 |
| nok_address_3 | VARCHAR2 | 80 | N | NOK address line 3 |
| nok_address_4 | VARCHAR2 | 80 | N | NOK address line 4 |
| nok_post_code | VARCHAR2 | 20 | N | NOK postcode |
| nok_telephone_1 | VARCHAR2 | 20 | N | NOK phone 1 |
| nok_telephone_2 | VARCHAR2 | 20 | N | NOK phone 2 |
| nok_comments | VARCHAR2 | 2000 | N | NOK comments |
| pat_permission_to_copy_gp | VARCHAR2 | 1 | N | Y or N — permission to copy correspondence to GP |

#### 5.4.8 GP Registration

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| gp_national_code | VARCHAR2 | 10 | N | GP ODS national code; → GP_MASTER.registration_code |
| practice_national_code | VARCHAR2 | 10 | N | GP practice national code; → GP_PRACTICE_MASTER.gp_practice_code |
| practice_post_code | VARCHAR2 | 20 | N | GP practice postcode |
| practice_applies_from | DATE | 10 | N | Date GP registration applies from |
| gdp_national_code | VARCHAR2 | 10 | N | Dentist (GDP) national code |
| gdp_practice_national_code | VARCHAR2 | 10 | N | Dentist practice national code |
| gdp_practice_post_code | VARCHAR2 | 20 | N | Dentist practice postcode |
| gdp_practice_applies_from | DATE | 10 | N | Date GDP registration applies from |

---

### 5.5 LOAD_PMIIDS — Additional Patient Identifiers
**Page:** 26 | **Fields:** 7
**FK:** `loadpmi_record_number` → LOAD_PMI.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadpmi_record_number | NUMBER | 42 | N | FK to LOAD_PMI |
| system_code | NUMBER | — | N | *Parse artefact in raw — is VARCHAR2 10* |
| external_system_id | VARCHAR2 | 100 | N | Source patient ID |
| main_crnload_pmi | VARCHAR2 | 30 | N | Main CRN from LOAD_PMI (join key) |
| additional_id_type | VARCHAR2 | 80 | N | Type of additional identifier (e.g. District Number, NHS Number historic) |
| additional_id | VARCHAR2 | 30 | N | Identifier value |
| volume | NUMBER | — | N | *Parse artefact — likely volume/sequence number* |

---

### 5.6 LOAD_PMIALIASES — Patient Name Aliases
**Page:** 27 | **Fields:** 10
**FK:** `loadpmi_record_number` → LOAD_PMI.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadpmi_record_number | NUMBER | 42 | N | FK to LOAD_PMI |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source patient ID |
| main_crnload_pmi | VARCHAR2 | 30 | N | Main CRN join key |
| sex | VARCHAR2 | 80 | N | Sex code for this alias (maps to code type 3) |
| title | VARCHAR2 | 80 | N | Title for alias name (code type 29) |
| pat_name_1 | VARCHAR2 | 40 | N | Alias given name 1 |
| pat_name_2 | VARCHAR2 | 40 | N | Alias given name 2 |
| pat_name_3 | VARCHAR2 | 40 | N | Alias given name 3 |
| pat_name_family | VARCHAR2 | 40 | N | Alias family name |

---

### 5.7 LOAD_PMIADDRS — Patient Address History
**Pages:** 28–29 | **Fields:** 19
**FK:** `loadpmi_record_number` → LOAD_PMI.record_number
**Note:** Requires DOB cross-join from PATDATA (not in ADTLADDCOR)

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| of_birth | DATE | 10 | Y | Patient date of birth — required for address history (cross-join from PATDATA) |
| marital_code | VARCHAR2 | 80 | N | Marital status at this address period |
| applies_start | DATE | 10 | Y | Address record applies from (DD/MM/YYYY) |
| applies_end | DATE | 10 | Y | Address record applies to (DD/MM/YYYY) |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadpmi_record_number | NUMBER | 42 | N | FK to LOAD_PMI |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source patient ID |
| main_crnload_pmi | VARCHAR2 | 30 | N | Main CRN join key |
| address_type | VARCHAR2 | 1 | N | Address type code (only specific types accepted) |
| address_1 | VARCHAR2 | 80 | N | Address line 1 |
| address_2 | VARCHAR2 | 80 | N | Address line 2 |
| address_3 | VARCHAR2 | 80 | N | Address line 3 |
| address_4 | VARCHAR2 | 80 | N | Address line 4 |
| post_code | VARCHAR2 | 20 | N | Postcode |
| country_code | VARCHAR2 | 80 | N | Country code (maps to code type reference) |
| phone_1 | VARCHAR2 | 20 | N | Phone 1 at this address |
| phone_2 | VARCHAR2 | 20 | N | Phone 2 at this address |
| phone_3 | VARCHAR2 | 20 | N | Phone 3 at this address |

---

### 5.8 LOAD_PMICONTACTS — Patient Contacts (NOK/Carers)
**Pages:** 30–31 | **Fields:** 23
**FK:** `loadpmi_record_number` → LOAD_PMI.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadpmi_record_number | NUMBER | 42 | N | FK to LOAD_PMI |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source patient ID |
| main_crnload_pmi | VARCHAR2 | 30 | N | Main CRN join key |
| contact_type | VARCHAR2 | 80 | N | Contact type (maps to code type — e.g. NOK, Carer) |
| relationship | VARCHAR2 | 80 | N | Relationship to patient |
| parental_responsibility | VARCHAR2 | 1 | N | Y or N — has parental responsibility |
| title | VARCHAR2 | 80 | N | Contact title |
| name_1 | VARCHAR2 | 40 | N | Contact given name |
| name_family | VARCHAR2 | 40 | N | Contact family name |
| address_1 | VARCHAR2 | 80 | N | Contact address line 1 |
| address_2 | VARCHAR2 | 80 | N | Contact address line 2 |
| address_3 | VARCHAR2 | 80 | N | Contact address line 3 |
| address_4 | VARCHAR2 | 80 | N | Contact address line 4 |
| post_code | VARCHAR2 | 20 | N | Contact postcode |
| country_code | VARCHAR2 | 80 | N | Country code |
| phone_1 | VARCHAR2 | 20 | N | Phone 1 |
| phone_2 | VARCHAR2 | 20 | N | Phone 2 |
| phone_3 | VARCHAR2 | 20 | N | Phone 3 |
| comments | VARCHAR2 | 2000 | N | Comments about this contact |
| applies_start | DATE | 10 | Y | Contact record applies from |
| applies_end | DATE | 10 | Y | Contact record applies to |

---

### 5.9 LOAD_PMIALLERGIES — Patient Allergies
**Page:** 32 | **Fields:** 9
**FK:** `loadpmi_record_number` → LOAD_PMI.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadpmi_record_number | NUMBER | 42 | N | FK to LOAD_PMI |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source patient ID |
| main_crnload_pmi | VARCHAR2 | 30 | N | Main CRN join key |
| allergy_code | VARCHAR2 | 80 | N | Allergy code (maps to code type reference) |
| allergy_comment | VARCHAR2 | 80 | N | Free text comment about allergy |
| applies_start | DATE | 10 | Y | Allergy record applies from |
| applies_end | DATE | 10 | Y | Allergy record applies to |

---

### 5.10 LOAD_PMISTAFFWARNINGS — Clinical Staff Warnings
**Page:** 33 | **Fields:** 9
**FK:** `loadpmi_record_number` → LOAD_PMI.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadpmi_record_number | NUMBER | 42 | N | FK to LOAD_PMI |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source patient ID |
| main_crnload_pmi | VARCHAR2 | 30 | N | Main CRN join key |
| warning_code | VARCHAR2 | 80 | N | Warning code (e.g. MRSA, risk factor); maps to code type reference |
| warning_comment | VARCHAR2 | 80 | N | Free text comment |
| applies_start | DATE | 10 | Y | Warning applies from |
| applies_end | DATE | 10 | Y | Warning applies to |

---

### 5.11 LOAD_PMIGPAUDIT — GP Registration Audit
**Page:** 34 | **Fields:** 7
**FK:** `loadpmi_record_number` → LOAD_PMI.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadpmi_record_number | NUMBER | 42 | N | FK to LOAD_PMI |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source patient ID |
| main_crnload_pmi | VARCHAR2 | 30 | N | Main CRN join key |
| gp_national_code | VARCHAR2 | 10 | N | GP ODS code for this registration period |
| practice_national_code | VARCHAR2 | 10 | N | GP practice code for this period |

> **Note:** `practice_post_code` and `applies_start`/`applies_end` appear in the raw catalog under LOAD_CASENOTELOCS (PDF boundary bleed). They logically belong to LOAD_PMIGPAUDIT.

---

### 5.12 LOAD_CASENOTELOCS — Case Note Locations
**Pages:** 35–36 | **Fields:** 12
**Note:** Reference data table — case note storage locations per hospital

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| practice_post_code | VARCHAR2 | 20 | N | *Bleed from LOAD_PMIGPAUDIT — actually GP practice postcode for audit* |
| applies_start | DATE | 10 | N | Location applies from |
| applies_end | DATE | 10 | N | Location applies to |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source identifier |
| hospital_code | VARCHAR2 | 30 | N | Hospital code for this location |
| site | VARCHAR2 | 80 | N | Hospital site name |
| location_type | VARCHAR2 | 80 | N | Type of case note location |
| user_code | VARCHAR2 | 10 | N | Short user-facing location code |
| description | VARCHAR2 | 80 | N | Location description |
| active_flag | VARCHAR2 | 1 | N | Y/N — whether location is currently active |

---

### 5.13 LOAD_PMICASENOTEHISTORY — Patient Case Note History
**Pages:** 37–38 | **Fields:** 15
**Note:** Tracks movement history of physical case notes

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| field | DATE | — | N | **PHANTOM FIELD** — PDF parse artefact; ignore |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source patient ID |
| id_type | VARCHAR2 | 80 | N | Identifier type for this case note record |
| id_number | VARCHAR2 | 30 | N | Case note identifier number |
| volume | NUMBER | 42 | N | Case note volume number |
| hospital_code | VARCHAR2 | 30 | N | Hospital holding/sending case notes |
| site | VARCHAR2 | 80 | N | Site holding case notes |
| location_code | VARCHAR2 | 10 | N | Case note location code (from LOAD_CASENOTELOCS) |
| start_date | DATE | 10 | N | Start date case notes held at this location |
| end_date | DATE | — | N | *Parse artefact in raw — DATE* |
| short_note | VARCHAR2 | — | N | *Parse artefact in raw — should be VARCHAR2 80* |
| comment_1 | VARCHAR2 | 2000 | N | Case note comment 1 |
| comment_2 | VARCHAR2 | 2000 | N | Case note comment 2 |

---

### 5.14 LOAD_RTT_PATHWAYS — RTT Pathway Master
**Page:** 39 | **Fields:** 10
**Note:** One pathway per referral-to-treatment journey

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source system pathway identifier |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |
| pathway_id | VARCHAR2 | 20 | N | Unique pathway identifier |
| ubrn | VARCHAR2 | 20 | N | Unique Booking Reference Number (Choose & Book) |
| pathway_start_date | DATE | 10 | Y | Pathway start date (DD/MM/YYYY) |
| pathway_end_date | DATE | — | Y | Pathway end date |
| description | DATE | — | N | *Parse artefact — should be VARCHAR2 80; pathway short description* |
| pathway_coded_desc_code | VARCHAR2 | 80 | N | Coded pathway description (maps to code type reference) |

---

### 5.15 LOAD_REFERRALS — Referral Records
**Pages:** 40–43 | **Fields:** 30
**FK:** `loadrttpwy_record_number` → LOAD_RTT_PATHWAYS.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| pathway_end_event | VARCHAR2 | 80 | N | The event that ended the pathway |
| pathway_specialty | VARCHAR2 | 80 | N | Specialty of the pathway |
| pathway_status | VARCHAR2 | 80 | N | Status of the RTT pathway |
| pathway_type | VARCHAR2 | 50 | N | Pathway type (e.g. Consultant-led, No wait) |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadrttpwy_record_number | NUMBER | 42 | N | FK to LOAD_RTT_PATHWAYS |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source referral ID |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |
| patient_category | VARCHAR2 | 80 | N | Patient category (NHS/Private); maps to code type |
| first_seen | DATE | 10 | Y | Date patient first seen (DD/MM/YYYY) |
| override_wait_reset_date | DATE | — | N | Used to override the wait reset date |
| ref_new_followup_flag | DATE | — | N | *Parse artefact — should be VARCHAR2 1; N=New, F=Follow-up* |
| ref_date | DATE | 10 | Y | Referral date (DD/MM/YYYY) |
| ref_received_date | DATE | — | Y | Date referral received |
| ref_source | VARCHAR2 | 80 | N | Referral source; maps to code type |
| ref_gp_code | VARCHAR2 | 10 | N | Referring GP national code |
| ref_practice_code | VARCHAR2 | 10 | N | Referring GP practice national code |
| ref_practice_postcode | VARCHAR2 | 20 | N | Referring GP practice postcode |
| ref_urgency | VARCHAR2 | 80 | N | Referral urgency; maps to code type |
| ref_type | VARCHAR2 | 80 | N | Referral type; maps to code type |
| ref_reason | VARCHAR2 | 80 | N | Reason for referral; maps to code type |
| ref_specialty | VARCHAR2 | 80 | N | Referral specialty; maps to code type |
| ref_team | VARCHAR2 | 80 | N | Referral team; maps to code type |
| ref_consultant | VARCHAR2 | 30 | N | Referring consultant code |
| ref_outcome | VARCHAR2 | 80 | N | Referral outcome; maps to code type |
| ref_discharge_date | DATE | 10 | Y | Referral discharge date |
| ged_date | CHAR | — | N | *Parse artefact — raw merges ref_comment; should be VARCHAR2 2000; free text comment* |
| encounter_type | VARCHAR2 | 1 | Y | Encounter type (1 char) |

---

### 5.16 LOAD_RTT_PERIODS — RTT Clock Periods
**Pages:** 44–45 | **Fields:** 8
**FKs:** `loadrttpwy_record_number` → LOAD_RTT_PATHWAYS; `loadref_record_number` → LOAD_REFERRALS

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadrttpwy_record_number | NUMBER | 42 | N | FK to LOAD_RTT_PATHWAYS |
| loadref_record_number | NUMBER | — | N | FK to LOAD_REFERRALS |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source period identifier |
| clock_start | DATE | 10 | Y | RTT clock start date (DD/MM/YYYY) |
| start_event_reason_code | VARCHAR2 | 80 | N | Reason code for clock start event |
| clock_stop | DATE | 10 | Y | RTT clock stop date |
| stop_event_reason_code | VARCHAR2 | 80 | N | Reason code for clock stop event |
| breach_reason_code | VARCHAR2 | 80 | N | Coded reason for 18-week breach |
| breach_reason_text | VARCHAR2 | 500 | N | Free text breach reason |
| referral_as_start_encountery | VARCHAR2 | 1 | N | Y/N — is referral also the start encounter? |

---

### 5.17 LOAD_RTT_EVENTS — Events Within an RTT Period
**Pages:** 46–47 | **Fields:** 10
**FK:** `loadrttprd_record_number` → LOAD_RTT_PERIODS.record_number
**Note:** Contains phantom fields from PDF parsing

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadrttprd_record_number | NUMBER | 42 | N | FK to LOAD_RTT_PERIODS |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source event identifier |
| event_date | VARCHAR2 | 19 | N | Event date/time (ISO format — note: stored as VARCHAR2 not DATE) |
| event_action_code | DATE | — | N | *Parse artefact — should be VARCHAR2 80; action code for the event* |
| event_reason_code | VARCHAR2 | 80 | N | Reason code for event |
| rtt_status | VARCHAR2 | 80 | N | RTT status code at this event |
| event_text | VARCHAR2 | 80 | N | Short event description text |
| must | DATE | — | Y | **PHANTOM FIELD** — PDF artefact; ignore |
| before | DATE | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| ranges | DATE | — | N | **PHANTOM FIELD** — PDF artefact; ignore |

---

### 5.18 LOAD_OPDWAITLIST — Outpatient Waiting List
**Pages:** 48–51 | **Fields:** 27
**FKs:** `loadref_record_number` → LOAD_REFERRALS; `loadrttprd_record_number` → LOAD_RTT_PERIODS

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadref_record_number | NUMBER | 42 | N | Mandatory FK to LOAD_REFERRALS |
| rttpwy_recno_out_encounter | NUMBER | — | N | FK to LOAD_RTT_PATHWAYS (out-encounter link) |
| loadrttprd_record_number | NUMBER | 42 | N | FK to LOAD_RTT_PERIODS |
| loadrttprd_action | VARCHAR2 | 5 | N | RTT period action type (e.g. START, STOP) |
| rttevent_recno_encounter | NUMBER | 42 | N | FK to LOAD_RTT_EVENTS (encounter event) |
| rttevent_recno_outcome | NUMBER | 42 | N | FK to LOAD_RTT_EVENTS (outcome event) |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source waiting list entry ID |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |
| hospital_code | VARCHAR2 | 30 | N | Hospital code |
| site | VARCHAR2 | 80 | N | Hospital site name |
| list_code | VARCHAR2 | 10 | N | Waiting list code |
| list_name | VARCHAR2 | 80 | N | Waiting list name |
| encounter_type | VARCHAR2 | 1 | N | Encounter type code |
| specialty | VARCHAR2 | 80 | N | Specialty; maps to code type |
| new_followup_flagn | VARCHAR2 | 1 | N | N=New, F=Follow-up |
| short_notice_flag | VARCHAR2 | 1 | N | Y or N — short notice patient |
| status | VARCHAR2 | 1 | N | Waiting list status code |
| target_date | DATE | 10 | Y | Target appointment date |
| consultant | VARCHAR2 | 30 | N | Consultant code |
| outcome | VARCHAR2 | 80 | N | Outcome code |
| removed | DATE | 10 | Y | Date removed from waiting list |
| wl_comment | VARCHAR2 | 2000 | N | Waiting list comment |
| ios_usercode | VARCHAR2 | 80 | N | IOS user code |
| transport_required | VARCHAR2 | 80 | N | Transport required (deprecated field) |

---

### 5.19 LOAD_OPDWAITLISTDEF — OPD Waiting List Deferrals
**Page:** 52 | **Fields:** 8
**FK:** `loadowl_record_number` → LOAD_OPDWAITLIST.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadowl_record_number | NUMBER | 42 | N | FK to LOAD_OPDWAITLIST |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source deferral ID |
| deferral_start | DATE | 10 | Y | Deferral start date |
| deferral_end | DATE | — | Y | Deferral end date |
| deferral_reason | DATE | — | N | *Parse artefact — should be VARCHAR2 80; deferral reason code* |
| deferral_comment | VARCHAR2 | 2000 | N | Free text deferral comment |

---

### 5.20 LOAD_OPD_APPOINTMENTS — Outpatient Appointments
**Pages:** 53–56 | **Fields:** 34
**FKs:** `loadref_record_number` → LOAD_REFERRALS; `loadowl_record_number` → LOAD_OPDWAITLIST; `loadrttprd_record_number` → LOAD_RTT_PERIODS

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| must | DATE | — | Y | **PHANTOM FIELD** — PDF artefact; ignore |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadref_record_number | NUMBER | 42 | N | Mandatory FK to LOAD_REFERRALS |
| loadowl_record_number | NUMBER | — | N | FK to LOAD_OPDWAITLIST |
| rttpwy_recno_out_encounter | NUMBER | — | N | FK to LOAD_RTT_PATHWAYS (out-encounter) |
| loadrttprd_record_number | NUMBER | 42 | N | FK to LOAD_RTT_PERIODS |
| loadrttprd_action | VARCHAR2 | 5 | N | RTT period action type |
| rttevent_recno_encounter | NUMBER | 42 | N | FK to LOAD_RTT_EVENTS (encounter) |
| rttevent_recno_outcome | NUMBER | 42 | N | FK to LOAD_RTT_EVENTS (outcome) |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source appointment ID |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |
| new_followup_flag | VARCHAR2 | 1 | N | N=New, F=Follow-up |
| appt_team | VARCHAR2 | 80 | N | Appointment team code |
| appt_date | DATE | 10 | Y | Appointment date (DD/MM/YYYY) |
| booked_date | DATE | — | Y | Date appointment was booked |
| booking_type | VARCHAR2 | 80 | N | Booking type; maps to code type |
| clinic_code_1 | VARCHAR2 | 20 | N | Primary clinic code |
| clinic_code_2 | VARCHAR2 | 20 | N | Secondary clinic code |
| appt_type | VARCHAR2 | 20 | N | Appointment type code |
| consultant_in_charge | VARCHAR2 | 30 | N | Consultant responsible for the appointment |
| consultant_taking_appt | VARCHAR2 | 30 | N | Consultant who actually took the appointment |
| transport_required | VARCHAR2 | 80 | N | Transport requirement; maps to code type |
| walkin_flag | VARCHAR2 | 1 | N | Y or N — walk-in appointment |
| time_arrived | DATE | 10 | Y | Time patient arrived |
| time_seen | DATE | 10 | Y | Time patient was seen |
| time_complete | DATE | 10 | Y | Time appointment completed |
| outcome | VARCHAR2 | 80 | N | Appointment outcome; maps to code type |
| cancelled_date | DATE | 10 | Y | Date appointment cancelled |
| appt_comment | DATE | — | N | *Parse artefact — should be VARCHAR2 2000; appointment comment* |
| cab_ubrn | VARCHAR2 | 20 | N | Choose & Book UBRN |
| cab_service | VARCHAR2 | 10 | N | Choose & Book service code |
| cab_usrn | VARCHAR2 | 36 | N | Choose & Book USRN |

---

### 5.21 LOAD_OPD_CODING — OPD Clinical Coding
**Page:** 57 | **Fields:** 8
**FK:** `load_opd_record_number` → LOAD_OPD_APPOINTMENTS.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| load_opd_record_number | NUMBER | 42 | N | FK to LOAD_OPD_APPOINTMENTS |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source coding record ID |
| diagnosis_division | VARCHAR2 | 80 | N | Diagnosis coding scheme/division |
| note_type | VARCHAR2 | 80 | N | Type of coding note |
| diagnosis | VARCHAR2 | 25 | N | Diagnosis code (ICD-10 or OPCS-4) |
| diagnosis_note | VARCHAR2 | 200 | N | Free text diagnosis note |

---

### 5.22 LOAD_CMTY_APPOINTMENTS — Community Care Appointments
**Pages:** 58–62 | **Fields:** 48
**FKs:** `loadowl_record_number` → LOAD_OPDWAITLIST; `loadrttpwy_record_number` → LOAD_RTT_PATHWAYS; `loadrttprd_record_number` → LOAD_RTT_PERIODS

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| diagnosed_by | VARCHAR2 | 30 | N | Clinician who made the diagnosis |
| diagnosis_date | DATE | 10 | Y | Date of diagnosis |
| must | DATE | — | Y | **PHANTOM FIELD** — PDF artefact; ignore |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadowl_record_number | NUMBER | 42 | N | FK to LOAD_OPDWAITLIST |
| loadrttpwy_record_number | NUMBER | — | N | FK to LOAD_RTT_PATHWAYS |
| loadrttprd_record_number | NUMBER | — | N | FK to LOAD_RTT_PERIODS |
| loadrttprd_action | NUMBER | — | N | *Parse artefact — should be VARCHAR2 20* |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source appointment ID |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |
| patient_category | VARCHAR2 | 80 | N | Patient category; maps to code type |
| first_seen | DATE | 10 | Y | Date patient first seen |
| override_wait_reset_date | DATE | — | N | Override wait reset date |
| ref_new_followup_flag | DATE | — | N | *Parse artefact — should be VARCHAR2 1* |
| ref_date | DATE | 10 | Y | Referral date |
| appointments | DATE | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| ref_received_date | DATE | — | Y | Date referral received |
| ref_source | VARCHAR2 | 80 | N | Referral source; maps to code type |
| ref_gp_code | VARCHAR2 | 10 | N | Referring GP national code |
| ref_practice_code | VARCHAR2 | 10 | N | Referring practice national code |
| ref_practice_postcode | VARCHAR2 | 20 | N | Referring practice postcode |
| ref_urgency | VARCHAR2 | 80 | N | Referral urgency |
| ref_type | VARCHAR2 | 80 | N | Referral type |
| ref_reason | VARCHAR2 | 80 | N | Reason for referral |
| ref_specialty | VARCHAR2 | 80 | N | Referral specialty |
| ref_team | VARCHAR2 | 80 | N | Referral team |
| ref_consultant | VARCHAR2 | 30 | N | Referring consultant |
| ref_outcome | VARCHAR2 | 80 | N | Referral outcome |
| ref_discharge_date | DATE | 10 | Y | Referral discharge date |
| ged_date | CHAR | — | Y | *Parse artefact — merges appt_date; should be DATE 10; appointment date* |
| booked_date | DATE | — | Y | Date appointment booked |
| booking_type | VARCHAR2 | 80 | N | Booking type; maps to code type |
| clinic_code_1 | VARCHAR2 | 20 | N | Primary clinic code |
| clinic_code_2 | VARCHAR2 | 20 | N | Secondary clinic code |
| appt_type | VARCHAR2 | 20 | N | Appointment type |
| consultant_code | VARCHAR2 | 30 | N | Consultant code |
| transport_required | VARCHAR2 | 80 | N | Transport requirement |
| walkin_flag | VARCHAR2 | 1 | N | Y or N — walk-in |
| time_arrived | DATE | 10 | Y | Time patient arrived |
| time_seen | DATE | 10 | Y | Time patient seen |
| time_complete | DATE | 10 | Y | Time appointment completed |
| outcome | VARCHAR2 | 80 | N | Appointment outcome |
| ged | CHAR | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| cancelled_date | DATE | 10 | Y | Cancellation date |
| ref_comment | DATE | — | N | *Parse artefact — should be VARCHAR2 2000; referral comment* |
| appt_comment | VARCHAR2 | 2000 | N | Appointment comment |

---

### 5.23 LOAD_IWL_PROFILES — Inpatient Waiting List Profiles
**Pages:** 63–64 | **Fields:** 12
**Note:** Reference data — defines standard waiting list configurations

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source profile ID |
| waitlist_profile | VARCHAR2 | 15 | N | Short profile code |
| description | VARCHAR2 | 40 | N | Profile description |
| list_no | VARCHAR2 | 2 | N | Consultant list number |
| consultant_code | VARCHAR2 | 30 | N | Consultant code for this profile |
| treatment_type | VARCHAR2 | 1 | N | Treatment type code |
| admit_type | VARCHAR2 | 1 | N | Admission type code |
| max_wait_months | NUMBER | 42 | N | Maximum wait time in months |
| avg_length_stay | NUMBER | 42 | N | Average length of stay (days) |
| admit_duration_hours | NUMBER | 42 | N | Admission duration in hours |
| operation_duration_mins | NUMBER | 42 | N | Operation duration in minutes |

---

### 5.24 LOAD_IWL — Inpatient Waiting List
**Pages:** 65–68 | **Fields:** 33
**FKs:** `loadref_record_number` → LOAD_REFERRALS; `loadrttprd_record_number` → LOAD_RTT_PERIODS

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadref_record_number | NUMBER | 42 | N | Mandatory FK to LOAD_REFERRALS |
| rttpwy_recno_out_encounter | NUMBER | — | N | FK to LOAD_RTT_PATHWAYS (out-encounter) |
| loadrttprd_record_number | NUMBER | 42 | N | FK to LOAD_RTT_PERIODS |
| loadrttprd_action | VARCHAR2 | 5 | N | RTT period action type |
| rttevent_recno_encounter | NUMBER | 42 | N | FK to LOAD_RTT_EVENTS (encounter) |
| rttevent_recno_outcome | NUMBER | 42 | N | FK to LOAD_RTT_EVENTS (outcome) |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source waiting list entry ID |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |
| waitlist_date | DATE | 10 | Y | Date placed on waiting list |
| urgency | VARCHAR2 | 80 | N | Urgency; maps to code type |
| short_notice_flag | VARCHAR2 | 1 | N | Y or N — short notice patient |
| status | VARCHAR2 | 1 | N | Waiting list status |
| waitlist_type | VARCHAR2 | 80 | N | Waiting list type; maps to code type |
| waitlist_profile | VARCHAR2 | 15 | N | Profile code (from LOAD_IWL_PROFILES) |
| site_code | VARCHAR2 | 80 | N | Hospital site code |
| specialty | VARCHAR2 | 80 | N | Specialty; maps to code type |
| consultant_code | VARCHAR2 | 30 | N | Consultant code |
| intended_management | VARCHAR2 | 80 | N | Intended management type |
| transport_required | VARCHAR2 | 80 | N | Transport requirement |
| provisional_diagnosis | VARCHAR2 | 80 | N | Provisional diagnosis (free text) |
| provisional_procedure | VARCHAR2 | 200 | N | Provisional procedure (free text) |
| intended_procedure_code | VARCHAR2 | 25 | N | Intended procedure OPCS-4 code 1 |
| intended_procedure_code2 | VARCHAR2 | 25 | N | Intended procedure OPCS-4 code 2 |
| est_theatre_time | NUMBER | 42 | N | Estimated theatre time (minutes) |
| admission_duration | NUMBER | 42 | N | Expected admission duration (days) |
| last_review_date | DATE | 10 | Y | Last waiting list review date |
| last_review_response | DATE | — | N | *Parse artefact — should be VARCHAR2 80; last review response code* |
| wl_outcome | VARCHAR2 | 80 | N | Waiting list outcome code |
| removed | DATE | 10 | Y | Date removed from waiting list |
| wl_entry_comment | VARCHAR2 | 2000 | N | Waiting list entry comment |

---

### 5.25 LOAD_IWL_DEFERRALS — Inpatient Waiting List Deferrals/Suspensions
**Pages:** 69–70 | **Fields:** 9
**FK:** `loadiwl_record_number` → LOAD_IWL.record_number
**Note:** PDF boundary confusion — some fields appear under LOAD_IWL_TCIS in catalog

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| admission_reason_comment | VARCHAR2 | 2000 | N | Admission reason comment |
| operation_text | VARCHAR2 | 2000 | N | Operation description text |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadiwl_record_number | NUMBER | 42 | N | FK to LOAD_IWL |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source deferral ID |
| deferral_start | DATE | 10 | Y | Deferral/suspension start date |
| deferral_end | DATE | 10 | Y | Deferral/suspension end date |
| deferral_reason | VARCHAR2 | 80 | N | Deferral reason code |
| deferral_comment | VARCHAR2 | 2000 | N | Free text deferral comment |

---

### 5.26 LOAD_IWL_TCIS — Inpatient TCI (To Come In) Bookings
**Pages:** 70–71 | **Fields:** 18
**FK:** `loadiwl_record_number` → LOAD_IWL.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadiwl_record_number | NUMBER | 42 | N | FK to LOAD_IWL |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source TCI record ID |
| status | VARCHAR2 | 1 | N | TCI status code |
| booking_type | VARCHAR2 | 80 | N | Booking type; maps to code type |
| consultant_code | VARCHAR2 | 30 | N | Consultant code for TCI |
| offer_date | DATE | 10 | Y | Date TCI was offered |
| agreed_date | DATE | — | Y | Date patient agreed to TCI |
| agreed_flag | DATE | — | N | *Parse artefact — should be VARCHAR2 1; Y/N patient agreed flag* |
| preassessment_date | DATE | 10 | Y | Pre-assessment date |
| tci_date | DATE | — | Y | TCI admission date |
| operation_date | DATE | — | Y | Operation/procedure date |
| estimated_discharge_date | DATE | — | Y | Estimated discharge date |
| ge_date | CHAR | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| deferral_end | DATE | 10 | Y | *Catalog boundary bleed from LOAD_IWL_DEFERRALS* |
| deferral_reason | VARCHAR2 | 80 | N | *Catalog boundary bleed* |
| deferral_comment | VARCHAR2 | 2000 | N | *Catalog boundary bleed* |

---

### 5.27 LOAD_ADT_ADMISSIONS — Inpatient Admissions
**Pages:** 72–74 | **Fields:** 25
**FK:** `loadiwl_record_number` → LOAD_IWL.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| ward | VARCHAR2 | 80 | N | Admitting ward; maps to code type |
| tci_outcome | VARCHAR2 | 80 | N | TCI outcome code |
| cancelled_date | DATE | 10 | Y | Date admission cancelled |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| loadiwl_record_number | NUMBER | 42 | N | FK to LOAD_IWL |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source admission ID |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |
| ref_gp_code | VARCHAR2 | 10 | N | Referring GP national code |
| ref_practice_code | VARCHAR2 | 10 | N | Referring practice national code |
| ref_practice_postcode | VARCHAR2 | 20 | N | Referring practice postcode |
| intended_management | VARCHAR2 | 80 | N | Intended management; maps to code type |
| wl_date | DATE | 10 | Y | Date placed on waiting list |
| admit_date | DATE | 10 | Y | Admission date |
| estimated_discharge_date | DATE | — | Y | Estimated discharge date |
| ge_date | CHAR | — | N | *Parse artefact — merges admission_type; should be VARCHAR2 80* |
| admit_from | VARCHAR2 | 80 | N | Source of admission; maps to code type |
| admitted_by | VARCHAR2 | 30 | N | Admitting clinician code |
| discharge_date | DATE | 10 | Y | Discharge date |
| ge_typee | CHAR | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| ged | CHAR | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| ge_toe | CHAR | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| discharged_by | VARCHAR2 | 30 | N | Discharging clinician code |
| ged_by_staff_id | CHAR | — | N | *Parse artefact — merges admission_outcome; should be VARCHAR2 80* |

---

### 5.28 LOAD_ADT_EPISODES — Consultant Episodes
**Page:** 75 | **Fields:** 8
**FK:** `adt_adm_record_number` → LOAD_ADT_ADMISSIONS.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| indicates | DATE | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| must | DATE | — | Y | **PHANTOM FIELD** — PDF artefact; ignore |
| ge_date | CHAR | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| adt_adm_record_number | NUMBER | 42 | N | FK to LOAD_ADT_ADMISSIONS |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source episode ID |
| patient_category | VARCHAR2 | 80 | N | Patient category; maps to code type |
| actual_management | VARCHAR2 | 80 | N | Actual management type; maps to code type |

---

### 5.29 LOAD_ADT_WARDSTAYS — Ward Stay Records
**Pages:** 76–77 | **Fields:** 18
**FK:** `adt_eps_record_number` → LOAD_ADT_EPISODES.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| specialty | VARCHAR2 | 80 | N | Specialty at this ward stay |
| consultant_code | VARCHAR2 | 30 | N | Consultant code |
| start_date | DATE | 10 | Y | Ward stay start date |
| end_date | DATE | — | Y | Ward stay end date |
| table | DATE | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| indicates | DATE | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| adt_eps_record_number | NUMBER | 42 | N | FK to LOAD_ADT_EPISODES |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source ward stay ID |
| team | VARCHAR2 | 80 | N | Clinical team; maps to code type |
| ward | VARCHAR2 | 80 | N | Ward code; maps to code type |
| bed_sex | VARCHAR2 | 1 | N | Sex of bed allocation (M/F/U) |
| bed_location | VARCHAR2 | 15 | N | Bed location code |
| is_home_stay | VARCHAR2 | 1 | N | Y or N — home stay (MH) |
| is_awol | VARCHAR2 | 1 | N | Y or N — absent without leave (MH) |
| leave_location_code | VARCHAR2 | 80 | N | Leave location; maps to code type |
| transfer_reason | VARCHAR2 | 80 | N | Ward transfer reason; maps to code type |

---

### 5.30 LOAD_ADT_CODING — Inpatient Clinical Coding
**Page:** 78 | **Fields:** 8
**FK:** `adt_eps_record_number` → LOAD_ADT_EPISODES.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| adt_eps_record_number | NUMBER | 42 | N | FK to LOAD_ADT_EPISODES |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source coding record ID |
| diagnosis_division | VARCHAR2 | 80 | N | Coding scheme/division (ICD-10 / OPCS-4) |
| note_type | VARCHAR2 | 80 | N | Type of coding note |
| diagnosis | VARCHAR2 | 25 | N | Diagnosis/procedure code |
| diagnosis_note | VARCHAR2 | 200 | N | Free text diagnosis note |

---

### 5.31 LOAD_MH_DETENTION_MASTER — Mental Health Detention Records
**Pages:** 79–80 | **Fields:** 9
**FK:** `adt_adm_record_number` → LOAD_ADT_ADMISSIONS.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| diagnosis_note | VARCHAR2 | 200 | N | Diagnosis free text note |
| diagnosed_by | VARCHAR2 | 30 | N | Clinician who diagnosed |
| diagnosis_date | DATE | 10 | Y | Date of diagnosis (MHA section date) |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| adt_adm_record_number | NUMBER | 42 | N | FK to LOAD_ADT_ADMISSIONS |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source detention record ID |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |

---

### 5.32 LOAD_MH_DETENTION_TRANSFERS — Mental Health Detention Transfers
**Pages:** 80–81 | **Fields:** 17
**FK:** `mh_dm_record_number` → LOAD_MH_DETENTION_MASTER.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| start_date | DATE | 10 | Y | Transfer/section start date |
| end_date | DATE | — | Y | Transfer/section end date |
| expiry_date | DATE | — | Y | Section expiry date |
| table | DATE | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| mh_dm_record_number | NUMBER | 42 | N | FK to LOAD_MH_DETENTION_MASTER |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source transfer record ID |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |
| institution | DATE | — | N | *Parse artefact — should be VARCHAR2 80; institution/hospital code* |
| legal_status | VARCHAR2 | 80 | N | Legal/MHA section status; maps to code type |
| mental_category | VARCHAR2 | 80 | N | Mental health category; maps to code type |
| caseholder | VARCHAR2 | 30 | N | Caseholder clinician code |
| section_review_date | DATE | 10 | Y | Section review date |
| consent_reminder_date | DATE | — | Y | Consent reminder date |
| consent_due_date | DATE | — | Y | Consent due date |

---

### 5.33 LOAD_MH_CPA_MASTER — Care Programme Approach Master
**Page:** 82 | **Fields:** 9

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| system_code | VARCHAR2 | 10 | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source CPA record ID |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |
| cpa_type | VARCHAR2 | 80 | N | CPA type; maps to code type |
| key_worker_staff_id | VARCHAR2 | 30 | N | Key worker staff ID |
| care_coordinator | VARCHAR2 | 30 | N | Care coordinator ID |
| applies_start | DATE | 10 | Y | CPA applies from |

---

### 5.34 LOAD_MH_CPA_HISTORY — CPA History Records
**Page:** 83 | **Fields:** 12
**FK:** `mh_cm_record_number` → LOAD_MH_CPA_MASTER.record_number

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| applies_end | DATE | 10 | Y | CPA period applies to |
| next_review_date | DATE | 10 | Y | Next CPA review date |
| table | DATE | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| record_number | NUMBER | 42 | N | Unique ETL row identifier |
| mh_cm_record_number | NUMBER | 42 | N | FK to LOAD_MH_CPA_MASTER |
| system_code | NUMBER | — | N | Source system code |
| external_system_id | VARCHAR2 | 100 | N | Source history record ID |
| main_crn_type | VARCHAR2 | 80 | N | Patient ID type |
| main_crn | VARCHAR2 | 30 | N | Patient identifier |
| cpa_type | VARCHAR2 | 80 | N | CPA type for this period |
| key_worker_staff_id | VARCHAR2 | 30 | N | Key worker for this period |
| care_coordinator | VARCHAR2 | 30 | N | Care coordinator for this period |

---

### 5.35 LOAD_OPD_ARCHIVE — Outpatient Archive
**Pages:** 84–90 | **Fields:** 81
**Note:** Self-contained archive table — not linked to live LOAD_OPD_APPOINTMENTS. Loaded independently. Contains all patient demographic snapshot at time of attendance.

#### 5.35.1 Patient Snapshot

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| crn | VARCHAR2 | 30 | N | Patient CRN at time of archive |
| of_birth | DATE | 10 | Y | Date of birth |
| sex | VARCHAR2 | 1 | N | Sex code (1 char) |
| pat_name_1 | VARCHAR2 | 40 | N | Patient given name |
| pat_name_family | VARCHAR2 | 40 | N | Patient family name |
| address_1–5 | VARCHAR2 | 80 | N | Patient address lines 1–5 (5 fields) |
| post_code | VARCHAR2 | 20 | N | Postcode |
| district | VARCHAR2 | 10 | N | District code |
| pct_codepct | VARCHAR2 | 20 | N | PCT code |

#### 5.35.2 Commissioning & Referral

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| contract_number | VARCHAR2 | 30 | N | Contract number |
| purchaser_ref | NUMBER | — | N | Purchaser reference |
| provider_code | VARCHAR2 | 30 | N | Provider code |
| purchaser_code | VARCHAR2 | 30 | N | Purchaser code |
| ref_source | VARCHAR2 | 80 | N | Referral source |
| gp_registration_codegp | VARCHAR2 | 10 | N | GP registration code |
| gp_namegp | VARCHAR2 | 80 | N | GP name |
| gp_fundholder_codegp | VARCHAR2 | 10 | N | GP fund holder code |
| gp_practice_code | VARCHAR2 | 10 | N | GP practice code |
| practice_name | VARCHAR2 | 80 | N | GP practice name |
| referral_request_date | DATE | 10 | Y | Referral request date |
| referral_reason | DATE | — | N | *Parse artefact — should be VARCHAR2 80* |
| referring_consultant_gmc | VARCHAR2 | 10 | N | Referring consultant GMC code |
| referring_consultant_name | VARCHAR2 | 80 | N | Referring consultant name |

#### 5.35.3 Referral Dates

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| first_attendance | DATE | 10 | N | Date of first attendance |
| referral_discharge_date | DATE | 10 | Y | Referral discharge date |
| ge_date | CHAR | — | N | *Parse artefact — merges referral_discharge_status; should be VARCHAR2 80* |
| ge_status | CHAR | — | N | *Parse artefact — merges hospital_name; should be VARCHAR2 80* |
| encounter_type | VARCHAR2 | 1 | Y | Encounter type code |

#### 5.35.4 Clinic & Clinician

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| clinic_name | VARCHAR2 | 80 | N | Clinic name |
| specialty | VARCHAR2 | 80 | N | Specialty |
| consultant_team | VARCHAR2 | 80 | N | Consultant team |
| consultant_gmc | VARCHAR2 | 10 | N | Consultant GMC code |
| consultant_name | VARCHAR2 | 80 | N | Consultant name |
| transport | VARCHAR2 | 80 | N | Transport details |

#### 5.35.5 Appointment Details

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| appointment_priority | VARCHAR2 | 80 | N | Appointment priority |
| appointment_purpose | VARCHAR2 | 80 | N | Appointment purpose |
| appointment_status | VARCHAR2 | 80 | N | Appointment status |
| appointment_date | DATE | 10 | Y | Appointment date |
| appointment_time | DATE | — | Y | *Parse artefact — should be VARCHAR2 5; HH:MM format* |
| walkin_flag | VARCHAR2 | 1 | N | Y or N — walk-in |
| forced_booking_flag | VARCHAR2 | 1 | N | Y or N — forced booking |
| booked | DATE | 10 | N | Date booked |
| booking_type | VARCHAR2 | 80 | N | Booking type |
| appointment_type | VARCHAR2 | 80 | N | Appointment type |
| time_arrived | VARCHAR2 | 5 | Y | Time arrived (HH:MM — stored as VARCHAR2) |
| time_seen | VARCHAR2 | 5 | Y | Time seen (HH:MM) |
| time_completed | VARCHAR2 | 5 | Y | Time completed (HH:MM) |
| outcome | VARCHAR2 | 80 | N | Appointment outcome |
| cancelled_date | DATE | 10 | Y | Cancellation date |
| cancelled_by | DATE | — | N | *Parse artefact — should be VARCHAR2 30* |
| cancellation_reason | VARCHAR2 | 80 | N | Cancellation reason |

#### 5.35.6 Clinical Coding (Procedures × 10)

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| procedure_scheme | VARCHAR2 | 30 | N | Procedure coding scheme (OPCS-4) |
| primary_procedure_code | VARCHAR2 | 25 | N | Primary procedure code |
| primary_procedure_desc | VARCHAR2 | 200 | N | Primary procedure description |
| procedure_1_code through procedure_10_code | VARCHAR2 | 25 | N | Additional procedure codes 1–10 (10 fields) |
| procedure_1_desc through procedure_10_desc | VARCHAR2 | 200 | N | Additional procedure descriptions 1–10 (10 fields) |

---

### 5.36 LOAD_ADT_ARCHIVE — Inpatient Archive
**Pages:** 91–99 | **Fields:** 92
**Note:** Largest target table (92 fields). Self-contained archive for inpatient admissions. Loaded independently.

#### 5.36.1 Patient Snapshot

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| encounter_type | VARCHAR2 | 1 | Y | Encounter type code |
| crn | VARCHAR2 | 30 | N | Patient CRN |
| of_birth | DATE | 10 | Y | Date of birth |
| sex | VARCHAR2 | 1 | N | Sex code |
| pat_name_1 | VARCHAR2 | 40 | N | Given name |
| pat_name_family | VARCHAR2 | 40 | N | Family name |
| address_1–5 | VARCHAR2 | 80 | N | Address lines 1–5 |
| post_code | VARCHAR2 | 20 | N | Postcode |
| district | VARCHAR2 | 10 | N | District code |
| pct_codepct | VARCHAR2 | 20 | N | PCT code |

#### 5.36.2 Commissioning

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| contract_number | VARCHAR2 | 30 | N | Contract number |
| purchaser_ref | NUMBER | — | N | Purchaser reference |
| provider_code | VARCHAR2 | 30 | N | Provider code |
| purchaser_code | VARCHAR2 | 30 | N | Purchaser code |
| waiting_list_name | VARCHAR2 | 80 | N | Name of source waiting list |
| decided_to_admit_date | DATE | 10 | Y | Date decision to admit made |
| inpatient_wait_days | DATE | — | N | *Parse artefact — should be NUMBER 42; days waited* |
| operation_date | DATE | 10 | Y | Operation date |

#### 5.36.3 Referral Source

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| ref_source | VARCHAR2 | 80 | N | Referral source |
| gp_registration_codegp | VARCHAR2 | 10 | N | GP registration code |
| gp_namegp | VARCHAR2 | 80 | N | GP name |
| gp_fundholder_codegp | VARCHAR2 | 10 | N | GP fund holder code |
| gp_practice_code | VARCHAR2 | 10 | N | GP practice code |
| practice_name | VARCHAR2 | 80 | N | GP practice name |
| patient_category | VARCHAR2 | 80 | N | Patient category |
| intended_management | VARCHAR2 | 80 | N | Intended management |

#### 5.36.4 Admission & Discharge

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| admit_date | DATE | 10 | Y | Admission date |
| est_discharge_date | DATE | — | Y | Estimated discharge date |
| ge_date | CHAR | — | Y | *Parse artefact — merges physical_discharge_date; should be DATE 10* |
| admitting_specialty | VARCHAR2 | 80 | N | Admitting specialty |
| admitting_consultant_gmc | VARCHAR2 | 60 | N | Admitting consultant GMC code |
| admitting_consultant_name | VARCHAR2 | 80 | N | Admitting consultant name |
| discharge_method | VARCHAR2 | 80 | N | Method of discharge |
| ge_methode | CHAR | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| ged | CHAR | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| ge_toe | CHAR | — | N | **PHANTOM FIELD** — PDF artefact; ignore |
| discharging_specialty | VARCHAR2 | 80 | N | Discharging specialty |
| ge_specialty | CHAR | — | N | *Parse artefact — merges discharging_consultant_gmc; VARCHAR2 10* |
| ge_consultant | CHAR | — | N | *Parse artefact — merges discharging_consultant_name; VARCHAR2 80* |
| admission_outcome | VARCHAR2 | 80 | N | Admission outcome |
| episode_order | VARCHAR2 | 5 | N | Episode order within admission |

#### 5.36.5 Episode Detail

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| age_at_start_of_episode | NUMBER | 42 | N | Patient age at episode start |
| episode_start | DATE | 10 | Y | Episode start date |
| episode_end | DATE | 10 | Y | Episode end date |
| duration_of_episode | NUMBER | 42 | N | Episode duration (days) |
| specialty | VARCHAR2 | 80 | N | Episode specialty |
| consultant_gmc | VARCHAR2 | 10 | N | Episode consultant GMC code |
| consultant_name | VARCHAR2 | 80 | N | Episode consultant name |
| ward_name | VARCHAR2 | 80 | N | Ward name |

#### 5.36.6 Clinical Coding (Diagnoses × 10 + Procedures × 10)

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| diagnosis_scheme | VARCHAR2 | 30 | N | Diagnosis coding scheme (ICD-10) |
| primary_diagnosis_code | VARCHAR2 | 25 | N | Primary ICD-10 diagnosis code |
| primary_diagnosis_desc | VARCHAR2 | 200 | N | Primary diagnosis description |
| diagnosis_1_code | VARCHAR2 | 25 | N | Secondary diagnosis code 1 |
| diagnosis | VARCHAR2 | 200 | N | *Parse artefact — should be diagnosis_1_desc; VARCHAR2 200* |
| diagnosis_2_code through diagnosis_10_code | VARCHAR2 | 25 | N | Diagnosis codes 2–10 (9 fields) |
| procedure_scheme | VARCHAR2 | 30 | N | Procedure coding scheme (OPCS-4) |
| primary_procedure_code | VARCHAR2 | 25 | N | Primary OPCS-4 procedure code |
| primary_procedure_desc | VARCHAR2 | 200 | N | Primary procedure description |
| procedure_1_code through procedure_10_code | VARCHAR2 | 25 | N | Additional procedure codes 1–10 |
| procedure_1_desc through procedure_10_desc | VARCHAR2 | 200 | N | Additional procedure descriptions 1–10 |
| hrghrg | VARCHAR2 | 10 | N | HRG code |
| comments | VARCHAR2 | 2000 | N | General admission comments |
| procedure_10_desc | VARCHAR2 | 200 | N | Procedure 10 description (boundary bleed) |

---

### 5.37 LOAD_DETENTION_ARCHIVE — Mental Health Detention Archive
**Pages:** 100–101 | **Fields:** 18
**Note:** Self-contained archive. Loaded independently.

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| crn | VARCHAR2 | 30 | N | Patient CRN |
| of_birth | DATE | 10 | Y | Date of birth |
| sex | VARCHAR2 | 1 | N | Sex code |
| pat_name_1 | VARCHAR2 | 40 | N | Given name |
| pat_name_family | VARCHAR2 | 40 | N | Family name |
| address_1 | VARCHAR2 | 80 | N | Address line 1 |
| address_2 | VARCHAR2 | 80 | N | Address line 2 |
| address_3 | VARCHAR2 | 80 | N | Address line 3 |
| address_4 | VARCHAR2 | 80 | N | Address line 4 |
| address_5 | VARCHAR2 | 80 | N | Address line 5 |
| post_code | VARCHAR2 | 20 | N | Postcode |
| detention_start | DATE | 10 | Y | Detention start date (MHA section start) |
| detention_end | DATE | 10 | Y | Detention end date |
| detention_location | VARCHAR2 | 80 | N | Location of detention (hospital/unit) |
| caseholder | VARCHAR2 | 80 | N | Caseholder clinician |
| mental_category | VARCHAR2 | 80 | N | Mental health category (MHA section type) |
| legal_status | VARCHAR2 | 80 | N | Legal status / MHA section code |
| detention_notes | VARCHAR2 | 2000 | N | Free text detention notes |

---

### 5.38 LOAD_CPA_ARCHIVE — Care Programme Approach Archive
**Pages:** 102–103 | **Fields:** 17
**Note:** Self-contained archive. Loaded independently.

| Field | Type | Len | Mand | Description |
|-------|------|-----|------|-------------|
| crn | VARCHAR2 | 30 | N | Patient CRN |
| of_birth | DATE | 10 | Y | Date of birth |
| sex | VARCHAR2 | 1 | N | Sex code |
| pat_name_1 | VARCHAR2 | 40 | N | Given name |
| pat_name_family | VARCHAR2 | 40 | N | Family name |
| address_1 | VARCHAR2 | 80 | N | Address line 1 |
| address_2 | VARCHAR2 | 80 | N | Address line 2 |
| address_3 | VARCHAR2 | 80 | N | Address line 3 |
| address_4 | VARCHAR2 | 80 | N | Address line 4 |
| address_5 | VARCHAR2 | 80 | N | Address line 5 |
| post_code | VARCHAR2 | 20 | N | Postcode |
| cpa_start | DATE | 10 | Y | CPA start date |
| cpa_end | DATE | 10 | Y | CPA end date |
| cpa_type | VARCHAR2 | 80 | N | CPA type (Standard/Enhanced) |
| key_worker | VARCHAR2 | 80 | N | Key worker name/code |
| care_coordinator | VARCHAR2 | 80 | N | Care coordinator name/code |
| cpa_notescpa | VARCHAR2 | 2000 | N | CPA notes |

---

## 6. Data Profiling Summary

### 6.1 Field Count by Table

| Domain | Tables | Total Fields | Avg Fields | Mandatory Fields |
|--------|--------|-------------|------------|-----------------|
| Infrastructure (STAFF/USERS/SITES) | 3 | 105 | 35 | 23 |
| PMI Core + Sub-tables | 10 | 224 | 22 | 18 |
| RTT/Referral | 4 | 60 | 15 | 14 |
| OPD (Waitlist + Appointments + Coding) | 4 | 78 | 20 | 22 |
| Community | 1 | 48 | 48 | 16 |
| IWL (Profiles + WL + Deferrals + TCIs) | 4 | 74 | 19 | 22 |
| ADT (Admissions + Episodes + Ward + Coding) | 4 | 59 | 15 | 15 |
| Mental Health | 4 | 47 | 12 | 13 |
| Archives | 4 | 208 | 52 | 28 |
| **TOTAL** | **38** | **903*** | **24** | **~171** |

> *Catalog lists 880 actual field rows + ~23 phantom rows = 903 raw rows*

### 6.2 Data Type Distribution

| SQL Data Type | Field Count | % | Notes |
|---------------|-------------|---|-------|
| VARCHAR2 | ~560 | 63% | Most codes stored as human-readable mapped strings (VARCHAR2 80) |
| DATE | ~230 | 26% | All date fields — format DD/MM/YYYY unless otherwise noted |
| NUMBER | ~85 | 10% | Surrogate keys (42), numeric counts, time values |
| CHAR | ~8 | 1% | PDF artefact fields only — not real target columns |

### 6.3 Field Length Distribution

| Length | Count | Typical Use |
|--------|-------|-------------|
| 1 char | ~55 | Flag fields (Y/N), single-char codes (sex, status, encounter_type) |
| 5–10 chars | ~70 | Short codes (GP national code, procedure codes, clinic codes) |
| 20–30 chars | ~60 | Identifiers (CRN, postcode, staff_id, external_system_id) |
| 40 chars | ~35 | Name fields (pat_name_1, family_name) |
| 80 chars | ~280 | Mapped code fields + descriptions (most VARCHAR2 80 fields) |
| 100 chars | ~8 | external_system_id fields |
| 200 chars | ~40 | Clinical coding descriptions |
| 2000 chars | ~30 | Free text comments and notes |
| 42 (NUMBER) | ~85 | Surrogate key fields (record_number, FK fields) |

### 6.4 Mandatory Field Summary (Y = Must be supplied)

| Table | Mandatory Fields |
|-------|-----------------|
| LOAD_STAFF | job_id, psswd_life_months, staff_id, default_parts_entity, default_tools_entity, default_labour_entity, employee_flag, default_stock_entity, eoasis_user, ask_review_warnings, mon/tue/wed/thu/fri/sat/sun_allowed |
| LOAD_PMI | of_birth, date_registered, entered_country, of_death (if applicable) |
| LOAD_PMIADDRS | of_birth, applies_start, applies_end |
| LOAD_PMICONTACTS | applies_start, applies_end |
| LOAD_PMIALLERGIES | applies_start, applies_end |
| LOAD_PMISTAFFWARNINGS | applies_start, applies_end |
| LOAD_SITES | applies_start, applies_end |
| LOAD_RTT_PATHWAYS | pathway_start_date, pathway_end_date |
| LOAD_REFERRALS | first_seen, ref_date, ref_received_date, ref_discharge_date, encounter_type |
| LOAD_RTT_PERIODS | clock_start, clock_stop |
| LOAD_OPDWAITLIST | target_date, removed |
| LOAD_OPDWAITLISTDEF | deferral_start, deferral_end |
| LOAD_OPD_APPOINTMENTS | appt_date, booked_date, time_arrived, time_seen, time_complete, cancelled_date |
| LOAD_CMTY_APPOINTMENTS | diagnosis_date, first_seen, ref_date, ref_received_date, ref_discharge_date, time_arrived, time_seen, time_complete, cancelled_date |
| LOAD_IWL | waitlist_date, last_review_date, removed |
| LOAD_IWL_DEFERRALS | deferral_start |
| LOAD_IWL_TCIS | offer_date, agreed_date, preassessment_date, tci_date, operation_date, estimated_discharge_date |
| LOAD_ADT_ADMISSIONS | cancelled_date, wl_date, admit_date, estimated_discharge_date, discharge_date |
| LOAD_MH_DETENTION_MASTER | diagnosis_date |
| LOAD_MH_DETENTION_TRANSFERS | start_date, end_date, expiry_date, section_review_date, consent_reminder_date, consent_due_date |
| LOAD_MH_CPA_MASTER | applies_start |
| LOAD_MH_CPA_HISTORY | applies_end, next_review_date |
| Archives | of_birth, encounter_type, key date fields (referral_request_date, appointment_date, admit_date, etc.) |

---

## 7. Code Type Mapping Reference

Many target fields use `Maps to: code type NNNNN` — meaning the source value must be translated to the PAS internal code for that code type before loading.

| Code Type | Description | Example Values | Applies To |
|-----------|-------------|----------------|------------|
| 1 | Religion | Christianity, Islam, Buddhism | religion_code |
| 2 | Marital Status | Single, Married, Divorced | marital_status |
| 3 | Sex | Male, Female, Unknown | sex |
| 4 | Occupation | Healthcare Worker, Student | occupation_code |
| 5 | Nationality | British, Irish, Pakistani | nationality |
| 9 | ID Type (Main CRN) | PAS Number, NHS Number | main_crn_type |
| 23 | Extra Information (Patient) | Smoker?, Orthoptic Printing Required? | extra_info_N_type |
| 29 | Title | Mr, Mrs, Dr, Prof | title |
| 274 | Where Died | Ward, Operating Theatre, Ambulance | where_died |
| 333 | Country Codes | GBR, IRL, USA | place_born, country_code |
| 10018 | Security Required | Basic, Enhanced, Administrator | staff_security_level |
| 10028 | Ethnic Origin | White British, Asian/Asian British | ethnic_group |
| 10366 | NHS Number Status Code | Number present and verified, Traced | nhs_number_statusnhs |
| 10454 | Site Codes | (local site codes) | site_code |
| 10495 | eOASIS User Types | Clinical, Administrative, System | type_of_user |
| 10599 | Dataload System | (source system identifier) | system_code |
| 10658 | Preferred Language | English, Welsh, Urdu | preferred_language |
| 10721 | Teams for Dataload Mapping | (local team codes) | default_team |
| 10752 | Causes of Death | Cardiac Failure, Trauma | cause_of_death |
| 10753 | Where Heard Of Service | GP Referral, Self-referral | where_heard_of_service |
| 10768 | Support Categories | (support classification) | client_user |

---

## 8. Data Quality Issues Identified in Target Catalog

| Issue ID | Table(s) | Field(s) | Severity | Description |
|----------|----------|----------|----------|-------------|
| TDQ-001 | All | `raw_field_name` column | Medium | PDF parse artefacts in raw_field_name — adjacent cell text merged into field name strings (e.g. `job_idMust`, `VARCHAR210SYSTEM_CODEUnique`) |
| TDQ-002 | Multiple | 14 phantom fields | High | Fields `must`, `before`, `ranges`, `table`, `indicates`, `ged`, `ge_date`, `ge_toe`, `ge_typee`, `ge_methode`, `ge_specialty`, `ge_consultant`, `ge_status`, `acters`, `appointments` are PDF artefacts — must be excluded from ETL |
| TDQ-003 | LOAD_RTT_EVENTS | `event_date` | High | `event_date` stored as VARCHAR2(19) not DATE — format ambiguity; needs explicit parsing |
| TDQ-004 | LOAD_OPD_ARCHIVE | `time_arrived`, `time_seen`, `time_completed` | Medium | Stored as VARCHAR2(5) not DATE — HH:MM format; different from LOAD_OPD_APPOINTMENTS which uses DATE |
| TDQ-005 | Multiple | `ged_date`, `ge_date` (non-phantom) | High | Several `ged_date` / `ge_date` fields are real fields where the field name was garbled by PDF parsing — actual field names are: `ref_comment` (LOAD_REFERRALS), `appointment_date` (LOAD_CMTY_APPOINTMENTS), `physical_discharge_date` (LOAD_ADT_ARCHIVE), `admission_type` (LOAD_ADT_ADMISSIONS) |
| TDQ-006 | LOAD_PMI | `date_registered` | High | Declared as NUMBER(42) in catalog but spec says "Must be in format: DD/MM/YYYY" — likely parsing error; should be DATE |
| TDQ-007 | LOAD_IWL_DEFERRALS | `deferral_end`, `deferral_reason`, `deferral_comment` | Medium | These fields appear under LOAD_IWL_TCIS table heading in catalog due to PDF table boundary bleeding — they belong to LOAD_IWL_DEFERRALS |
| TDQ-008 | LOAD_PMIIDS | `system_code`, `volume` | Low | `system_code` declared as NUMBER in catalog (parse error) — should be VARCHAR2(10); `volume` field purpose unclear |
| TDQ-009 | LOAD_PMICASENOTEHISTORY | `end_date`, `short_note` | Medium | Both fields have garbled data types in catalog due to PDF cell merging |
| TDQ-010 | LOAD_MH_DETENTION_TRANSFERS | `institution` | Medium | Declared as DATE (parse error) — should be VARCHAR2(80); institution/hospital name or code |
| TDQ-011 | LOAD_ADT_ARCHIVE | `diagnosis` (row 814) | High | Should be `diagnosis_1_desc` (VARCHAR2 200) — the description for diagnosis_1_code — the field name was dropped by PDF parser |
| TDQ-012 | Archives | 6 tables not in MD sections | Critical | LOAD_ADT_ARCHIVE, LOAD_OPD_ARCHIVE, LOAD_CPA_ARCHIVE, LOAD_DETENTION_ARCHIVE, LOAD_MH_CPA_HISTORY, LOAD_MH_CPA_MASTER — appear in PDF catalog but NOT in extracted MD table sections; field definitions may be incomplete |
| TDQ-013 | All | Spec document | Critical | Document is marked "FOR REF ONLY NOT TO BE USED" — cannot be treated as authoritative contract; confirmed spec must be obtained from Altera before go-live |

---

## 9. FK Dependency Map (Record Number Chains)

```
LOAD_PMI.record_number
  ├── LOAD_PMIIDS.loadpmi_record_number
  ├── LOAD_PMIALIASES.loadpmi_record_number
  ├── LOAD_PMIADDRS.loadpmi_record_number
  ├── LOAD_PMICONTACTS.loadpmi_record_number
  ├── LOAD_PMIALLERGIES.loadpmi_record_number
  ├── LOAD_PMISTAFFWARNINGS.loadpmi_record_number
  └── LOAD_PMIGPAUDIT.loadpmi_record_number

LOAD_RTT_PATHWAYS.record_number
  └── LOAD_REFERRALS.loadrttpwy_record_number
      └── LOAD_RTT_PERIODS.loadrttpwy_record_number
              ├── LOAD_RTT_EVENTS.loadrttprd_record_number
              ├── LOAD_OPDWAITLIST.loadrttprd_record_number
              │     ├── LOAD_OPDWAITLISTDEF.loadowl_record_number
              │     └── LOAD_OPD_APPOINTMENTS.loadrttprd_record_number
              │           └── LOAD_OPD_CODING.load_opd_record_number
              └── LOAD_IWL.loadrttprd_record_number
                    ├── LOAD_IWL_DEFERRALS.loadiwl_record_number
                    ├── LOAD_IWL_TCIS.loadiwl_record_number
                    └── LOAD_ADT_ADMISSIONS.loadiwl_record_number
                          ├── LOAD_ADT_EPISODES.adt_adm_record_number
                          │     ├── LOAD_ADT_WARDSTAYS.adt_eps_record_number
                          │     └── LOAD_ADT_CODING.adt_eps_record_number
                          └── LOAD_MH_DETENTION_MASTER.adt_adm_record_number
                                └── LOAD_MH_DETENTION_TRANSFERS.mh_dm_record_number

LOAD_MH_CPA_MASTER.record_number
  └── LOAD_MH_CPA_HISTORY.mh_cm_record_number

Archives: No FK dependencies — loaded independently
LOAD_IWL_PROFILES: No FK dependencies — reference data
```

---

## 10. Critical Gaps — Target Schema vs Source Capability

| Gap | Category | Impact |
|-----|----------|--------|
| No LOAD_AEA table | A&E data has no migration route | High — AEA data (69 fields) cannot be migrated |
| Archive tables absent from MD sections | 6 archive tables incompletely parsed | High — field validation impossible |
| Code type crosswalks undefined | All "Maps to" fields need lookup tables | Critical — 100% of coded fields will fail without mapping config |
| FK surrogate key resolution | `loadpmi_record_number` etc. not in source data | Critical — must be ETL-generated by sequential loading |
| Date format standardisation | Source uses CCYYMMDDHHMM; target uses DD/MM/YYYY | Critical — all date fields need reformatting |
| `date_registered` on LOAD_PMI | No direct source equivalent in PATDATA | Medium — recommend using PtDoB as substitute |
| `entered_country` on LOAD_PMI | No source field for date entered country | Medium — no direct mapping; must default |
| `nationality` on LOAD_PMI | No nationality field in source PATDATA | Medium — gap; source has EthnicType only |
| `where_heard_of_service` | No source equivalent | Low |
| `extra_info_1–10` pairs | 10 extra info slots — source has UserField1/2 only | Low |

---

*Document generated: 2026-02-25 | Target catalog: `schemas/target_schema_catalog.csv` (38 tables, 880 fields)*
*Raw specification: `requirement_spec/Copy of Target PAS - PAS 18.4 Data Migration Technical Guide - FOR REF ONLY NOT TO BE USED.md`*
