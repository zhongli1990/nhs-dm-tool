# Mapping Gap Register — NHS Queen Victoria Hospital EPR/PAS Migration
**Date:** 2026-02-25
**Source System:** PC60/V83 Legacy PAS (417 tables, 5,387 fields)
**Target System:** PAS 18.4 (38 LOAD_ tables, 880 fields)
**Version:** 2.0 — Full 38-table coverage

---

## Why Were Only 2 Tables Mapped Before?

The initial pipeline (`mapping_spec.json` v1.0) was a **proof-of-concept baseline** to validate the extraction and transformation pipeline end-to-end. The two tables chosen were:

1. **PATDATA → LOAD_PMI** — the most critical entity (patient identity), with the most complete source data
2. **ADMITDISCH → LOAD_ADT_ADMISSIONS** — the core clinical transaction, validating the episode-linkage pattern

The intent was always to extend domain-by-domain. No other domain had been mapped because:
- The authoritative target spec (PDF) is marked **"FOR REF ONLY NOT TO BE USED"** — confirmation of the approved contract was pending
- Code-set crosswalk tables (sex, ethnicity, admission type, RTT status etc.) had not yet been agreed with the vendor
- FK linkage strategy (how LOAD_PMI.record_number links to LOAD_PMIIDS, etc.) was unresolved
- Source table field names for WLCURRENT, WLACTIVITY, SMREPISODE had not been verified against the actual live database

This v2.0 mapping spec now covers all 38 target tables.

---

## Coverage Summary (v2.0)

| Metric | Count |
|---|---|
| Target tables | 38 |
| Mapped (source data exists) | 33 |
| Reference/config only (no source table) | 5 |
| Source tables with mappings | 10 |
| Source tables unmapped | 407 |

---

## Table-Level Gap Register

### ✅ MAPPED — With Direct Source

| Target Table | Source Table | Fields Mapped | Gaps |
|---|---|---|---|
| LOAD_PMI | PATDATA | 41 | See G-PMI-* below |
| LOAD_PMIIDS | PATDATA | 3 | Row-splitting; FK linkage |
| LOAD_PMIALIASES | PATDATA | 6 | Row-splitting for 3 previous surnames |
| LOAD_PMIADDRS | ADTLADDCOR | 7 | DOB/marital join; current address second pass |
| LOAD_PMICONTACTS | PATDATA | 12 | Name-split; carer row-split |
| LOAD_PMIALLERGIES | PATDATA | 2 | Row-split for 2nd allergy; codeset |
| LOAD_PMISTAFFWARNINGS | PATDATA | 2 | Row-split for 2nd risk code; codeset |
| LOAD_PMIGPAUDIT | PATDATA | 2 | Practice code join; no history |
| LOAD_PMICASENOTEHISTORY | PATDATA | 2 | Casenote system data missing |
| LOAD_RTT_PATHWAYS | OPREFERRAL | 6 | UBRN; pathway_id semantics |
| LOAD_REFERRALS | OPREFERRAL | 12 | encounter_type; mandatory dates |
| LOAD_RTT_PERIODS | OPREFERRAL | 5 | clock_stop null for active; table join |
| LOAD_RTT_EVENTS | OPREFERRAL | 5 | Event history not in legacy PAS |
| LOAD_OPDWAITLIST | OPA | 12 | FK linkages; status codeset |
| LOAD_OPDWAITLISTDEF | OPA | 5 | Mandatory dates; filter on cancellation |
| LOAD_OPD_APPOINTMENTS | OPA | 16 | time_arrived/seen/complete missing |
| LOAD_OPD_CODING | OPA | 3 | Row-split; diagnosis_date missing |
| LOAD_OPD_ARCHIVE | OPA | 25 | Address join; GP name; times |
| LOAD_CMTY_APPOINTMENTS | CPSGREFERRAL | 12 | Appointment-level data missing |
| LOAD_IWL | WLCURRENT | 17 | Field names inferred; FK linkage |
| LOAD_IWL_DEFERRALS | WLACTIVITY | 7 | Field names inferred; FK linkage |
| LOAD_IWL_TCIS | WLACTIVITY | 10 | Field names inferred; mandatory dates |
| LOAD_ADT_ADMISSIONS | ADMITDISCH | 13 | Mandatory nulls; codeset |
| LOAD_ADT_EPISODES | FCEEXT | 4 | FK linkage; PDF may be incomplete |
| LOAD_ADT_WARDSTAYS | ADMITDISCH | 7 | Multi-ward transfers not captured |
| LOAD_ADT_CODING | FCEEXT | 3 | Row-split; diagnosis_date |
| LOAD_MH_DETENTION_MASTER | SMREPISODE | 5 | Field names inferred; MHA scope |
| LOAD_MH_DETENTION_TRANSFERS | SMREPISODE | 8 | Field names inferred; MHA data may be elsewhere |
| LOAD_MH_CPA_MASTER | SMREPISODE | 6 | Field names inferred; FK linkage |
| LOAD_MH_CPA_HISTORY | SMREPISODE | 8 | Field names inferred; FK linkage |
| LOAD_ADT_ARCHIVE | FCEEXT | 27 | Address/GP join; multiple coding rows |
| LOAD_DETENTION_ARCHIVE | SMREPISODE | 16 | Field names inferred |
| LOAD_CPA_ARCHIVE | SMREPISODE | 16 | Field names inferred |

