# NHS PAS V83 Source Data Schema Profile
**Project:** Queen Victoria Hospital NHS Trust — EPR/PAS Data Migration (V83 → PAS 18.4)
**Document version:** 1.0
**Date:** 2026-02-25
**Source:** `INQuire DD PC83.xlsx` — extracted to `schemas/source_schema_catalog.csv`

---

## 1. Executive Summary

The source system is an **INQuire PAS (PC83/V83)** deployment used by Queen Victoria Hospital NHS Trust. The data dictionary contains **417 tables** and **5,387 fields** covering the full patient administration lifecycle from demographics and waiting lists through inpatient admission, clinical coding and mental health detention records.

This document provides a complete field-by-field schema profile for the **13 highest-priority source tables** that feed the 38 target LOAD_ tables in the PAS 18.4 migration target. It also classifies all 417 source tables by clinical domain and documents the key data profiling characteristics.

---

## 2. Overall Source Data Profiling

### 2.1 Volume Statistics

| Metric | Value |
|--------|-------|
| Total source tables | 417 |
| Total source fields | 5,387 |
| Average fields per table | 12.9 |
| Largest table (fields) | PATDATA — 131 |
| Top-20 tables by field count | 20 tables × 49–131 fields |
| Tables with ≤5 fields | ~180 (lookup/reference tables) |

### 2.2 Data Element Code Series

INQuire uses an **NHS data element catalogue** with alphabetic series prefixes:

| Series | Prefix | Typical Domain | Example |
|--------|--------|----------------|---------|
| A-series | `A0xxx`–`A9xxx` | Core patient & episode data (national standard) | `A0000` = InternalPatientNumber, `A0032C` = PtDoB, `A0366B` = NhsNumber |
| C-series | `C0xxx`–`C9xxx` | Commissioning, contract, local reference data | `C7245` = DistrictOfResidence, `C7046` = PracticeCode |
| H-series | `H0xxx`–`H9xxx` | Hospital operational data (AEA, waiting lists) | `H6087` = A&E Attendance DateTime, `H0024` = Referral Consultant |
| R-series | `R0xxx`–`R9xxx` | Regional/version-specific extensions | `R9219` = CurrentGender (v5.1+), `R9111` = Earliest Reasonable Offer Date |
| D-series | `D2xxx` | Discharge/DRG local codes | `D2154` = RiskFactorCode, `D2182` = DischDate |
| E-series | `E4xxx` | Episode-level extended stats | `E4161` = LosForConsEps |

### 2.3 Date Format Variants

The source system stores dates in multiple formats simultaneously:

| Format | Example | Pattern | Usage |
|--------|---------|---------|-------|
| External display | `17/03/2018` | `DD/MM/YYYY` | Human-facing fields (e.g. `PtDoB`, `AdmissionDate`) |
| External with time | `17/03/2018 14:30` | `DD/MM/YYYY HH:MM` | Datetime fields (e.g. `AdmissionDate`, `DischargeDate`) |
| Internal date | `20180317` | `CCYYMMDD` | Int-suffix fields (e.g. `InternalDateOfBirth`, `PtDateOfDeathInt`) |
| Internal datetime | `201803171430` | `CCYYMMDDHHMM` | Int-suffix datetime fields (e.g. `IpAdmDtimeInt`, `EpisodeStartDtTmInt`) |
| Legacy datetime | `201803171430` | `CCCCMMDDHHMM` | Older A-series codes (note 4-digit century prefix) |

**Migration rule:** All target date fields must be normalised to `CCYYMMDD` or `CCYYMMDDHHMM`. Use the `*Int` sibling field in preference to the display field.

### 2.4 Code Sets Requiring Crosswalk

| Code Set | Source Field(s) | Crosswalk Required |
|----------|-----------------|--------------------|
| Sex / Gender | `Sex` (A0033, 1-char), `CurrentGender` (R9219), `CurrentGenderInt` (R9200B) | Map to PAS 18.4 sex code (M/F/U/9) |
| Ethnicity | `EthnicType` (H1017, 4-char) | NHS 16+1 ethnicity crosswalk |
| Marital Status | `MaritalStatus` (A0058, 1-char) | NHS standard code set |
| Religion | `Religion` (A0054, 4-char) | Local → national code |
| Method of Admission | `MethodOfAdmission` (C0211A, 2-char) | HES admission method codes |
| Method of Discharge | `MethodOfDischarge` (A0362/A8812) | HES discharge method codes |
| Source of Admission | `SourceOfAdm` (A0320) | HES source of admission codes |
| Destination on Discharge | `DestinationOnDischarge` (C0206A) | HES destination codes |
| Priority / Urgency | `Urgency` (A0950), `RefPriority` (C7191) | Routine/Urgent/Two-week-wait |
| GP code | `GpCode` (A0046, 8-char) | ODS national GP code lookup |
| Specialty | `Specialty` (A0448/A0431, 4-char) | HES specialty code crosswalk |
| RTT Period Status | `RttPeriodStatus` (R2224/R2582) | RTT 18-week code set |

### 2.5 Key Structural Patterns

- **Dual field pattern:** Every significant date/code carries an external display field + an internal (`*Int`) sibling field stored in machine-readable format.
- **Episode linkage:** `InternalPatientNumber` (A0000, 9-char numeric) + `EpisodeNumber` (A0142, 9-char) form the composite primary key across all episode-level tables.
- **Address redundancy:** Patient addresses appear in PATDATA (4+1 lines `PtAddrLine1–5` + `PtAddrPostCode`), extended address (`ExtAddressLine1–5`), postal address (`PtPostAddrLine1–5`), and address corrections audit (ADTLADDCOR).
- **Gender versioning:** Pre-v5.1 uses `Sex` (A0033); v5.1+ introduces `CurrentGender` (R9219), `CurrentGenderInt`, `CurrentGenderDesc`. Both coexist in PATDATA, OPA, HWSAPP.
- **OSV status:** Overseas Visitor status `OsvStatus` (C8421, 1-char) appears in OPA, ADMITDISCH, WLCURRENT, WLENTRY, FCEEXT — mandatory for CHC/IVF pathway.

---

## 3. Table Domain Classification

### 3.1 Priority Tables for Migration (13 tables)

| Table | Fields | Clinical Domain | Target Table(s) |
|-------|--------|-----------------|-----------------|
| PATDATA | 131 | Patient Master Index | LOAD_PMI + 7 sub-tables |
| ADMITDISCH | 69 | Inpatient Admissions & Discharges | LOAD_ADT_ADMISSIONS, LOAD_ADT_WARDSTAYS |
| OPA | 107 | Outpatient Appointments | LOAD_OPD_APPOINTMENTS, LOAD_OPDWAITLIST, LOAD_OPD_ARCHIVE |
| FCEEXT | 68 | Finished Consultant Episodes | LOAD_ADT_EPISODES, LOAD_ADT_CODING, LOAD_ADT_ARCHIVE |
| OPREFERRAL | 47 | Outpatient Referrals / RTT | LOAD_REFERRALS, LOAD_RTT_PATHWAYS, LOAD_RTT_PERIODS |
| WLCURRENT | 90 | Inpatient Waiting List (current) | LOAD_IWL |
| WLENTRY | 90 | Inpatient Waiting List (all) | LOAD_IWL (historical) |
| WLACTIVITY | 68 | Waiting List Activity / TCI | LOAD_IWL_TCIS, LOAD_IWL_DEFERRALS |
| CPSGREFERRAL | 46 | Community / Service Group Referrals | LOAD_CMTY_APPOINTMENTS |
| SMREPISODE | 52 | Mental Health / Specialist Medical | LOAD_MH_DETENTION_MASTER, LOAD_DETENTION_ARCHIVE |
| AEA | 69 | A&E Attendances (unmapped — gap) | No current LOAD_ target |
| HWSAPP | 90 | Hospital Waiting Service Applications | LOAD_CMTY_APPOINTMENTS (partial) |
| ADTLADDCOR | 23 | Address Correction Audit | LOAD_PMIADDRS |

### 3.2 Full Domain Classification of all 417 Source Tables

| Domain | Table Count (approx.) | Representative Tables |
|--------|----------------------|-----------------------|
| Patient Demographics / PMI | 12 | PATDATA, ADTLADDCOR, PTMERGE, PATALLOC |
| Inpatient ADT | 25 | ADMITDISCH, ADMISSIONMANAGEMENT, FCEEXT, WARDMOVES |
| Outpatient | 30 | OPA, OPREFERRAL, HWSAPP, OPAREFERRAL, CLINICS |
| Waiting Lists (IP) | 15 | WLCURRENT, WLENTRY, WLACTIVITY, CURRENTPREADMISSIONS, PREADMISSION |
| A&E | 8 | AEA, AEA_IMAGING, AEAASSESS |
| Mental Health / SMR | 10 | SMREPISODE, MHDETENTION, CPANOTES |
| Community | 12 | CPSGREFERRAL, CPSGACTIVITY, CPSGDIARY |
| Cancer | 10 | IPCANCERREG, OPCANCERREG, CANCERSUMMARY |
| Critical Care | 8 | CRITICALCARENEONATE, CRITICALCAREACTYDTPAED, CCU |
| Theatres / Operations | 15 | OCORDER, OCLIST, THEATRESESSION |
| Reference / Code Tables | ~200 | GP master, specialty, ward, consultant code tables |
| Audit / History | ~50 | Audit trails, change logs |
| Finance / Contract | ~20 | Contract, purchaser, HRG tariff |
| Scheduling / Diary | ~12 | Clinical diary, clinic sessions |

---

## 4. Detailed Field-by-Field Schema: Priority Tables

> **Column key:**
> `Field` = source field name | `Sz` = max char size | `Code` = data element code | `Description` | `Inferred Type` | `Migration Target`

---

### 4.1 PATDATA — Patient Master Index
**Field count:** 131 | **Primary key:** `InternalPatientNumber` (A0000)
**Migration target:** LOAD_PMI (core), LOAD_PMIIDS, LOAD_PMIALIASES, LOAD_PMICONTACTS, LOAD_PMIADDRS, LOAD_PMIALLERGIES, LOAD_PMISTAFFWARNINGS, LOAD_PMIGPAUDIT, LOAD_PMICASENOTEHISTORY

#### 4.1.1 Identity Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| InternalPatientNumber | 9 | A0000 | PAS internal patient number (surrogate PK) | Numeric string | `external_system_id`, `main_crn` |
| NhsNumber | 17 | A0366B | NHS Number (with spaces, e.g. `123 456 7890`) | Formatted string | `nhs_number` |
| NHSNumberStatus | 2 | A5768 | NHS Number verification status | Code | `nhs_number_verified` |
| OldNHSNumber | 17 | A8132 | Previous NHS Number (pre-tracing) | String | `LOAD_PMIIDS` |
| PmiAlternatePatientNumberinternal | 18 | A9069 | Alternate patient identifier | String | `LOAD_PMIIDS` |
| DistrictNumber | 14 | A0007C | District patient number | String | `LOAD_PMIIDS` |
| CaseNoteNumber | — | — | (Not in PATDATA; see ADMITDISCH.CaseNoteNumber) | — | — |

#### 4.1.2 Name Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| Surname | 24 | A0027 | Current family name | String | `pat_name_family` |
| Forenames | 20 | A0028 | Forenames | String | `pat_name_1` |
| Title | 5 | A0030 | Title (Mr/Mrs/Dr etc.) | Code/String | `title` |
| PreferredName | 20 | C1457 | Preferred given name (v5.0+) | String | `pat_name_preferred` |
| BirthName | 24 | A4444 | Birth surname | String | `LOAD_PMIALIASES` |
| PreviousSurname1 | 24 | A0324 | Previous surname 1 | String | `LOAD_PMIALIASES` |
| PreviousSurname2 | 24 | A0324A | Previous surname 2 | String | `LOAD_PMIALIASES` |
| PreviousSurname3 | 24 | A0324B | Previous surname 3 | String | `LOAD_PMIALIASES` |