### ⚠️ REFERENCE / CONFIGURATION ONLY — No Source Table

| Target Table | Gap Description | Action Required |
|---|---|---|
| LOAD_STAFF | No staff master table in legacy PAS scope | Extract distinct consultant/GP codes from ADMITDISCH, OPA, FCEEXT as seed; supplement from HR/Active Directory |
| LOAD_USERS | No user master table in legacy PAS scope | Obtain from IT department / Active Directory export |
| LOAD_SITES | No site master table in legacy PAS scope | Obtain from ODS (Organisation Data Service) or hospital configuration |
| LOAD_CASENOTELOCS | No casenote location table in legacy PAS scope | Obtain from hospital library management system |
| LOAD_IWL_PROFILES | No waiting list profile table in legacy PAS scope | Extract from PAS application configuration with clinical teams |

---

## Field-Level Gap Register

### G-SPEC-001 🔴 CRITICAL — Target Specification Not Authoritative
**Affected tables:** All 38
**Description:** The target PDF spec is explicitly marked **"FOR REF ONLY NOT TO BE USED"**. All field definitions, mandatory flags, and data types are provisional.
**Action:** Obtain the signed-off vendor data migration specification before finalising any field-level mapping.
**Risk:** HIGH — all mandatory field logic and codeset definitions may change.

---

### G-SPEC-002 🔴 CRITICAL — PDF Parse Artefacts in Target Field Names
**Affected tables:** Most LOAD_ tables
**Description:** Target catalog average parse confidence is 81.9%. Fields like `ge_date`, `ge_typee`, `ged`, `ge_toe`, `ge_methode`, `ge_specialty`, `ge_consultant`, `ged_by_staff_id`, `appointments`, `must`, `before`, `ranges`, `table`, `indicates` are likely PDF parsing artefacts where column suffix text merged with the next field name.
**Action:** Verify each low-confidence field name (<0.85) against the authoritative vendor spec.
**Risk:** HIGH — mapping to wrong target field name will cause silent data misrouting.

---

### G-CODE-001 🔴 CRITICAL — Sex/Gender Codeset Not Mapped
**Affected tables:** LOAD_PMI, LOAD_PMIALIASES, LOAD_OPD_ARCHIVE, LOAD_ADT_ARCHIVE, LOAD_DETENTION_ARCHIVE, LOAD_CPA_ARCHIVE
**Description:** Source `PATDATA.CurrentGender` uses codes 1=Male, 2=Female, 9=Not Specified. Target uses a string-based sex codeset. Mapping not yet defined.
**Action:** Obtain PAS18.4 sex codeset from vendor; implement transform.