#### 4.1.3 Demographics

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| PtDoB | 10 | A0032C | Date of birth (DD/MM/YYYY) | Date | `of_birth` |
| InternalDateOfBirth | 8 | A0032B | DOB internal (CCYYMMDD) | Date int | Use in preference |
| PtDobDayInt | 2 | A0150 | DOB day component | Int | — |
| PtDobMonthInt | 2 | A0149 | DOB month component | Int | — |
| PtDobYearInt | 4 | A0148 | DOB year component | Int | — |
| Sex | 1 | A0033 | Sex code (legacy, 1=M 2=F 9=Unspecified) | Code | `sex` (with crosswalk) |
| Sex_1 | 1 | A0033C | Sex supplementary | Code | Redundant |
| CurrentGender | 1 | R9219 | Gender identity (v5.1+) | Code | `sex` (preferred) |
| CurrentGenderDesc | 14 | R9200 | Gender description | String | — |
| CurrentGenderInt | 1 | R9200B | Gender internal code | Code | — |
| SexOrientationCode | 2 | R9212 | Sexual orientation (v5.1+) | Code | `sexual_orientation` |
| ObsoleteSexOrientationCode | 2 | R9212 | Obsolete version of above | Code | Ignore |
| EthnicType | 4 | H1017 | Ethnic category (NHS 16+1 code) | Code | `ethnicity` (with crosswalk) |
| MaritalStatus | 1 | A0058 | Marital status | Code | `marital_status` |
| Religion | 4 | A0054 | Religion code | Code | `religion` |
| Occupation | 20 | A0610 | Occupation description | String | — |
| Occnspouse | 20 | A0611 | Spouse/partner occupation | String | — |
| School | 20 | A0367 | School name (paediatric) | String | — |
| CountryOfBirth | 4 | R1948A | Country of birth (code, v4.3+) | Code | `country_of_birth` |
| PlaceOfBirth | 20 | A0068 | Place of birth (text) | String | `place_of_birth` |
| SpokenLanguage | 30 | R9552 | Primary spoken language (v6.0+) | String | `language` |
| AccommodationStatus | 30 | R9551 | Accommodation status (v6.0+) | String | — |
| OsvChargingCategory | 30 | R9554 | Overseas visitor charging category | Code | `overseas_charging` |
| WithheldIdentityReason | 2 | R9632 | Reason identity withheld (v6.0+) | Code | — |

#### 4.1.4 Address Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| PtAddrLine1 | 20 | A0037 | Address line 1 | String | `add_line_1` |
| PtAddrLine2 | 20 | A0038 | Address line 2 | String | `add_line_2` |
| PtAddrLine3 | 20 | A0039 | Address line 3 | String | `add_line_3` |
| PtAddrLine4 | 20 | A0040 | Address line 4 | String | `add_line_4` |
| PtAddrPostCode | 10 | A0041 | Postcode | String | `postcode` |
| ExtAddressLine1 | 35 | A1113 | Extended address line 1 (v3.4+) | String | Prefer over PtAddrLine1 |
| ExtAddressLine2 | 35 | A1114 | Extended address line 2 | String | — |
| ExtAddressLine3 | 35 | A1115 | Extended address line 3 | String | — |
| ExtAddressLine4 | 35 | A1116 | Extended address line 4 | String | — |
| ExtAddressLine5 | 35 | A1122 | Extended address line 5 | String | — |
| ExtAddressPostcd | 10 | A1125 | Extended address postcode | String | — |
| ExtAddressAddLine1 | 35 | C1047 | Extended address additional line (v4.2+) | String | — |
| PtPostAddrLine1–4 | 20 | A9267–A9270 | Postal address lines (may differ from home) | String | LOAD_PMIADDRS |
| PtPostAddrPostCode | 10 | A9271 | Postal address postcode | String | LOAD_PMIADDRS |
| PostAddrExpiryDate | 10 | A3101 | Postal address expiry date (v4.0+) | Date | — |
| PostAddrExpiryDateInt | 8 | A3101A | Postal address expiry date internal | Date int | — |
| DistrictOfResidenceCode | 3 | C7245 | District of residence (from postcode) | Code | `district_of_residence` |
| PostalAddressDistrictOfResidence | 3 | A2993 | Postal address district | Code | — |
| PseudoDisrtrictOfResidence | 3 | A2994 | Pseudo district (suppressed data) | Code | — |
| PtPseudoPostCode | 10 | C4629 | Pseudo postcode (suppressed data) | String | — |

#### 4.1.5 Contact Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| PtHomePhone | 23 | A0042 | Home telephone | String | LOAD_PMICONTACTS |
| PtWorkPhone | 23 | A0043 | Work telephone | String | LOAD_PMICONTACTS |
| PtMobilePhone | 23 | C1458 | Mobile (v5.0+) | String | LOAD_PMICONTACTS |
| PtEmail | 60 | C1459 | Email address (v5.0+) | String | LOAD_PMICONTACTS |
| HomePhone | 23 | A4645 | Alternative home phone | String | — |
| WorkPhone | 23 | A4646 | Alternative work phone | String | — |
| CarerName | 30 | A4639 | Primary carer name | String | LOAD_PMICONTACTS |
| CarerAddress | 100 | A4650 | Carer address | String | LOAD_PMICONTACTS |
| CarerEmail | 60 | R9449 | Carer email (v6.0+) | String | LOAD_PMICONTACTS |
| CarerSupport | 3 | A6925 | Carer support indicator | Code | — |
| Relationship | 9 | A4649 | Carer relationship | String | — |
| RelationshipInt | 2 | A4649A | Carer relationship (internal code) | Code | — |
| NoKName | 30 | A0059 | Next of kin name | String | LOAD_PMICONTACTS |
| NoKRelationship | 9 | A0060 | Next of kin relationship | String | LOAD_PMICONTACTS |
| NoKAddrLine1–4 | 20 | A0061–A0064 | Next of kin address | String | LOAD_PMICONTACTS |
| NoKPostCode | 10 | A0065 | Next of kin postcode | String | LOAD_PMICONTACTS |
| NoKHomePhone | 23 | A0066 | Next of kin home phone | String | LOAD_PMICONTACTS |
| NoKWorkPhone | 23 | A0067 | Next of kin work phone | String | LOAD_PMICONTACTS |
| NoKEmail | 60 | R9448 | Next of kin email (v6.0+) | String | LOAD_PMICONTACTS |
| NoKComments | 30 | A0131 | Next of kin comments | String | — |

#### 4.1.6 Clinical Flags

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| BloodGroup | 3 | A0069 | Blood group (A+/O- etc.) | Code | `blood_group` |
| Allergies | 15 | A0070 | Allergy 1 | String | LOAD_PMIALLERGIES |
| Allergies_1 | 15 | A0072 | Allergy 2 | String | LOAD_PMIALLERGIES |
| MRSA | 3 | A9016 | MRSA carrier indicator (YES/NO) | Code | LOAD_PMISTAFFWARNINGS |
| MRSASetDt | 10 | A3045 | Date MRSA marker set | Date | — |
| MRSASetDtInt | 12 | A9017A | MRSA set date internal (CCYYMMDDHHMM) | Datetime int | — |
| RiskFactorCode | 6 | D2154 | Risk factor code 1 | Code | LOAD_PMISTAFFWARNINGS |
| RiskFactorCode_1 | 6 | D2155 | Risk factor code 2 | Code | LOAD_PMISTAFFWARNINGS |
| MedicalProfileComments | 30 | A0135 | Free-text medical profile comment | String | — |
| Comments | 30 | A4647 | General comments | String | — |
| GeneralComments | 120 | A3500U | Extended general comments | String | — |
| IsCPISExists | 3 | R9535 | CPIS (Child Protection) flag (v6.0+) | Code | — |

#### 4.1.7 GP Registration

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| GpCode | 8 | A0046 | Registered GP code (ODS format) | String | `gp_code` |
| GdpCode | 6 | C4285 | Registered GDP (dentist) code | String | `gdp_code` |
| HealthAuthorityCode | 3 | A9030 | Health authority (obsolete, pre-2013) | Code | Ignore |

#### 4.1.8 Death & Consent Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| PtDeathIndInt | 1 | A0076 | Deceased indicator (internal) | Boolean (0/1) | `deceased_flag` |
| PtDateOfDeath | 10 | A0125 | Date of death (DD/MM/YYYY) | Date | `date_of_death` |
| PtDateOfDeathInt | 10 | A0125A | Date of death internal (CCYYMMDD) | Date int | Preferred |
| PtDeathRecordedDt | 16 | C1253 | Death recording datetime (v4.2+) | Datetime | — |
| PtDeathRecordedDtInt | 12 | C1253A | Death recording datetime internal | Datetime int | — |
| PtDeathRecUserId | 4 | C1252 | User who recorded death | String | — |
| PtDeathInformedBy | 60 | C1254 | Who informed of death | String | — |
| PtDeathComment1 | 60 | C1251B | Death comment 1 (v4.2+) | String | — |
| PtDeathComment2 | 60 | C1251C | Death comment 2 (v4.2+) | String | — |
| PtMsg | 1 | R2451A | Consent to receive messages (v4.3+) | Boolean | `consent_messaging` |
| PtMsgExt | 9 | R2451 | Consent to messages (extended, v6.0+) | Code | — |
| Ptshareinformation | 1 | R9361A | Share information consent (v6.0+) | Boolean | — |
| Ptviaemail | 1 | R9360A | Contact via email consent (v6.0+) | Boolean | — |

#### 4.1.9 Telehealth & System Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| ConsForTeleApptExt | 9 | R3133 | Consent for telephone appointment (v8.2+) | Code | — |
| ConsForTeleApptInt | 1 | R3133A | Consent for telephone appointment (internal) | Boolean | — |
| ConsForVdoApptExt | 9 | R3134 | Consent for video appointment (v8.2+) | Code | — |
| ConsForVdoApptInt | 1 | R3134A | Consent for video appointment (internal) | Boolean | — |
| DateTimeModified | 8 | A0469 | Record last modified date | Date | — |
| DateTimeModifiedInt | 12 | A0469A | Record last modified datetime internal | Datetime int | Audit use |
| FacilId | 20 | R2706 | Facility identifier (v8.2+) | String | — |
| PDSNHSNoNotFiled | 3 | R9491 | PDS NHS number not filed flag (v6.0+) | Code | — |
| OverridePostcoder | 3 | R3018 | Override postcode validator flag (v6.0+) | Code | — |
| PatientDepIndExt | 3 | R8219 | Patient dependant indicator (v8.2+) | Code | — |
| PatientDepIndInt | 1 | R8219A | Patient dependant indicator (internal) | Boolean | — |
| UserField1 | 30 | D2160 | Local user-defined field 1 | String | — |
| UserField2 | 30 | D2161 | Local user-defined field 2 | String | — |
| PtIdentificationComments | 30 | A0035 | Patient ID comments | String | — |
| PtAddrComments | 30 | A0126 | Address comments | String | — |
| Ptcommneedslastreviewed | 10 | R9355 | Communication needs last reviewed (v6.0+) | Date | — |

---

### 4.2 ADMITDISCH — Inpatient Admissions & Discharges
**Field count:** 69 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber`
**Migration target:** LOAD_ADT_ADMISSIONS (admission header), LOAD_ADT_WARDSTAYS (ward movements)

#### 4.2.1 Patient & Episode Identity

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| InternalPatientNumber | 9 | A0000 | PAS patient identifier | Numeric string | FK to LOAD_PMI |
| EpisodeNumber | 9 | A0142 | Episode sequence number | Numeric string | `source_ep_number` |
| DistrictNumber | 14 | A0007C | District patient number | String | — |
| CaseNoteNumber | 14 | C0160 | Case note / medical record number | String | `case_note_number` |

#### 4.2.2 Admission Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| AdmissionDate | 16 | A0372 | Admission date (DD/MM/YYYY HH:MM) | Datetime | `admission_date` |
| AdmissionTime | 10 | A3045B | Admission time | Time | — |
| IpAdmDtimeInt | 12 | A0372A | Admission datetime internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| MethodOfAdmission | 2 | C0211A | Admission method code (HES) | Code | `admission_method` |
| SourceOfAdm | 2 | A0320 | Source of admission code (HES) | Code | `admission_source` |
| IntdMgmt | 1 | A0311 | Intended management (0=Day/1=Overnight etc.) | Code | `intended_management` |
| Category | 3 | A0432 | Patient category (NHS/Private) | Code | `patient_category` |
| AdmReason | 60 | A0309 | Reason for admission (text) | String | `admission_reason` |
| Operation | 60 | A0310 | Intended operation description | String | — |
| HospCode | 4 | A0428 | Admitting hospital code | Code | `hospital_code` |
| AdmWard | 4 | A0429 | Admitting ward code | Code | `ward_code` |
| Consultant | 6 | A0430 | Admitting consultant code | Code | `consultant_code` |
| Specialty | 4 | A0431 | Admitting specialty code | Code | `specialty_code` |
| Bed | 4 | A9412 | Bed identifier | Code | `bed_code` |
| Room | 4 | H7506 | Room identifier | Code | — |
| Lodger | 3 | A0313 | Lodger indicator (YES/NO) | Code | — |

#### 4.2.3 Discharge Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| DischargeDate | 16 | A0348 | Discharge date (DD/MM/YYYY HH:MM) | Datetime | `discharge_date` |
| DischargeTime | 10 | A3045 | Discharge time | Time | — |
| IpDschDtimeInt | 12 | A0348A | Discharge datetime internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| DischWard | 4 | A0441 | Discharging ward code | Code | `discharge_ward` |
| MethodOfDischarge | 2 | A0362 | Discharge method code (HES) | Code | `discharge_method` |
| DestinationOnDischarge | 2 | C0206A | Destination on discharge (HES) | Code | `discharge_destination` |
| TransTo | 14 | C0224 | Hospital transferred to on discharge | Code | `transfer_to_hospital` |
| TransFrom | 14 | C0213 | Hospital transferred from on admission | Code | `transfer_from_hospital` |

#### 4.2.4 Clinical Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| HRGCode | 5 | A5706 | Healthcare Resource Group code (v4.3+) | Code | `hrg_code` |
| JointCons | 6 | A0485 | Joint consultant code | Code | — |
| JointSpec | 4 | A0549 | Joint specialty code | Code | — |
| EpiGPCode | 8 | H7621 | Episodic GP code | String | `episodic_gp` |
| EpiGPPracticeCode | 6 | C7046 | Episodic GP practice code | String | — |
| EpiOptCode | 8 | R9415 | Episodic optometrist code (v6.0+) | String | — |
| EpiOptPracticeCode | 3 | R9398 | Episodic optometrist practice | String | — |
| TheatreTime | 3 | A0332 | Theatre time allocated (minutes) | Numeric | — |
| ExpectedLos | 3 | A0312 | Expected length of stay (days) | Numeric | — |
| LivestillBirth | 5 | C4572 | Live/still birth indicator | Code | — |
| A1stRegDaynightAdm | 3 | C8498 | First of regular day/night admissions flag | Code | — |

#### 4.2.5 RTT & Waiting List Link

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| DateOnWl | 8 | C0197 | Date placed on waiting list | Date | LOAD_IWL FK |
| WlDateCcyy | 10 | C0197C | Waiting list date (CCYY format) | Date | — |
| RttPeriodStatus | 4 | R2224 | RTT period status code | Code | LOAD_RTT_PERIODS |
| AdmEROD | 10 | R9111 | Earliest Reasonable Offer Date (PCxx baseline) | Date | `erod` |
| AdmERODInt | 12 | R9111A | EROD internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| DecisionToRefer | 10 | C1200 | Decision to refer date (v4.2+) | Date | LOAD_REFERRALS |
| ReasonForReferral | 4 | C1199 | Reason for referral code (v4.2+) | Code | — |

#### 4.2.6 Administrative & Report Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| BenefitCode | 1 | C0144 | Benefit code | Code | — |
| OsvStatus | 1 | C8421 | Overseas visitor status | Code | `osv_status` |
| NHSEmployee | 1 | R9650 | NHS employee indicator (v8.2+) | Boolean | — |
| NHSEmployeeRole | 30 | R9653 | NHS employee role | String | — |
| NHSEmployerOrg | 30 | R9651 | NHS employer organisation | String | — |
| ConToInfEmployer | 1 | R9654 | Consent to inform employer (v8.2+) | Boolean | — |
| EpsCurrActvSts | 11 | A0162 | Current episode status | Code | `episode_status` |
| Referral | 1 | C0196 | Referral indicator | Code | — |
| Br409Required | 3 | A0329 | BR409 form required flag | Code | — |
| DateBR409Sent | 10 | A0337 | Date BR409 sent | Date | — |
| Outlier | 1 | H7505A | Outlier indicator | Code | — |
| Comment | 30 | C0195 | General comment | String | — |
| PatientProcedureDescription2 | 60 | C8709 | Patient procedure description 2 (v6.0+) | String | — |
| ReportRequired | 3 | R1573 | Report required (YES/NO) | Code | — |
| ReportRequiredInt | 1 | R1573A | Report required internal | Boolean | — |
| ReportReason | 30 | R1574 | Report reason | String | — |
| ReportDelayCode | 4 | R1571 | Report delay code | Code | — |
| ReportDelayDesc | 30 | R1572 | Report delay description | String | — |
| ReportDispDt | 16 | R1575 | Report dispatched date (DD/MM/YYYY HH:MM) | Datetime | — |
| ReportDispDtInt | 12 | R1575A | Report dispatched datetime internal | Datetime int | — |
| ExpDateofDischarge | 16 | A0306 | Expected discharge date (PCxx) | Datetime | `expected_discharge_date` |
| ExpDateofDischInt | 12 | A0306A | Expected discharge date internal | Datetime int | Preferred |

---

### 4.3 OPA — Outpatient Appointments
**Field count:** 107 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber`
**Migration target:** LOAD_OPD_APPOINTMENTS, LOAD_OPDWAITLIST, LOAD_OPD_ARCHIVE, LOAD_OPD_CODING

#### 4.3.1 Patient Identity

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| InternalPatientNumber | 9 | A0000 | Patient identifier | Numeric string | FK to LOAD_PMI |
| EpisodeNumber | 9 | A0142 | Episode number | Numeric string | `source_ep_number` |
| DistrictNumber | 14 | A0007C | District patient number | String | — |
| NhsNumber | 17 | A0366B | NHS Number | String | `nhs_number` |
| Forenames | 20 | A0028 | Patient forenames | String | — |
| Surname | 24 | A0027 | Patient surname | String | — |
| Sex | 1 | A0033 | Sex (legacy) | Code | — |
| CurrentGender | 1 | R9219 | Gender identity (v5.1+) | Code | `sex` |
| CurrentGenderDesc | 14 | R9200 | Gender description | String | — |
| CurrentGenderInt | 1 | R9200B | Gender internal | Code | — |
| Dob | 10 | A0032C | Date of birth | Date | — |
| Postcode | 10 | A0041 | Patient postcode | String | — |
| GdpCode | 6 | C4285 | GDP code | String | — |
| HaCode | 3 | C7245 | Health authority code | Code | — |
| PracticeCode | 6 | C7046 | GP practice code | String | `gp_practice` |
| RegGPCode | 8 | A0046 | Registered GP code | String | `gp_code` |
| EpiGp | 8 | H7621 | Episodic GP code | String | — |
| OsvStatus | 1 | C8421 | Overseas visitor status | Code | — |

#### 4.3.2 Appointment Booking

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| ApptDate | 10 | A3045A | Appointment date | Date | `appointment_date` |
| ApptTime | 10 | A3045 | Appointment time | Time | `appointment_time` |
| ApptEndTime | 5 | A1383 | Appointment end time | Time | — |
| PtApptStartDtimeInt | 12 | A1446A | Appointment datetime internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| ApptCategory | 3 | A1647 | Appointment category (NEW/FOL) | Code | `appointment_category` |
| ApptClass | 1 | C4683 | Appointment class (1=New, 2=Follow-up) | Code | — |
| ApptType | 3 | A1271 | Appointment type | Code | `appointment_type` |
| ApptStatus | 4 | A1295 | Appointment status (ATT/WLK/NATT/SATT/NR) | Code | `appointment_status` |
| ApptComment | 60 | A1288 | Appointment comment | String | — |
| PtCategory | 3 | A1284 | Patient category at appointment | Code | — |
| PtVerticalApptInd | 1 | A1296 | Vertical timeslot position indicator | Code | — |
| ApptBookedDate | 16 | H0369 | Booking date/time | Datetime | `booking_date` |
| ApptBookedTime | 10 | A3045B | Booking time | Time | — |
| DateApptBookedInt | 12 | H0369A | Booking datetime internal | Datetime int | Preferred |
| BookingType | 4 | C0868E | Booking type code | Code | `booking_type` |
| ReasonForCanc | 30 | A1291 | Cancellation reason | String | `cancellation_reason` |
| CancelBy | 1 | A1289 | Cancelled by (H=Hospital, P=Patient) | Code | `cancelled_by` |
| CancelComment | 30 | A1292 | Cancellation comment | String | — |
| ApptCancDate | 16 | A1290 | Cancellation date | Datetime | `cancellation_date` |
| ApptCancTime | 10 | A3045C | Cancellation time | Time | — |
| ApptCancDTimeInt | 12 | A1290A | Cancellation datetime internal | Datetime int | Preferred |
| ApptEnteredDtime | 12 | A9733A | Original entry datetime of appointment | Datetime int | Audit |
| ApptEnteredUID | 4 | C4332 | User who originally entered appointment | String | Audit |
| LastRevisionDtime | 12 | A9734A | Last revision datetime | Datetime int | Audit |
| LastRevisionUID | 4 | C4333 | User who last revised | String | Audit |
| Transport | 2 | A1286 | Transport code | Code | — |
| Interpreter | 3 | C1750 | Interpreter required (YES/NO, v5.0+) | Code | — |
| InterpreterLanguage | 35 | C1751 | Interpreter language (v5.0+) | String | — |

#### 4.3.3 Clinic & Clinician

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| ClinicCode | 8 | A1380 | Clinic code | Code | `clinic_code` |
| ClinicSpecialty | 4 | A0293 | Clinic specialty | Code | `specialty_code` |
| ClinicConsultant | 6 | C4575 | Clinic consultant | Code | `consultant_code` |
| ResCode | 8 | A1381 | Responsible clinician code | Code | — |
| RefConsultant | 6 | H0024 | Referring consultant code | Code | `referring_consultant` |