---

### G-CODE-002 🔴 CRITICAL — Ethnicity Codeset Not Mapped
**Affected tables:** LOAD_PMI
**Description:** `PATDATA.EthnicType` uses a 4-char local code. Target `ethnic_group` uses NHS 16+1 ethnic category codes. No crosswalk defined.
**Action:** Produce source-to-NHS ethnicity crosswalk with data governance team.

---

### G-CODE-003 🟡 HIGH — Admission Type/Method Codesets Not Mapped
**Affected tables:** LOAD_ADT_ADMISSIONS, LOAD_ADT_ARCHIVE
**Description:** `ADMITDISCH.MethodOfAdmission`, `SourceOfAdm`, `MethodOfDischarge`, `DestinationOnDischarge` use 1-2 char local codes. Target requires PAS18.4 coded values.
**Action:** Obtain source-to-target codeset crosswalks from vendor migration pack.

---

### G-CODE-004 🟡 HIGH — RTT Period Status Codeset Not Mapped
**Affected tables:** LOAD_RTT_PATHWAYS, LOAD_REFERRALS, LOAD_RTT_PERIODS, LOAD_RTT_EVENTS
**Description:** `OPREFERRAL.RTTPeriodStatus` is a 4-char local code. Target expects PAS18.4 RTT status codes.
**Action:** Obtain codeset crosswalk; map source status codes to 18-week RTT standard codes.

---

### G-CODE-005 🟡 HIGH — Ward/Specialty/Consultant Codesets Not Mapped
**Affected tables:** LOAD_ADT_ADMISSIONS, LOAD_ADT_WARDSTAYS, LOAD_ADT_EPISODES, LOAD_IWL, LOAD_OPD_APPOINTMENTS
**Description:** Source ward codes (4-char), specialty codes (4-char), and consultant codes (6-char) are legacy system codes. Target requires PAS18.4 equivalents.
**Action:** Produce reference data crosswalk files for wards, specialties, and consultants.

---

### G-CODE-006 🟡 HIGH — Marital Status, Religion, Occupation Codesets Not Mapped
**Affected tables:** LOAD_PMI, LOAD_PMIADDRS
**Description:** `PATDATA.MaritalStatus` (1-char), `Religion` (4-char), `Occupation` (20-char) use local codes.
**Action:** Map to PAS18.4 code values with data governance.

---

### G-CODE-007 🟡 HIGH — Legal Status / Mental Category (MHA) Codesets Not Mapped
**Affected tables:** LOAD_MH_DETENTION_MASTER, LOAD_MH_DETENTION_TRANSFERS, LOAD_DETENTION_ARCHIVE
**Description:** `SMREPISODE.LegalStatus` and `MentalCategory` use local mental health act codes.
**Action:** Map to standard MHA section codes with MH informatics team.

---

### G-DATE-001 🟡 HIGH — Date Format Transforms Not Implemented
**Affected tables:** All tables with DATE fields
**Description:** Source dates exist in multiple formats: `DD/MM/YYYY HH:MM`, `CCYYMMDDHHMM` (internal integer), `CCYYMMDD`. Target DATE fields expect `DD/MM/YYYY`. No date transform is implemented in the current pipeline.
**Action:** Implement date format normalisation in `transform.py` per source field.

---

### G-FK-001 🔴 CRITICAL — Foreign Key Linkage Strategy Not Implemented
**Affected tables:** All child tables (LOAD_PMIIDS, LOAD_PMIADDRS, LOAD_PMICONTACTS, LOAD_PMIALLERGIES, LOAD_PMISTAFFWARNINGS, LOAD_PMIGPAUDIT, LOAD_PMICASENOTEHISTORY, LOAD_PMIALIASES, LOAD_REFERRALS, LOAD_RTT_PERIODS, LOAD_RTT_EVENTS, LOAD_OPDWAITLIST, LOAD_OPDWAITLISTDEF, LOAD_OPD_APPOINTMENTS, LOAD_OPD_CODING, LOAD_CMTY_APPOINTMENTS, LOAD_IWL, LOAD_IWL_DEFERRALS, LOAD_IWL_TCIS, LOAD_ADT_EPISODES, LOAD_ADT_WARDSTAYS, LOAD_ADT_CODING, LOAD_MH_DETENTION_MASTER, LOAD_MH_DETENTION_TRANSFERS, LOAD_MH_CPA_MASTER, LOAD_MH_CPA_HISTORY)
**Description:** All child LOAD_ tables require a parent record_number FK (e.g., `loadpmi_record_number`, `adt_adm_record_number`, `loadref_record_number`). The current pipeline assigns AUTO-incremented integers that do not correctly cross-reference parent records.
**Action:** Implement a surrogate key resolution step: after loading parent tables, build an `external_system_id → record_number` lookup and populate child FK fields from that lookup before writing child CSVs. This is a **critical blocker** for production load.

---

### G-ROW-001 🟡 HIGH — Row-Splitting Not Implemented
**Affected tables:** LOAD_PMIIDS (OldNHSNumber), LOAD_PMIALIASES (PreviousSurname2, PreviousSurname3, BirthName), LOAD_PMIALLERGIES (Allergies_1), LOAD_PMISTAFFWARNINGS (RiskFactorCode_1), LOAD_PMICONTACTS (carer), LOAD_ADT_CODING (secondary diagnoses), LOAD_OPD_CODING (secondary diagnoses)
**Description:** Some source fields must produce multiple target rows from a single source row. The current pipeline has no row-splitting mechanism.
**Action:** Implement a `row_split_rules` section in mapping_spec.json and a corresponding transform function.

---

### G-JOIN-001 🟡 HIGH — Cross-Table Joins Not Implemented
**Affected tables:** LOAD_PMIADDRS (needs DOB from PATDATA), LOAD_OPD_ARCHIVE (needs address from PATDATA), LOAD_ADT_ARCHIVE (needs address from PATDATA), LOAD_REFERRALS (needs encounter_type from OPA)
**Description:** Some target fields require data from multiple source tables. The current single-source-table-per-migration design cannot handle these.
**Action:** Implement a join capability in the pipeline, or pre-produce enriched denormalised source extracts.

---

### G-MAND-001 🔴 CRITICAL — Mandatory Fields Fail on Live Data
**Affected tables:** LOAD_PMI (date_registered, entered_country), LOAD_ADT_ADMISSIONS (wl_date, estimated_discharge_date, discharge_date for current inpatients), LOAD_OPD_APPOINTMENTS (time_arrived, time_seen, time_complete), LOAD_REFERRALS (ref_discharge_date), LOAD_IWL (removed), LOAD_RTT_PERIODS (clock_stop)
**Description:** These fields are marked mandatory in the target catalog but will be NULL for a significant proportion of source records (e.g., emergency admissions have no WL date; current inpatients have no discharge date; OPA does not store arrival/seen times).
**Action:**
1. Confirm with vendor whether these mandatory hints are correct
2. Define default values or NULL-handling strategy with clinical informatics
3. Consider whether live/current records should be excluded from archive tables

---

### G-SCOPE-001 🟡 HIGH — Emergency Attendance (AEA) Not Mapped
**Affected tables:** No LOAD_AEA in target — emergency data loads into LOAD_ADT_ARCHIVE
**Description:** Source `AEA` table has 69 fields. Emergency attendance data has no direct target table mapping. Historical ED data would need to be mapped to LOAD_ADT_ARCHIVE.
**Action:** Define AEA → LOAD_ADT_ARCHIVE mapping. Note: encounter_type='AE' in LOAD_ADT_ARCHIVE.

---