#### 4.3.4 Referral Fields

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| ReferralDate | 10 | A3045F | Referral date | Date | `referral_date` |
| ReferralTime | 10 | A3045E | Referral time | Time | — |
| ReferralDateInt | 12 | A1216A | Referral datetime internal | Datetime int | Preferred |
| RefBy | 3 | A1274 | Referred by type code | Code | `referral_source` |
| ReasonForRef | 4 | C7078 | Reason for referral | Code | `referral_reason` |
| RefSpecialty | 4 | H0025 | Referral specialty | Code | — |
| RefPrimaryDiagnosisCode | 7 | C4604 | Primary diagnosis at referral (ICD-10) | Code | `primary_diagnosis` |
| RefSubsidDiag | 7 | C4607 | Subsidiary diagnosis at referral | Code | — |
| RefPriority | 1 | C7191 | Referral priority code | Code | `priority` |
| GpDiagnosis | 7 | A9737 | GP's diagnosis | Code | — |
| CaseNoteNumber | 14 | H0028B | Case note number | String | `case_note_number` |
| ReferralContractId | 6 | C7071 | Referral contract identifier | Code | — |
| ReferralPurchaser | 5 | C7000E | Referral purchaser code | Code | — |
| BookFromWL | 8 | A0583 | Waiting list code appointment booked from | Code | `wl_source_code` |

#### 4.3.5 Discharge & Clinical Outcome

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| DischDate | 16 | D2182 | OPD discharge date | Datetime | `discharge_date` |
| DischTime | 10 | A3045D | OPD discharge time | Time | — |
| OpDischargeDTimeInt | 12 | D2182A | OPD discharge datetime internal | Datetime int | Preferred |
| Disposal | 4 | C7054 | Disposal code (next action) | Code | `disposal_code` |
| AttPriDiagCode | 7 | A2503 | Primary diagnosis at attendance (ICD-10) | Code | `primary_diagnosis_att` |
| AttSubDiagCode | 7 | A2504 | Subsidiary diagnosis at attendance | Code | — |
| ApptPrimaryProcedureCode | 5 | C4632 | Primary procedure code | Code | `primary_procedure` |
| HRGCode | 6 | A1159 | HRG code (v3.4+) | Code | `hrg_code` |
| ReadPrimary | 8 | A6333 | READ primary procedure code | Code | — |
| PrimaryProcGroup | 4 | C6033 | Primary procedure group | Code | — |

#### 4.3.6 Contracting & Purchasing

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| ApptConractId | 6 | C7071E | Appointment contract ID | Code | — |
| ApptPurchaser | 5 | C7000 | Appointment purchaser | Code | — |
| ApptPurchRef | 20 | C6035 | Purchaser reference | String | — |
| PatChoice | 3 | A0589 | Patient choice indicator (v3.4+) | Code | — |
| WaitingGuaranteeException | 1 | A4427 | Waiting guarantee exception | Code | — |
| WaitingGuaranteeExceptionDesc | 46 | A4428 | Waiting guarantee exception description | String | — |

#### 4.3.7 RTT / 18-Week Pathway

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| OpEROD | 10 | R9108 | Earliest Reasonable Offer Date (OP) | Date | `erod` |
| OpERODInt | 12 | R9108A | EROD internal | Datetime int | Preferred |
| BreachDate | 10 | C1509 | 18-week breach date | Date | `breach_date` |
| BreachDateInt | 8 | C1509A | Breach date internal (CCYYMMDD) | Date int | Preferred |
| BreachReasonCode | 4 | C1510 | Breach reason code | Code | `breach_reason_code` |
| BreachReasonDesc | 30 | C1510A | Breach reason description | String | — |
| BreachReasonCmnt | 30 | C1511 | Breach reason comment | String | — |
| BreachRecDtime | 18 | A1172 | Breach recorded datetime | Datetime | — |
| BreachRecDtimeInt | 12 | A1172A | Breach recorded datetime internal | Datetime int | — |
| RttPeriodStatus | 4 | R2223 | RTT period status | Code | LOAD_RTT_PERIODS |
| RttAFDT | 3 | R1597 | RTT Actual First Definitive Treatment date (Ext) | Date | `rtt_afdt` |
| RttAFDTInt | 1 | R1597A | RTT AFDT internal | Date int | — |
| CABServiceCode | 6 | C1951 | CAB service code | Code | — |
| CABServiceDesc | 50 | C1864B | CAB service description | String | — |
| UniqueServiceID | 50 | C1865 | Unique service identifier | String | `unique_service_id` |

#### 4.3.8 Choose & Book / e-Booking

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| EbookingReferenceNumber | 30 | C1846 | e-Booking reference number (v5.0+) | String | `ebooking_ref` |
| EbookingDNAReason | 1 | C1849 | e-Booking DNA reason | Code | — |
| EbookingDNAReasonDesc | 35 | C1849B | e-Booking DNA reason description | String | — |
| OfferAccepted | 3 | C1803 | Offer accepted flag (v5.0+) | Code | — |
| ReasonableOffer | 3 | C1805 | Reasonable offer flag (v5.0+) | Code | — |
| A2ndOfferDate | 10 | C1804 | Second offer date (v5.0+) | Date | — |
| A2ndOfferDateInt | 8 | C1804A | Second offer date internal | Date int | — |
| PatientDepIndEXT | 3 | R8219 | Patient dependant indicator (v8.2+) | Code | — |
| PatientDepIndINT | 1 | R8219A | Patient dependant indicator internal | Boolean | — |
| WNBReasonCode | 4 | R8221A | Would Not Benefit reason code (v8.2+) | Code | — |
| WNBReasonDesc | 30 | R8221 | WNB reason description | String | — |

---

### 4.4 OPREFERRAL — Outpatient Referrals
**Field count:** 47 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber`
**Migration target:** LOAD_REFERRALS, LOAD_RTT_PATHWAYS, LOAD_RTT_PERIODS, LOAD_RTT_EVENTS

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| InternalPatientNumber | 9 | A0000 | Patient identifier | Numeric string | FK to LOAD_PMI |
| EpisodeNumber | 9 | A0142 | Episode number | Numeric string | `source_ep_number` |
| DistrictNumber | 14 | A0007C | District number | String | — |
| CaseNoteNumber | 14 | H0028B | Case note number | String | `case_note_number` |
| HospitalCode | 4 | H0022 | Hospital code | Code | `hospital_code` |
| ConsCode | 6 | H0024 | Consultant code | Code | `consultant_code` |
| Specialty | 4 | H0025 | Specialty code | Code | `specialty_code` |
| Category | 3 | H0053 | Referral category | Code | — |
| RefBy | 3 | H0299 | Referred by type | Code | `referral_source_type` |
| EpiReferringCon | 6 | A5493 | Referring consultant code (v3.3+) | Code | `referring_consultant` |
| EpiGPCode | 8 | H7621 | Episodic GP code | String | `episodic_gp` |
| EpiGPPracticeCode | 6 | C7046 | Episodic GP practice code | String | — |
| EpiGDPCode | 8 | H7622 | Referring GDP code (v3.3+) | String | — |
| EpiOptCode | 8 | R9415 | Episodic optometrist (v6.0+) | String | — |
| EpiOptPracticeCode | 3 | R9398 | Episodic optometrist practice | String | — |
| ReferralDate | 10 | A3045A | Referral date | Date | `referral_date` |
| OpRegDtimeInt | 12 | A1216A | Referral datetime internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| DecisionToRefer | 10 | A0835 | Date of decision to refer (v3.2+) | Date | `decision_to_refer_date` |
| PriorityType | 1 | C7191 | Priority type (R/U/2WW) | Code | `priority_type` |
| SuspectedCancerCode | 6 | A0814 | 2WW suspected cancer code (v3.2+) | Code | `suspected_cancer` |
| Verbal | 3 | A8189 | Verbal referral flag (YES/NO, v3.2+) | Code | — |
| WalkinReferral | 3 | A8188 | Walk-in referral flag (YES/NO, v3.2+) | Code | — |
| AppointmentWithinTargetDays | 3 | A0836 | Appt within target days flag (v3.2+) | Code | — |
| Comment | 60 | H7010 | Referral comment | String | — |
| RefComment | 25 | H0368 | Short referral comment | String | — |
| DiagnosisStatus | 1 | H7009 | Diagnosis status | Code | — |
| GpDiagnosis | 7 | A9737 | GP's diagnosis | Code | — |
| GPReferralLetterNumber | 6 | A4413 | GP referral letter number | String | `referral_letter_number` |
| KornerEpisodePrimaryDiagnosisCode | 7 | C4604 | Primary diagnosis (ICD-10) | Code | `primary_diagnosis` |
| ReadPrimary | 8 | A6329 | READ primary diagnosis code | Code | — |
| ReadSubsid | 8 | A6331 | READ subsidiary code | Code | — |
| Subsid | 7 | C4607 | Subsidiary diagnosis | Code | — |
| RiIcd10OpEpisodeDiagnosisCodeType | 1 | A8111 | ICD-10 diagnosis code type | Code | — |
| DateOfPrimaryDiagnosis | 8 | C4676A | Date primary diagnosis | Date int | — |
| RTTPeriodStatus | 4 | R2582 | RTT period status (v4.3+) | Code | LOAD_RTT_PERIODS |
| RTTPeriodStatusInt | 2 | R2583 | RTT period status internal | Code | — |
| CurrentStatus | 4 | A3488 | Current referral status (v4.0+) | Code | `current_status` |
| CurrentStatusDescription | 25 | A3488A | Current status description | String | — |
| StatusDT | 16 | A3498 | Status change datetime (v4.0+) | Datetime | — |
| StatusDTInt | 12 | A3498A | Status change datetime internal | Datetime int | — |
| ReasonForRef | 4 | C7078 | Reason for referral code | Code | `referral_reason` |
| QM08StartWaitDate | 10 | A3045B | QM08 wait start date | Date | — |
| QM08EndWtDate | 10 | A3045D | QM08 wait end date | Date | — |
| DischargeDt | 12 | D2182A | Discharge datetime internal | Datetime int | `discharge_date` |
| DischargeTm | 16 | D2182 | Discharge datetime external | Datetime | — |
| OsvExempt | 1 | C8421A | OSV exempt flag | Code | — |
| OsvStatus | 1 | C8421 | Overseas visitor status | Code | — |

---

### 4.5 WLCURRENT — Current Inpatient Waiting List
**Field count:** 90 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber`
**Migration target:** LOAD_IWL

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| InternalPatientNumber | 9 | A0000 | Patient identifier | Numeric string | FK to LOAD_PMI |
| EpisodeNumber | 9 | A0142 | Episode number | Numeric string | `source_ep_number` |
| DistrictNumber | 14 | A0007C | District number | String | — |
| CaseNoteNumber | 14 | C0160 | Case note number | String | `case_note_number` |
| DateOnList | 16 | A0971 | Date placed on waiting list | Datetime | `date_on_list` |
| WlOnListDtTmInt | 12 | A0971A | On-list datetime internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| WLOnListTime | 10 | A3045E | On-list time | Time | — |
| OriginalDateOnList | 10 | A9659 | Original date on list (pre-suspension) | Date | `original_date_on_list` |
| OriginalDateOnListTime | 10 | A3045C | Original on-list time | Time | — |
| LastReviewDate | 10 | C0335 | Last waiting list review date | Date | `last_review_date` |
| ReviewResult | 22 | C0339 | Review result code | Code | — |
| EpsCurrWlRevwRespDtInt | 8 | C0337A | Review response date internal | Date int | — |
| Hospital | 4 | A0445 | Hospital code | Code | `hospital_code` |
| Ward | 4 | A0446 | Ward code | Code | `ward_code` |
| Consultant | 6 | A0447 | Consultant code | Code | `consultant_code` |
| Specialty | 4 | A0448 | Specialty code | Code | `specialty_code` |
| Category | 3 | A0449 | Patient category (NHS/Private) | Code | `patient_category` |
| Urgency | 1 | A0950 | Urgency code (R/U/2) | Code | `urgency` |
| IntdMgmt | 1 | A0311 | Intended management | Code | `intended_management` |
| WlCode | 6 | A0939 | Waiting list code | Code | `waiting_list_code` |
| DiagGroup | 6 | C0333 | Diagnosis group | Code | — |
| Period | 6 | C3702 | Contract period | Code | — |
| Operation | 60 | A0310B | Intended operation | String | `intended_operation` |
| OperationDate | 10 | A3045B | Operation date | Date | — |
| IntendedProc | 7 | C3291 | Intended OPCS-4 procedure code | Code | `intended_procedure` |
| ReadPrimIntProc | 8 | A8999 | READ intended procedure code | Code | — |
| ProvisionalDiagnosis | 7 | A9662 | Provisional diagnosis (ICD-10) | Code | `provisional_diagnosis` |
| ReadProvDiag | 8 | A8993 | READ provisional diagnosis | Code | — |
| PatientProcedureDescription2 | 60 | C8709 | Patient procedure description 2 (v6.0+) | String | — |
| ProcGrp | 3 | A8487B | Procedure group | Code | — |
| ExpectedLos | 3 | A0312 | Expected length of stay | Numeric | `expected_los` |
| ExpectedAnaesthesia | 1 | C8690A | Expected anaesthesia type (v—PCxx) | Code | `anaesthesia_type` |
| TheatreTime | 3 | A0332 | Theatre time (mins) | Numeric | — |
| ShortNotice | 3 | A0952 | Short notice patient (YES/NO) | Code | `short_notice` |
| SpecialCase | 3 | A0951 | Special case flag | Code | — |
| InCare | 3 | A0956 | In care flag | Code | — |
| Lodger | 3 | A0313 | Lodger indicator | Code | — |
| ContactPhone | 23 | A0212 | Contact phone | String | — |
| KH07StartWait | 10 | A3045A | KH07 wait start date | Date | `kh07_start_date` |
| KH07StartWaitInt | 8 | A5667 | KH07 wait start date internal (CCYYMMDD) | Date int | Preferred |
| KH07SusDays | 4 | A5666 | Suspended days since KH07 start | Numeric | `kh07_suspended_days` |
| KH07Wait | 6 | A5723 | Current KH07 waiting days (net) | Numeric | `kh07_wait_days` |
| HistSuspDays | 4 | C2007 | Historical suspended days (v5.0+) | Numeric | — |
| WlBreachDate | 14 | R0088 | Waiting list breach date | Date | `breach_date` |
| WlBreachDateInternal | 12 | R0088A | Breach date internal | Date int | Preferred |
| WlBreachReasonCode | 4 | R0090 | Breach reason code | Code | `breach_reason_code` |
| BreachReasonComment | 30 | R0089 | Breach reason comment | String | — |
| BreachReasonDesc | 30 | C1501 | Breach reason description | String | — |
| BreachRecordedDate | 12 | A1172A | Breach recorded datetime | Datetime int | — |
| GuaranteedAdmissionDate | 10 | A9660 | Guaranteed admission date | Date | `guaranteed_adm_date` |
| LatestAdmDate | 10 | A9661 | Latest admission date | Date | `latest_adm_date` |
| WLApproxAdmissionDate | 10 | A0972 | Approximate admission date | Date | — |
| WLApproxAdmissionTime | 10 | A3045D | Approximate admission time | Time | — |
| AdmissionDate | 16 | A0372 | Actual admission date (when admitted) | Datetime | — |
| AdmissionDateTmInt | 12 | A0372A | Actual admission datetime internal | Datetime int | — |
| AdmissionTime | 10 | A3045 | Actual admission time | Time | — |
| AdmReason | 60 | A0309 | Admission reason | String | — |
| MethodOfAdm | 2 | C0332 | Method of admission | Code | `admission_method` |
| BookingType | 4 | C0868 | Booking type | Code | `booking_type` |
| CancdeferInd | 1 | A9652A | Cancel/defer indicator | Code | — |
| ReferralLetterNumber | 6 | A4383 | Referral letter number | String | — |
| ContractID | 6 | C7071 | Contract identifier | Code | — |
| Provider | 4 | C7015 | Provider code | Code | — |
| Purchaser | 5 | C7000 | Purchaser code | Code | — |
| PurchaserRef | 20 | C6020 | Purchaser reference | String | — |
| Referral | 1 | C0196 | Referral indicator | Code | — |
| EpiGPCode | 8 | H7621 | Episodic GP code | String | `episodic_gp` |
| EpiGPPractice | 6 | C7046 | Episodic GP practice | String | — |
| EpiOptCode | 8 | R9415 | Episodic optometrist (v6.0+) | String | — |
| EpiOptPracticeCode | 3 | R9398 | Episodic optometrist practice | String | — |
| JointCons1–4 | 5–6 | A0483/A2988x | Joint consultant codes 1–4 | Code | — |
| JointSpec1–4 | 4–5 | A0479/A2989x | Joint specialty codes 1–4 | Code | — |
| EpsActvTypeInt | 2 | A0151 | Episode activity type internal | Code | `episode_activity_type` |
| EpsCurrActvStsInt | 3 | A0162A | Current episode status internal | Code | `episode_status` |
| Transport | 2 | A0308 | Transport code | Code | — |
| WaitingGuaranteeException | 1 | A4439 | Waiting guarantee exception | Code | — |
| WaitingGuaranteeExceptionDesc | 46 | A4440 | Waiting guarantee exception description | String | — |
| WlIndexSortKey1 | 6 | C0327 | Waiting list sort key 1 | String | — |
| WlIndexSortKey2 | 20 | C0328 | Waiting list sort key 2 | String | — |
| CommentCl | 60 | H0479 | Clinical comment | String | `comment_clinical` |
| CommentNonClin | 60 | A0954A | Non-clinical comment | String | `comment_admin` |
| UserId | 4 | A1176A | Last user to update record | String | Audit |
| OsvExempt | 1 | C8421A | OSV exempt | Code | — |
| OsvStatus | 1 | C8421 | Overseas visitor status | Code | — |

---

### 4.6 WLENTRY — Inpatient Waiting List Entries (Historical + Current)
**Field count:** 90 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber`
**Migration target:** LOAD_IWL (historical records supplement WLCURRENT)

> WLENTRY is structurally identical to WLCURRENT. It contains both active and historical waiting list episodes. Key differences: WLENTRY includes `DecisionToRefer` and `ReasonForReferral` fields linking to the referral pathway.

Additional fields versus WLCURRENT:

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| DecisionToRefer | 10 | C1200 | Decision to refer date (v4.2+) | Date | `decision_to_refer` |
| ReasonForReferral | 4 | C1199 | Reason for referral (v4.2+) | Code | `referral_reason` |
| CEA | 1 | A6893 | Clinical Excellence Award indicator | Code | — |
| AdmEROD | 10 | R9111 | Earliest Reasonable Offer Date | Date | `erod` |
| AdmERODInt | 12 | R9111A | EROD internal | Datetime int | Preferred |
| RttAFDT | 3 | R1597 | RTT AFDT date external | Date | `rtt_afdt` |
| RttAFDTInt | 1 | R1597A | RTT AFDT internal | Date int | — |
| WlBreachDate | 14 | R0088 | Breach date | Date | `breach_date` |
| WlBreachDateInternal | 12 | R0088A | Breach date internal | Date int | — |
| WlBreachReasonCode | 4 | R0090 | Breach reason code | Code | `breach_reason_code` |
| BreachReasonComment | 30 | R0089 | Breach reason comment | String | — |
| BreachReasonDes | 30 | C1501 | Breach reason description | String | — |
| BreachRecordedDate | 12 | A1172A | Breach recorded datetime | Datetime int | — |
| EpsActvDtimeInt | 12 | A0133A | Activity datetime internal | Datetime int | — |
| EpsCurrActvStsInt | 3 | A0162A | Episode status internal | Code | — |
| EpsCurrWlRevwRespDtInt | 8 | C0337A | Review response date internal | Date int | — |
| WLOnListDate | 16 | A0971 | On-list date | Datetime | `date_on_list` |
| WlOnListDtTmInt | 12 | A0971A | On-list datetime internal | Datetime int | Preferred |
| WLOnListTime | 10 | A3045E | On-list time | Time | — |
| UserId | 4 | A1176A | User ID | String | Audit |

---

### 4.7 WLACTIVITY — Waiting List Activity (TCI, Deferrals, Removals)
**Field count:** 68 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber` + `EpsActvDtimeInt`
**Migration target:** LOAD_IWL_TCIS (TCI records), LOAD_IWL_DEFERRALS (suspensions/deferrals)

#### 4.7.1 Core Activity

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| InternalPatientNumber | 9 | A0000 | Patient identifier | Numeric string | FK to LOAD_PMI |
| EpisodeNumber | 9 | A0142 | Episode number | Numeric string | FK to LOAD_IWL |
| Activity | 99 | A0402 | Activity code and description | String | `activity_type` |
| ActivityDate | 14 | A0133 | Activity date | Date | `activity_date` |
| ActivityTime | 10 | A3045 | Activity time | Time | — |
| EpsActvDtimeInt | 12 | A0133A | Activity datetime internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| EpsActvTypeInt | 2 | A0151 | Activity type internal code | Code | `activity_type_code` |
| PrevActivity | 20 | A0457 | Previous activity code | String | — |
| PrevActivityDate | 16 | A0450 | Previous activity date | Datetime | — |
| PrevActivityDTimeInt | 12 | A0450A | Previous activity datetime internal | Datetime int | — |
| PrevActivityTime | 10 | A3045A | Previous activity time | Time | — |
| PrevActivityInt | 2 | A0457A | Previous activity internal code | Code | — |

#### 4.7.2 TCI (To Come In) Booking

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| TCIDate | 16 | A0316 | TCI (admission offer) date | Datetime | `tci_date` |
| TCITime | 10 | A3045B | TCI time | Time | — |
| TCIDTimeInt | 12 | A0316A | TCI datetime internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| TCIAcceptDate | 8 | C0338 | Date patient accepted TCI offer | Date | `tci_accept_date` |
| TCIAcceptDateInt | 8 | C0338A | TCI accept date internal | Date int | Preferred |
| TCILetterDate | 8 | C0336 | TCI letter date | Date | `tci_letter_date` |
| TCIOfferDateInt | 8 | C0336A | TCI offer date internal (CCYYMMDD) | Date int | Preferred |
| TCILetterComment | 30 | C0340 | TCI letter comment | String | — |
| BookingType | 4 | C0868 | Booking type | Code | `booking_type` |
| AdmEROD | 10 | R9111 | Earliest Reasonable Offer Date | Date | `erod` |
| AdmERODInt | 12 | R9111A | EROD internal | Datetime int | Preferred |

#### 4.7.3 Deferral / Suspension

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| SuspReason | 4 | A0842 | Suspension reason code (v4.0+) | Code | `suspension_reason` |
| DefEndDate | 10 | A2326 | End of deferral/suspension | Date | `deferral_end_date` |
| DefEndDateInt | 12 | A2326A | Deferral end datetime internal | Datetime int | Preferred |
| DefRevisedEndDate | 10 | A9505 | Revised deferral end date | Date | `revised_end_date` |
| DefRevisedEndDateInt | 12 | A9505A | Revised deferral end datetime internal | Datetime int | Preferred |
| WlSuspensionInitiator | 1 | A2329A | Suspension initiator code | Code | `suspension_initiator` |
| WLSuspensionInitiatorDesc | 10 | A2329B | Suspension initiator description (v4.0+) | String | — |
| PatSelfDeferral | 3 | C2009 | Patient self-deferral flag (v5.0+) | Code | — |
| PatSelfDeferralInt | 1 | C2009A | Patient self-deferral internal | Boolean | — |