### G-SCOPE-002 🟡 HIGH — 407 Source Tables Have No Target Mapping
**Description:** The 417 source tables include many tables not in scope for PAS18.4 load (audit logs, report tables, system configuration, etc.). A formal scoping exercise is required to confirm which source tables contain clinically significant data that must be migrated.
**Action:**
1. Classify all 417 source tables as: IN-SCOPE / OUT-OF-SCOPE / ARCHIVE-ONLY
2. Document the classification rationale
3. Obtain sign-off from clinical informatics and data governance

---

### G-SCOPE-003 🟡 HIGH — WLCURRENT/WLACTIVITY Field Names Not Verified
**Affected tables:** LOAD_IWL, LOAD_IWL_DEFERRALS, LOAD_IWL_TCIS
**Description:** Field names used in the mapping spec for WLCURRENT and WLACTIVITY (e.g., `LastReviewDate`, `WlStatus`, `DeferralStartDate`, `TciDate`) are inferred from domain knowledge. The actual 90-field and 68-field source tables have not been individually cataloged for field names.
**Action:** Export actual WLCURRENT/WLACTIVITY field names from the legacy database and reconcile with mapping spec.

---

### G-SCOPE-004 🟡 HIGH — SMREPISODE Field Names Not Verified
**Affected tables:** LOAD_MH_DETENTION_MASTER, LOAD_MH_DETENTION_TRANSFERS, LOAD_MH_CPA_MASTER, LOAD_MH_CPA_HISTORY, LOAD_DETENTION_ARCHIVE, LOAD_CPA_ARCHIVE
**Description:** SMREPISODE field names in the mapping spec (e.g., `LegalStatus`, `MentalCategory`, `CpaType`, `Caseholder`, `LeadClinician`, `NextReviewDate`) are inferred. The actual 52-field SMREPISODE table must be verified.
**Action:** Export actual SMREPISODE field catalog and reconcile. Consider whether formal MHA detention data is actually in SMREPISODE or in a dedicated table outside current scope.

---

### G-SCOPE-005 🟡 HIGH — No Cancer Registry Mapping
**Affected tables:** No direct target equivalent
**Description:** Source contains `IPCANCERREG` (57 fields), `OPCANCERREG` (54 fields), `CANCERSUMMARY` (49 fields). Target PAS18.4 does not appear to have a dedicated cancer load table. Cancer data may need to be sent to a separate cancer registry (Somerset Cancer Register or equivalent).
**Action:** Confirm cancer data migration route with project sponsor.

---

### G-SCOPE-006 🟡 HIGH — No Critical Care Mapping
**Affected tables:** No direct target equivalent in load tables
**Description:** Source contains `CRITICALCARENEONATE` (57 fields), `CRITICALCAREACTYDTPAED` (49 fields). Target PAS18.4 critical care load tables are not in the target catalog.
**Action:** Confirm critical care migration route. May require CCMDS submission or separate system.

---

### G-QUAL-001 🟢 MEDIUM — Allergy/Risk Codeset Translations Required
See G-CODE-001 through G-CODE-007 above.

---

### G-QUAL-002 🟢 MEDIUM — GP National Codes May Not Match ODS Spine
**Affected tables:** LOAD_PMI, LOAD_PMIGPAUDIT, LOAD_REFERRALS, LOAD_OPD_APPOINTMENTS
**Description:** `PATDATA.GpCode` is a legacy 8-char local GP code. Target `gp_national_code` expects the national GMP code (7-char format G1234567). A GP code lookup against ODS is required.
**Action:** Implement GP code → national GMP code lookup using ODS API or extract.

---

## Actions Summary