#### 4.7.4 Removal / Cancellation

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| RemovalReason | 4 | A0958 | Removal reason code | Code | `removal_reason` |
| RemovalComment | 25 | A0957 | Removal comment | String | `removal_comment` |
| CancelledBy | 3 | A0387 | Cancelled by (Hospital/Patient) | Code | `cancelled_by` |
| Reason | 30 | A0962 | General reason for activity | String | — |
| Remark | 50 | A1020 | Remark | String | — |
| CharterCancelCode | 6 | A9651 | Charter cancellation code | Code | — |
| CharterCancelDeferInd | 3 | A9644 | Charter cancel/defer indicator | Code | — |
| CharterCancelDescription | 58 | A9643D | Charter cancellation description | String | — |
| OpCancelled | 1 | C1795 | Operation cancelled indicator (v5.0+) | Code | — |
| OpCancelledDesc | 10 | C1795B | Operation cancelled description | String | — |
| PatientChoice | 1 | C1796 | Patient choice on cancellation (v5.0+) | Code | `patient_choice` |
| PatientChoiceDesc | 20 | C1796B | Patient choice description | String | — |

#### 4.7.5 Clinician & Scheduling

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| Consultant | 6 | A0447 | Consultant code | Code | `consultant_code` |
| Specialty | 4 | A0448 | Specialty code | Code | `specialty_code` |
| Hospital | 4 | A0445 | Hospital code | Code | `hospital_code` |
| Ward | 4 | A0446 | Ward code | Code | `ward_code` |
| Category | 3 | A0449 | Patient category | Code | — |
| Urgency | 1 | A0950 | Urgency | Code | `urgency` |
| WaitingList | 6 | A9358 | Waiting list code | Code | `waiting_list_code` |
| DiagGroup | 6 | A9545 | Diagnosis group | Code | — |
| EfgCode | 4 | A5697 | EFG code | Code | — |
| HrgRankedProcedureCode | 5 | A5698 | HRG ranked procedure code | Code | — |
| HrgResourceGroup | 5 | A5696 | HRG resource group | Code | — |

#### 4.7.6 P-Booking (Patient Booking) Letters

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| FirstPbLetterSent | 10 | R9034 | First patient-booking letter sent date | Date | — |
| FirstPbReminderSent | 10 | R9035 | First reminder sent date | Date | — |
| SecondPbReminderSent | 10 | R9036 | Second reminder sent date | Date | — |
| PbResponseDate | 10 | R9037 | Patient response date | Date | — |
| RttAFDT | 3 | R1597 | RTT AFDT external | Date | `rtt_afdt` |
| RttAFDTInt | 1 | R1597A | RTT AFDT internal | Date int | — |
| PrevConsultant | 6 | A9804 | Previous consultant | Code | — |
| PrevHospital | 4 | A9803 | Previous hospital | Code | — |
| PrevSpecialty | 4 | A9805 | Previous specialty | Code | — |
| PrevWaitingList | 6 | A9542 | Previous waiting list code | Code | — |
| PrevDiagGroup | 6 | A9543 | Previous diagnosis group | Code | — |
| LastRevisionDtime | 12 | A9390 | Last revision datetime | Datetime int | Audit |
| LastRevisionUID | 4 | A9658 | Last revision user | String | Audit |

---

### 4.8 FCEEXT — Finished Consultant Episodes (Extended)
**Field count:** 68 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber` + `FceSequenceNo`
**Migration target:** LOAD_ADT_EPISODES, LOAD_ADT_CODING, LOAD_ADT_ARCHIVE

#### 4.8.1 Episode Identity

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| InternalPatientNumber | 9 | A0000 | Patient identifier | Numeric string | FK to LOAD_PMI |
| EpisodeNumber | 9 | A0142 | Episode number | Numeric string | FK to LOAD_ADT_ADMISSIONS |
| FceSequenceNo | 2 | C0272 | FCE sequence within episode | Numeric | `fce_sequence` |
| DistrictNumber | 14 | A0007C | District number | String | — |
| CaseNoteNo | 14 | C0160B | Case note number | String | `case_note_number` |
| NhsNumber | 17 | A0366B | NHS Number | String | `nhs_number` |
| Forenames | 20 | A0028 | Patient forenames | String | — |
| Surname | 24 | A0027 | Patient surname | String | — |
| Sex | 1 | A0033 | Sex | Code | — |
| Dob | 10 | A0032C | Date of birth | Date | — |
| AgeAtStartOfEpisode | 3 | C4390 | Age at FCE start | Numeric | `age_at_start` |
| Postcode | 10 | A0041 | Patient postcode | String | — |

#### 4.8.2 Episode Dates

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| FCEStartDate | 10 | A3045C | FCE start date | Date | `fce_start_date` |
| FCEStartTime | 10 | A3045 | FCE start time | Time | — |
| FCEStartDTimeInt | 12 | C8453A | FCE start datetime internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| FCEEndDate | 10 | A3045A | FCE end date | Date | `fce_end_date` |
| FCEEndTime | 10 | A3045B | FCE end time | Time | — |
| EpsActvDtimeInt | 12 | A0133A | Episode activity datetime internal | Datetime int | Audit |
| AdmissionDatetime | 16 | A0372 | Admission datetime (full episode) | Datetime | — |
| DischargeDatetime | 16 | A0348 | Discharge datetime (full episode) | Datetime | — |
| Los | 4 | C3545 | Length of stay (days) | Numeric | `length_of_stay` |
| LosForConsEps | 5 | E4161 | LOS for this consultant episode | Numeric | — |
| DaysOnWl | 6 | C4519 | Days on waiting list prior to admission | Numeric | `days_on_wl` |
| DateOnList | 16 | A0971 | Date placed on waiting list | Datetime | — |

#### 4.8.3 Clinician

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| Consultant | 6 | A0382 | Consultant code | Code | `consultant_code` |
| Specialty | 4 | A0383 | Specialty code | Code | `specialty_code` |
| EpisodicGP | 8 | H7621 | Episodic GP code | String | `episodic_gp` |
| GpCode | 8 | A0046 | Registered GP code | String | — |
| GdpCode | 6 | C4285 | GDP code | String | — |
| HaCode | 3 | C7245 | Health authority code | Code | — |
| PracticeCode | 6 | C7046 | GP practice code | String | — |

#### 4.8.4 Admission & Discharge Classification

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| HospCdadmit | 4 | A0428 | Hospital at admission | Code | `hosp_code_admit` |
| HospCdend | 4 | A0210 | Hospital at end of FCE | Code | `hosp_code_end` |
| WardCdadmit | 4 | A0429 | Ward at admission | Code | `ward_code_admit` |
| WardCdend | 4 | A0082 | Ward at end of FCE | Code | `ward_code_end` |
| MethodOfAdmission | 2 | C0211A | Method of admission code | Code | `admission_method` |
| MethodOfDischarge | 2 | A0362 | Method of discharge code | Code | `discharge_method` |
| SourceOfAdmission | 2 | A0320 | Source of admission | Code | `admission_source` |
| DestinationOnDischarge | 2 | C0206A | Destination on discharge | Code | `discharge_destination` |
| PatientCategory | 3 | A0432 | Patient category (NHS/Private) | Code | `patient_category` |
| ClassPat | 1 | A2923 | Patient class | Code | — |
| IntdMgmt | 1 | A0311 | Intended management | Code | `intended_management` |
| TheatreVisits | 2 | A0521 | Theatre visits count (v3.1+) | Numeric | — |

#### 4.8.5 Clinical Coding

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| KornerEpisodePrimaryDiagnosisCode | 7 | C4604 | Primary diagnosis ICD-10 | Code | `primary_diagnosis` |
| Subsid | 7 | C4607 | Subsidiary diagnosis ICD-10 | Code | `secondary_diagnosis` |
| KornerEpisodePrimaryProcedureCode | 5 | C4632 | Primary procedure OPCS-4 | Code | `primary_procedure` |
| KornerEpisodePrimaryProcedureDateExternal | 8 | C4634A | Primary procedure date | Date | `procedure_date` |
| ReadPrimaryDiagnosis | 8 | A6329 | READ primary diagnosis | Code | — |
| ReadPrimaryDiagTerm | 2 | A6330 | READ primary diagnosis term | Code | — |
| ReadPrimaryProcedure | 8 | A6333 | READ primary procedure | Code | — |
| ReadPrimayProcTerm | 2 | A6334 | READ primary procedure term | Code | — |
| ReadSubsidDiagnosis | 8 | A6331 | READ subsidiary diagnosis | Code | — |
| ReadSubsidDiagTerm | 2 | A6332 | READ subsidiary diagnosis term | Code | — |
| ClinicalCodingStatus | 3 | A9457B | Clinical coding status | Code | `coding_status` |

#### 4.8.6 HRG / Tariff

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| HrgCode | 5 | A5706 | HRG code | Code | `hrg_code` |
| HrgOutlierFlag | 1 | A5709 | HRG outlier flag | Boolean | `hrg_outlier` |
| HrgRankedProcedureCode | 5 | A5708 | HRG ranked procedure | Code | — |
| HrgSpecialtyUsed | 3 | A5711 | HRG specialty used | Code | — |
| HrgTrimPoint | 5 | A5710 | HRG trim point | Numeric | — |
| EfgCode | 4 | A5707 | EFG code | Code | — |

#### 4.8.7 Commissioning

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| ContractId | 6 | C7071 | Contract identifier | Code | — |
| ProviderCode | 4 | C7015 | Provider code | Code | — |
| PurchaserCode | 5 | C7000 | Purchaser code | Code | — |
| DGVPCode | 5 | A1203 | DGVP code (v3.4+) | Code | — |
| DGVPVersion | 3 | A1210 | DGVP version (v3.4+) | Code | — |
| CidGrp | 1 | C6051A | CID group | Code | — |
| CidType | 1 | C7014A | CID type | Code | — |
| OsvStatus | 1 | C8421 | Overseas visitor status | Code | — |

---

### 4.9 AEA — Accident & Emergency Attendances
**Field count:** 69 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber` (+ `AENumber`)
**Migration target:** None currently mapped — **GAP: No LOAD_AEA table in target spec**

#### 4.9.1 Attendance Core

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| InternalPatientNumber | 9 | A0000 | Patient identifier | Numeric string | (unmapped) |
| EpisodeNumber | 9 | A0142 | Episode number | Numeric string | — |
| DistrictNumber | 14 | A0007C | District number | String | — |
| AENumber | 12 | H6092 | A&E unique attendance number | String | — |
| AeAttendanceDatetimeneutral | 12 | H6087 | Attendance datetime neutral (CCYYMMDDHHMM) | Datetime int | — |
| AttendanceDate | 10 | H6087D | Attendance date | Date | — |
| AttendanceTime | 5 | H6087T | Attendance time | Time | — |
| DepartureDate | 18 | H6109A | Departure date | Date | — |
| DepartureDtTmInt | 12 | H6109 | Departure datetime internal | Datetime int | — |
| DepartureTime | 10 | A3045 | Departure time | Time | — |
| DepartmentCode | 8 | H6255 | A&E department code | Code | — |
| HospitalCode | 4 | H6254 | Hospital code | Code | — |

#### 4.9.2 Arrival & Triage

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| ModeOfArrival | 4 | H6165 | Mode of arrival code (e.g. ambulance) | Code | — |
| ObsoleteModeOfArrival | 4 | H6165 | Obsolete mode of arrival (v6.0+) | Code | Ignore |
| InitiatorOfAttendance | 4 | H6139 | Referral source / initiator | Code | — |
| ObsoleteIniOfAttend | 4 | H6139 | Obsolete version (v8.2+) | Code | Ignore |
| NewOrFU | 1 | H6167A | New or follow-up attendance | Code | — |
| PatientType | 7 | C7422 | Patient type code | Code | — |
| Consultant | 6 | A0141 | A&E consultant | Code | — |
| Specialty | 4 | A0293 | A&E specialty | Code | — |
| Cubicle | 4 | H6100 | Cubicle code | Code | — |
| AllocStreamCode | 1 | C1788 | Allocated stream (1=Minor, 2=Major, v5.0+) | Code | — |
| AllocStreamDesc | 45 | C1788D | Stream description | String | — |

#### 4.9.3 Incident Details

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| ComplaintText1 | 60 | H6099 | Presenting complaint text 1 | String | — |
| ComplaintText2 | 60 | H6099A | Presenting complaint text 2 | String | — |
| AeAdditionalDetailsWhere | 60 | A6077 | Incident location details | String | — |
| What | 60 | A6078 | What happened (incident) | String | — |
| Why | 60 | A6079 | Why it happened | String | — |
| PatientHistory | 121 | A5556U | Patient medical history | String | — |
| Comments | 255 | A6082U | General comments | String | — |
| AllergiesClaimedByPatient | 30 | C7423 | Patient-reported allergies | String | — |
| MajorIncident | 3 | H6162A | Major incident flag (YES/NO) | Code | — |
| AssaultMethod | 2 | R2836 | Assault method code (v5.1+) | Code | — |
| AssaultMethodDesc | 25 | R2834 | Assault method description | String | — |
| AssaultLocationType | 2 | R2839 | Assault location type (v5.1+) | Code | — |
| AssaultLocDesc | 255 | R2847 | Assault location description | String | — |
| ViolentIncidentExt | 3 | R2833 | Violent incident flag (v8.2+) | Code | — |

#### 4.9.4 Outcome & Disposal

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| MethodOfDeparture | 4 | H6163 | Method of departure / disposal code | Code | — |
| FollowUpRequired | 3 | H6133A | Follow-up required flag | Code | — |
| DecisionToAdmit | 12 | R9573A | Decision to admit datetime internal (v6.0+) | Datetime int | — |
| DecisionToAdmitDtEXT | 16 | R9573 | Decision to admit external | Datetime | — |
| BedReqConsultant | 6 | A0833 | Bed request consultant | Code | — |
| BedReqSpecialty | 4 | A0868 | Bed request specialty | Code | — |
| BedReqSingleRoomRequired | 3 | A7052 | Single room required flag | Code | — |
| BedReqComment | 60 | A7053 | Bed request comment | String | — |
| BedReqRevisionCount | 4 | A7054A | Bed request revision count | Numeric | — |
| AccompaniedBy | 4 | C7320 | Accompanied by code | Code | — |
| NOKInformed | 3 | H6168A | Next of kin informed | Code | — |
| CoronerInformed | 3 | H6103A | Coroner informed | Code | — |

#### 4.9.5 Trauma Scoring

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| RTS | 2 | A4689 | First Revised Trauma Score | Numeric | — |
| RTSDtTm | 16 | A3619 | First RTS datetime | Datetime | — |
| RTSDtTmInt | 12 | A3619A | First RTS datetime internal | Datetime int | — |
| RTS2 | 2 | A4694 | Second Revised Trauma Score | Numeric | — |
| RTSDtTm2 | 16 | A3621 | Second RTS datetime | Datetime | — |
| RTSDtTmInt2 | 12 | A3621A | Second RTS datetime internal | Datetime int | — |

#### 4.9.6 Call & Ambulance

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| AmbulanceNumber | 10 | H6998 | Ambulance number | String | — |
| ImmediateCall | 3 | H6214A | Immediate call flag (v3.1+) | Code | — |
| CallInDate | 18 | H6215A | Call-in date | Date | — |
| CallInDtTmInt | 12 | H6215 | Call-in datetime internal | Datetime int | — |
| CallInTime | 18 | H6215C | Call-in time | Time | — |

#### 4.9.7 Operational Timing (v8.2+)

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| ExpctTrtDtExt | 16 | R8216 | Expected treatment date external | Datetime | — |
| ExpctTrtDtINT | 12 | R8216A | Expected treatment datetime internal | Datetime int | — |
| TrtAllocDtEXT | 16 | R8217 | Treatment allocated date external | Datetime | — |
| TrtAllocDtINT | 12 | R8217A | Treatment allocated datetime internal | Datetime int | — |
| TransferredFromHosp | 10 | R9639 | Transferred from hospital (v8.2+) | Code | — |
| ReferrerId | 8 | R2821 | Referrer ID (v6.0+) | String | — |
| ReferrerType | 3 | C4454 | Referrer type (v6.0+) | Code | — |
| InterpreterLanguage | 30 | R9580 | Interpreter language (v6.0+) | String | — |
| AEHRGCode | 6 | A1152 | A&E HRG code (v3.4+) | Code | — |

---

### 4.10 SMREPISODE — Mental Health & Specialist Medical Episodes
**Field count:** 52 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber`
**Migration target:** LOAD_MH_DETENTION_MASTER, LOAD_MH_DETENTION_TRANSFERS, LOAD_MH_CPA_MASTER, LOAD_MH_CPA_HISTORY, LOAD_DETENTION_ARCHIVE, LOAD_CPA_ARCHIVE

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| InternalPatientNumber | 9 | A0000 | Patient identifier | Numeric string | FK to LOAD_PMI |
| EpisodeNumber | 9 | A0142 | Episode number | Numeric string | `source_ep_number` |
| HospitalCode | 4 | A0210 | Hospital code | Code | `hospital_code` |
| WardCode | 4 | A0082 | Ward code | Code | `ward_code` |
| ConsultantCode | 6 | A0199 | Responsible consultant code | Code | `consultant_code` |
| SpecialtyCode | 4 | A0087 | Specialty code | Code | `specialty_code` |
| CategoryCode | 3 | A0089 | Patient category code | Code | — |
| EpisodeStartDate | 10 | A3045 | Episode start date | Date | `episode_start_date` |
| EpisodeStartTime | 10 | A3045A | Episode start time | Time | — |
| EpisodeStartDtTmInt | 12 | A0133A | Episode start datetime internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| AdmissionMethod | 2 | A8816 | Admission method (MHA section) | Code | `admission_method` |
| AdmissionSource | 2 | A8804 | Admission source | Code | `admission_source` |
| AdmissionFrom | 5 | A4391 | Admitted from location | Code | — |
| IntendManagement | 1 | A8803 | Intended management | Code | `intended_management` |
| StartReason | 2 | A4330 | Reason for episode start | Code | `start_reason` |
| StartPsychStatus | 1 | A4394 | Mental Health Act status at start | Code | `mha_status_start` |
| StartPsychStatusDesc | 40 | A4394D | MHA status description at start | String | — |
| StartClinFacility | 3 | A4363 | Clinical facility at start | Code | `start_facility` |
| CareTypePsych | 1 | A4438 | Psychiatric care type | Code | `care_type_psych` |
| CareTypeGeri | 1 | A4438G | Geriatric care type | Code | `care_type_geri` |
| ConditionICD10 | 7 | A4505 | Principal condition (ICD-10) | Code | `primary_diagnosis` |
| ConditionDesc | 45 | A4506 | Principal condition description | String | — |
| SocialFactorICD10 | 7 | A4401 | Social factor (Z-code ICD-10) | Code | `social_factor` |
| SocialFactorDesc | 45 | A4401D | Social factor description | String | — |
| SignificantFacility | 2 | A4350 | Significant treatment facility | Code | — |
| AftercareCode1 | 1 | A4433P | Aftercare section 117 code 1 | Code | `aftercare_1` |
| AftercareCode2 | 1 | A4433Q | Aftercare section 117 code 2 | Code | `aftercare_2` |
| AfterCare3 | 1 | A4433R | Aftercare code 3 | Code | `aftercare_3` |
| AfterCare4 | 1 | A4433S | Aftercare code 4 | Code | `aftercare_4` |
| AfterCareDesc1–4 | 48 | A4433D–G | Aftercare descriptions 1–4 | String | — |
| EndCarePlan | 3 | A4431 | End of care plan indicator | Code | — |
| EndCarePlanInt | 1 | A4431A | End of care plan internal | Boolean | — |
| EndClinFacility | 3 | A4426 | Clinical facility at end of episode | Code | — |
| EndToLocation | 5 | A4437 | Location at end of episode | Code | `end_location` |
| MethodOfDischarge | 2 | A8812 | Method of discharge | Code | `discharge_method` |
| DestinationCode | 2 | A8805 | Destination on discharge | Code | `discharge_destination` |
| ReferralFrom | 1 | A4396 | Referred from code | Code | — |
| GPReferralLetterNumber | 6 | A4383 | GP referral letter number | String | — |
| GPReferralLetterNumber_1 | 6 | A4413 | GP referral letter number (alt) | String | — |
| ReadyTransferDate | 10 | A8814 | Ready for transfer date | Date | `ready_transfer_date` |
| ReadyTransferTime | 10 | A3045B | Ready for transfer time | Time | — |
| ReadyTransferDtTmInt | 12 | A8814A | Ready transfer datetime internal | Datetime int | Preferred |
| MhlsCensusDate | 10 | A8837 | MHLS census date | Date | `mhls_census_date` |
| MhlsCensusDtInt | 8 | A8837A | MHLS census date internal (CCYYMMDD) | Date int | Preferred |
| MraNumber | 2 | C0272M | Mental health record area number | Numeric | — |
| PsychStatusDesc | 50 | A6946B | Psychiatric status description | String | — |
| PsychStatusPrev | 1 | A6946S | Previous psychiatric status | Code | — |
| CodingComplete | 1 | A9457 | Clinical coding complete flag | Boolean | `coding_complete` |
| QueryStatus | 1 | A8890 | Query status flag | Code | — |

---

### 4.11 CPSGREFERRAL — Community & Service Group Referrals
**Field count:** 46 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber`
**Migration target:** LOAD_CMTY_APPOINTMENTS

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| InternalPatientNumber | 9 | A0000 | Patient identifier | Numeric string | FK to LOAD_PMI |
| EpisodeNumber | 9 | A0142 | Episode number | Numeric string | `source_ep_number` |
| Casenote | 14 | A7726 | Case note number | String | `case_note_number` |
| CasenoteInt | 14 | A7726A | Case note number internal | String | — |
| ServGroup | 4 | A7759 | Service group code | Code | `service_group` |
| LeadClinician | 8 | A7651 | Lead clinician code | Code | `lead_clinician` |
| ReferralDate | 10 | A3045 | Referral date | Date | `referral_date` |
| ReferralTime | 10 | A3045A | Referral time | Time | — |
| RefDtTmInt | 12 | A7760A | Referral datetime internal (CCYYMMDDHHMM) | Datetime int | Preferred |
| Source | 3 | A7772 | Referral source code | Code | `referral_source` |
| Type | 11 | A7773 | Referral type | String | `referral_type` |
| TypeInt | 1 | A7773A | Referral type internal code | Code | — |
| Category | 3 | A7774 | Referral category | Code | `category` |
| Priority | 9 | A7775 | Priority | String | `priority` |
| PriorityInt | 2 | A7775A | Priority internal code | Code | — |
| ReferralPriority | 7 | A4666 | Referral priority (detailed) | Code | — |
| ClinicalCategory | 4 | A6087 | Clinical category | Code | `clinical_category` |
| PatientGrouping | 4 | A6094 | Patient grouping | Code | — |
| ReferrerType | 3 | C4454 | Referrer type (v5.1+) | Code | `referrer_type` |
| ReferrerId | 8 | R2821 | Referrer identifier (v5.1+) | String | `referrer_id` |
| ReferrerSpecialty | 4 | R2810 | Referrer specialty (v5.1+) | Code | `referrer_specialty` |
| ReferrerName | 35 | A4625 | Referrer name | String | `referrer_name` |
| Disabled | 3 | A8048 | Disability indicator (YES/NO) | Code | — |
| DisabledInt | 1 | A8048A | Disability indicator internal | Boolean | — |
| PredictedOutcomeOfReferral | 4 | A8306 | Predicted outcome code | Code | — |
| Outcome | 4 | A7781 | Actual outcome code | Code | `outcome` |
| Status | 9 | A7758 | Referral status (SG/SG DSCH) | String | `status` |
| StatusInt | 2 | A7758A | Referral status internal | Code | — |
| PrimDiag | 4 | A7776 | Primary diagnosis code | Code | `primary_diagnosis` |
| PrimDiagSeverity | 4 | A7777 | Primary diagnosis severity | Code | — |
| PrimDiagOutcome | 4 | A7778 | Primary diagnosis outcome | Code | — |
| SubsDiag | 4 | A8248 | Subsidiary diagnosis | Code | — |
| SubsDiagSeverity | 4 | A8249 | Subsidiary diagnosis severity | Code | — |
| SubsDiagOutcome | 4 | A8250 | Subsidiary diagnosis outcome | Code | — |
| SubsidOutcome | 4 | A8250 | Subsidiary outcome | Code | — |
| DiagComment1 | 60 | A7779 | Diagnostic comment 1 | String | — |
| DiagComment2 | 60 | A3710 | Diagnostic comment 2 | String | — |
| DischargeDate | 10 | A3045B | Discharge date | Date | `discharge_date` |
| DischargeTime | 10 | A3045C | Discharge time | Time | — |
| DischargeDtTmInt | 12 | A7782A | Discharge datetime internal | Datetime int | Preferred |
| DischargeReason | 4 | A7783 | Discharge reason code | Code | `discharge_reason` |
| ReturnPeriod | 2 | A6099 | Return period (months) | Numeric | — |
| Timeslot | 3 | A6073 | Timeslot code | Code | — |
| Edc | 10 | C1151 | Expected discharge / completion date (v4.2+) | Date | `expected_discharge` |
| EdcInternal | 10 | C1151A | EDC internal | Date int | — |
| NotUsed | 10 | A3132 | Deprecated field | — | Ignore |