| Priority | Action | Owner |
|---|---|---|
| 🔴 P1 | Obtain authoritative target data migration specification from PAS18.4 vendor | Project Manager |
| 🔴 P1 | Confirm and classify all 417 source tables (in-scope vs out-of-scope) | Data Architect |
| 🔴 P1 | Implement FK surrogate key resolution strategy | Technical Lead |
| 🟡 P2 | Produce all code-set crosswalk files (sex, ethnicity, admission type, RTT status, ward, specialty, consultant) | Data Analyst + Clinical Informatics |
| 🟡 P2 | Implement date format normalisation in transform.py | Developer |
| 🟡 P2 | Implement row-splitting transform capability | Developer |
| 🟡 P2 | Verify WLCURRENT, WLACTIVITY, SMREPISODE field names from live DB | DBA |
| 🟡 P2 | Define AEA → LOAD_ADT_ARCHIVE mapping | Data Analyst |
| 🟢 P3 | Implement cross-table join capability or produce denormalised source extracts | Developer |
| 🟢 P3 | Resolve mandatory field NULL-handling strategy for current inpatients, active RTT etc. | Clinical Informatics + Vendor |
| 🟢 P3 | Confirm cancer and critical care data migration routes | Project Sponsor |
| 🟢 P3 | GP code → national ODS code lookup implementation | Developer |

---

## Status Update After E2E Dry Run (2026-02-25)

Lifecycle execution status:
- `extract_specs.py`: PASS
- `generate_all_mock_data.py --rows 20 --seed 42`: PASS
- `analyze_semantic_mapping.py`: PASS
- `build_mapping_contract.py`: PASS
- `run_contract_migration.py`: PASS
- `run_enterprise_pipeline.py --min-patients 20`: PASS

Key resulting metrics:
- Source catalog: 417 tables / 5,387 fields
- Target catalog: 38 tables / 880 fields
- Contract model: 919 target fields classified
- Contract ETL output: 38 target tables, 760 rows total
- Enterprise gate: 0 ERROR, 25 WARN

Open warning class:
- `MAPPING_UNRESOLVED` only
- No data integrity ERROR currently reported by enterprise checks

Immediate closure priorities:
1. Resolve the 25 unresolved business fields in `enterprise_pipeline_issues.csv`.
2. Implement approved code crosswalks for all `LOOKUP_TRANSLATION` classes.
3. Implement explicit derivation logic for archive-heavy fields (`LOAD_ADT_ARCHIVE`, `LOAD_OPD_ARCHIVE`, detention/CPA archives).
4. Add final release gates with threshold-based hard fail rules.

## Tactical Hardening Progress (2026-02-25)

Implemented:
1. Crosswalk engine for `LOOKUP_TRANSLATION` in contract ETL with dictionary-driven mapping from `schemas/crosswalks/*.csv`.
2. Crosswalk reject output: `reports/contract_migration_rejects.csv`.
3. Domain transformation plugins for high-risk domains:
- PMI (`LOAD_PMI*`)
- ADT (`LOAD_ADT_*`)
- OPD (`LOAD_OPD_*`)
4. Release gate runner: `pipeline/run_release_gates.py` with hard-threshold checks.

Next governance actions remain unchanged:
- expand crosswalk dictionaries to full approved NHS/PAS sets
- resolve `MAPPING_UNRESOLVED` fields by SME sign-off
- improve population ratio before cutover gate approval

## Status Update After Policy Uplift and API Productization (2026-02-25)

Delivered:
1. Mapping resolution policy overrides for previously unresolved business fields (`pipeline/mapping_resolution_policy.json`).
2. Pre-production imputation mode in contract ETL (`--impute-mode pre_production`) for completeness testing.
3. Expanded crosswalk dictionaries and strict reject control (current rejects: 0).
4. Full-stack product scaffold with API and dynamic Next.js UI.

Current measured outcomes:
- Contract ETL: PASS
- Enterprise quality: PASS (0 ERROR, 0 WARN)
- Release gates (`pre_production` profile): PASS
- Population ratio: 0.6784

Governance note:
- Policy-overridden fields are now technically resolved for pre-production execution.
- Final cutover must still confirm SME and clinical governance acceptance for all policy defaults.