---

### 4.12 HWSAPP — Hospital Waiting Service Applications (Community OPD)
**Field count:** 90 | **Primary keys:** `InternalPatientNumber` + `EpisodeNumber`
**Migration target:** LOAD_CMTY_APPOINTMENTS (partial — community OPD appointments)

> HWSAPP is structurally very similar to OPA (outpatient appointments) but applies to community/service group outpatient clinics. It adds `ApplicationIndicator`, `ProgOfCare`, `ClinicianSpecialty`, `ClinicianSubSpec`, and `SGReasonForRef1–5` specific to community care pathways.

Key differences from OPA:

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| ApplicationIndicator | 1 | H0298A | Application indicator (1=IP, 2=OP, 3=SG) | Code | `application_type` |
| ProgOfCare | 1 | A7385 | Programme of care code (v4.0+) | Code | `programme_of_care` |
| ProgOfCareDesc | 25 | A7385B | Programme of care description | String | — |
| ClinicianSpecialty | 4 | R1157 | Clinician specialty (PCxx) | Code | `clinician_specialty` |
| ClinicianSubSpec | 5 | R1158 | Clinician sub-specialty (PCxx) | Code | — |
| SGReasonForRef1 | 4 | R1577 | SG reason for referral 1 (PCxx) | Code | `referral_reason_1` |
| SGReasonForRef2 | 4 | R1578 | SG reason for referral 2 | Code | — |
| SGReasonForRef3 | 4 | R1579 | SG reason for referral 3 | Code | — |
| SGReasonForRef4 | 4 | R1580 | SG reason for referral 4 | Code | — |
| SGReasonForRef5 | 4 | R1581 | SG reason for referral 5 | Code | — |
| RttPeriodStatus | 4 | R2223 | RTT period status (PCxx) | Code | LOAD_RTT_PERIODS |
| UserId | 4 | C4333 | User ID | String | Audit |
| WNBReasonCode | — | — | (Not present — see OPA for comparison) | — | — |

All remaining 80 fields are identical in name and semantics to OPA. See OPA schema (§4.3) for full field listing.

---

### 4.13 ADTLADDCOR — ADT Address Corrections Audit
**Field count:** 23 | **Primary key:** `Intpatno` + `SeqNo` + `Transactdatetime`
**Migration target:** LOAD_PMIADDRS

> This table is an audit trail of patient address changes. Each row records the old address and new address at the time of a correction transaction.

| Field | Sz | Code | Description | Type | Migration Target |
|-------|----|------|-------------|------|-----------------|
| Intpatno | 9 | H0179 | Internal patient number | Numeric string | FK to LOAD_PMI |
| Districtnumber | 14 | C4353A | District number | String | — |
| SeqNo | 3 | A0152 | Sequence number within patient | Numeric | — |
| TransactType | 2 | H0120A | Transaction type code | Code | `address_change_type` |
| Transactdatetime | 14 | H0178A | Transaction datetime | Datetime int | `effective_from_datetime` |
| TransactDate | — | — | Date of transaction (CCYYMMDD) | Date int | — |
| Transactuserid | 4 | A8366 | User who made the change | String | Audit |
| Newaddline1 | 20 | A0037 | New address line 1 | String | `add_line_1` |
| Newaddline2 | 20 | A0038 | New address line 2 | String | `add_line_2` |
| Newaddline3 | 20 | A0039 | New address line 3 | String | `add_line_3` |
| Newaddline4 | 20 | A0040 | New address line 4 | String | `add_line_4` |
| Newpostcode | 10 | A0041 | New postcode | String | `postcode` |
| Newpseudopostcode | 10 | C4629 | New pseudo postcode | String | — |
| Oldaddline1 | 20 | C7139 | Old address line 1 | String | `prev_add_line_1` |
| Oldaddline2 | 20 | C7140 | Old address line 2 | String | `prev_add_line_2` |
| Oldaddline3 | 20 | C7141 | Old address line 3 | String | `prev_add_line_3` |
| Oldaddline4 | 20 | C7142 | Old address line 4 | String | `prev_add_line_4` |
| Oldpostcode | 8 | C7143 | Old postcode | String | `prev_postcode` |
| Oldpseudopostcode | 8 | C7144 | Old pseudo postcode | String | — |
| PmiPatientAddressNewEffectiveDateFromInt | 12 | A9284A | New address effective from datetime | Datetime int | `new_eff_from` |
| PmiPatientAddressNewEffectiveDateToInt | 12 | A9289A | New address effective to datetime | Datetime int | `new_eff_to` |
| PmiPatientAddressOldEffectiveDateFromInt | 12 | A9241A | Old address effective from datetime | Datetime int | `old_eff_from` |
| PmiPatientAddressOldEffectiveDateToInt | 12 | A9252A | Old address effective to datetime | Datetime int | `old_eff_to` |

**Note:** To produce `LOAD_PMIADDRS`, this table must be joined with `PATDATA` to obtain `PtDoB` (DOB is required as a mandatory field in the target but is not stored in ADTLADDCOR).

---

## 5. Cross-Table Relationship Diagram

```
PATDATA (A0000)
    ├── ADTLADDCOR (Intpatno) ──► LOAD_PMIADDRS
    ├── ADMITDISCH (A0000 + A0142)
    │       └── FCEEXT (A0000 + A0142 + FceSequenceNo)
    │               ──► LOAD_ADT_EPISODES, LOAD_ADT_CODING, LOAD_ADT_ARCHIVE
    │       └── WLENTRY / WLCURRENT (A0000 + A0142) ──► LOAD_IWL
    │               └── WLACTIVITY (A0000 + A0142) ──► LOAD_IWL_TCIS, LOAD_IWL_DEFERRALS
    ├── OPA (A0000 + A0142) ──► LOAD_OPD_APPOINTMENTS, LOAD_OPD_ARCHIVE
    │       └── OPREFERRAL (A0000 + A0142) ──► LOAD_REFERRALS, LOAD_RTT_PATHWAYS
    ├── CPSGREFERRAL (A0000 + A0142) ──► LOAD_CMTY_APPOINTMENTS
    ├── HWSAPP (A0000 + A0142) ──► LOAD_CMTY_APPOINTMENTS (community OPD)
    ├── SMREPISODE (A0000 + A0142) ──► LOAD_MH_DETENTION_MASTER, LOAD_CPA_ARCHIVE
    └── AEA (A0000 + A0142) ──► (NO TARGET — GAP)
```

**Key linkage rule:** All target tables require `loadpmi_record_number` (the surrogate key generated by `LOAD_PMI` load). This must be resolved at load time by looking up `InternalPatientNumber` → `loadpmi_record_number` via a staging lookup table.

---

## 6. Data Profiling: Field Size Distribution

| Size Range | Field Count | % | Notes |
|------------|-------------|---|-------|
| 1 char | ~450 | 8.4% | Flags, codes, boolean indicators |
| 2–4 chars | ~800 | 14.9% | Short codes (specialty, ward, sex, method) |
| 5–9 chars | ~600 | 11.1% | Patient numbers, GP codes, A&E numbers |
| 10 chars | ~550 | 10.2% | Dates (external display format) |
| 12 chars | ~600 | 11.1% | Datetime internals (CCYYMMDDHHMM) |
| 14–20 chars | ~500 | 9.3% | Names, address lines (short) |
| 20–35 chars | ~500 | 9.3% | Names, descriptions, address lines (extended) |
| 36–60 chars | ~600 | 11.1% | Comments, reasons, descriptions |
| 60–255 chars | ~350 | 6.5% | Free text, clinical notes |
| Variable/other | ~430 | 8.0% | Blobs, memo fields, calculated |

---

## 7. Known Data Quality Issues

| Issue | Tables Affected | Severity | Recommendation |
|-------|----------------|----------|----------------|
| NHS Number format variation | PATDATA, OPA, FCEEXT, WLENTRY | High | Normalise using NHS Number checker algorithm |
| Dual gender coding (Sex + CurrentGender) | PATDATA, OPA, HWSAPP | Medium | Use `CurrentGender` if populated, else `Sex` |
| Date-only fields stored as datetime strings | All tables | Medium | Parse with both date-only and datetime parsers |
| Postcode pseudo-coding (suppressed) | PATDATA | Medium | Do not map `PtPseudoPostCode` to real address |
| Episode number gaps | ADMITDISCH, FCEEXT | High | Validate referential integrity before load |
| Obsolete fields still populated | OPA, AEA | Low | Document and exclude from migration |
| Missing mandatory `InternalPatientNumber` | ADTLADDCOR (`Intpatno`) | High | Field name differs — apply alias in extract |
| GP code format (8-char vs 6-char ODS) | All GP fields | High | Normalise to ODS format before crosswalk |
| Death indicators inconsistency | PATDATA | Medium | Cross-validate `PtDeathIndInt` vs `PtDateOfDeathInt` |
| Version-gated fields populated in older records | All tables | Low | Treat as nullable for records pre-release date |

---

*Document generated: 2026-02-25 | Source catalog: `schemas/source_schema_catalog.csv` (417 tables, 5,387 fields)*
