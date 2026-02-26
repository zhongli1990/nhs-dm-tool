![][image1]![][image2]![][image3]Altera PAS v18.4 Data    
![][image4]Migration Technical Guide ![][image5]EMEA Technical Services 

![][image6]![][image7]![][image8]![][image9]![][image10]![][image11]![][image12]  
1

This Data Migration ~~Technical Guide outlines the standards, processes and technical require~~ments for  ~~accurately, securely and efficiently from legacy systems to PAS, enabling a smooth transition~~ with minimal  ~~operational disruption. The guide defines the data structures, transformation rules, validatio~~n procedures and    
PAS Data Migration Technical Guide Introduction 

~~migration, the~~ stages involved, the testing approach and an overview of all functional areas covered ranging  ~~from; staff, user~~s and site configuration to patient demographics, referrals, outpatient and inpatient activity,    
quality controls necessary to support a consistent and auditable migration process. It is intended for project  teams, data engineers, technical analysts and system integrators involved in planning, executing, or  overseeing the migration activities.   
loa~~d~~ ~~p~~r~~oce~~s~~s.~~ E~~ach~~ ~~func~~t~~io~~n~~al~~ ~~ar~~e~~a~~ i~~nclu~~d~~es~~ ~~tab~~le-~~l~~evel ~~speci~~f~~icat~~i~~on~~s~~, fi~~e~~l~~d ~~de~~f~~i~~n~~i~~tio~~ns~~, ~~da~~t~~a r~~u~~les~~ an~~d stru~~ct~~ur~~al    
Overview  

This guide is organised into two main sections that together provide comprehensive support for the migration  

community care, mental health and associated archives.  

The second section presents a detailed data dictionary that defines every migration table used within the PAS  

requirements to ensure consistent, validated and accurate population of the PAS data model. Together, these  sections give stakeholders a complete reference for planning, executing and verifying all data migration  activities.

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 2

~~generic structu~~res detailed in this d~~ocument, it will be necessary for Altera t~~o write bespoke data translation  ~~procedures to~~ move data from extracts as supplied to the generic Altera PAS data migration table structures.    
Migration Principles   
~~The routines to~~ move data into the Altera PAS transaction tables can however be re-used. The level of    
Intention 

Generic migration software has been developed to reduce the amount of effort involved in data migration  projects. The underlying principle of the generic approach is to eliminate a layer of development by specifying  exact formats for the receipt of data and re-using generic migration code to load data directly into the Altera~~Extract data from the so~~urce system (optionally transformed into Altera Generic Formats)   
PAS transaction tables from the generic structures. If the source data is not supplied in the format of the  Any load errors due to invalid data types or formats are reported back to the Trust for resolution~~If not already in Altera G~~eneric Format transform the loaded data and populate the generic migration    
bespoke development required can be reduced by increasing the level of logic that is handled at the time of  extraction and ensuring that the layout of extracted data meets the generic structures. 

Migration Stages   
Enter mapping configuration data in Altera PAS    
The migration process is as follows: 

Altera loads the extracted data into the Altera PAS database 

tables 

Run data mapping reports to ascertain which coded values from the source system extracts require  Altera recommends that the Trust conducts tests in each trial migration comparing field values in the source    
mapping to coded values in Altera PAS    
~~PAS to field~~ values in Altera PAS for all migrated data items for a minimum of 50 patients encompassing a    
Migrate data from generic migration tables into the Altera PAS transaction tables Produce migration result and error reports 

The above process is repeated through a recommended minimum of three trials before the final go-live  migration. 

Testing 

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 3range of representative data values.  
~~S T A F F : H O S P I T A L S T A F F M E M B E R~~ S   
~~U S E R S : A L T E R A P A S A P P L I C A T I O~~ N U S E R S   
S ~~I T E S : S~~ ~~I T~~ ~~E S~~    
Migration Functional Areas 

The migration software is split into distinct functional areas:  

Sites codes, site addresses, and links from site code to provider. ~~P M I~~ : ~~P A T I E N~~ T ~~M A S T E~~ ~~R~~ I ~~N D E X~~    
R T T P W : R E F E R R A L T O T R E A T M E N T P A T H W A Y S   
Altera and Password information.  R E F : R EF E R R A L S   
R T T P R : R E F E R R A L T O T R E A T M E N T P E R I O D S   
Patient demographic data, identifiers, aliases, addresses, NOK and contact details, allergies, warnings, GP  audit and case note tracking information.   
R T T E V : R E F E R R A L T O T R E A T M E N T E V E N T S   
RTT pathways for outpatient and inpatient waiting lists, encounters including suspensions. O W L : O U T P A T I E N T W A I T I N G L I S T   
Referrals.   
O P D : O U T P A T I E N T A C T I V I T Y   
RTT periods (clocks).   
C M T Y : C O M M U N I T Y C A R E A P P O I N T M E N T S   
Events within an RTT Period (clock).    
I W L : I N P A T I E N T W A I T I N G L I S T   
Referrals for outpatient treatment including suspensions. 

Outpatient bookings and attendances. 

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 4  
Community care appointments. 

Referrals for inpatient treatment including suspensions and TCIs.  
A D T : I N P A T I E N T A C T I V I T Y   
M H : M E N T A L H E A L T H   
A R C H : A R C H I V E S   
Inpatient activity including episodes of care and bed transfers. 

Mental Health information, including patient detentions and care plans. 

The migration process must be run in the above order to ensure referential integrity. Data archives are loaded independently from other archive and transaction data.

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 5  
The following table definitions describe all fields available to be loaded into the Altera PAS. Data from other  systems intended f~~or Altera PAS must be provided in this format for successful migration in~~to Altera PAS. All  tables contain a primary key; record\_number and source system fields; system\_code and external\_system\_idas well as fields for s~~toring resulting foreign keys to Altera PAS. Data extracts must at the ve~~ry least contain a    
Data Dictionary for Migration Tables 

placeholder for each field listed below. Fields highlighted grey are mandatory and data must be provided for  these.  

STAFF DATA 

| TABLE NAME: LOAD\_STAFF Hospital Staff Data :  staff\_master  staff\_ids  staff\_names  staff\_hospitals  team\_staff  staff\_specialty  staff\_depts  Loaded via:   oasloadstaff\_package.load\_staff |
| ----- |

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER  | 42 |
| :---- | :---- |

 record\_number Unique identifier for this extracted record. 

VARCHAR2 10 system\_code Unique identifier for the originating system.  

| VARCHAR2 | 100 |
| :---: | :---- |

  external\_system\_id Maps to: code type 10599 "Dataload System" 

~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 6  
VARCHAR2 20 user\_name Unique identifier for user, the name used to log in with. Uppercase  

Loaded into maps006.user\_name

| VARCHAR2 | 40 |   first\_name |  Fore name   Uppercase |
| :---: | :---- | :---- | :---- |

|  |  |
| :---- | :---- |

Loaded into maps006.first\_name 

VARCHAR2 40 middle\_name Fore name 2  

Uppercase 

Loaded into maps006.middle\_name 

| VARCHAR2 | 40 |
| :---: | :---- |

  family\_name Family name  

Uppercase 

Loaded into maps006.family\_name 

~~Not held in Altera PAS application tables.~~   
VARCHAR2 10 Department\_code Must be a valid Altera PAS Work Entity work\_entity\_code as seen in  the ADTWORKE Form. 

The first 40 characters of the related work entity description will be    
derived and loaded into maps006.department. 

| NUMBER | 6 |
| :---- | :---- |

  job\_id Must be a valid Altera PAS Job Group Job ID as seen in the  MAPJOBS form. 

Loaded into maps006.job\_id 

VARCHAR2 80 password Password for user account. 

| NUMBER | 6 |
| :---- | :---- |

  psswd\_life\_months Must be a non-negative integer not exceeding 1200\. Loaded into maps006.psswd\_life\_months 

DATE psswd\_expiry\_date Date after which user logon will be disallowed. Loaded into maps006.psswd\_expiry\_date 

| NUMBER | 2 |
| :---- | :---- |

  language\_id Language ID used for error messages. Must be a valid AlteraPAS  Language ID as seen in the MAPFLANG form. 

Loaded into maps006.language\_id 

VARCHAR2 10 staff\_id Must be an Altera PAS Staff Master Staff ID as seen in the STFFSCRN  Form. 

~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 7  
Required if employee flag is set to Y 

Loaded into maps006.staff\_id 

| VARCHAR2 | 10 |   default\_parts\_entity |  Must be a valid Altera PAS Work Entity work\_entity\_code as seen in the ADTWORKE Form.  Derived work\_entity\_data.work\_entity is loaded into  maps006.default\_parts\_entity |
| :---: | :---- | :---- | :---- |

|  |  |
| :---- | :---- |

VARCHAR2 10 default\_tools\_entity Must be a valid Altera PAS Work Entity work\_entity\_code as seen in  the ADTWORKE Form. 

Derived work\_entity\_data.work\_entity is loaded into    
maps006.default\_tools\_entity 

| VARCHAR2 | 10 |
| :---: | :---- |

  default\_labour\_entity Must be a valid Altera PAS Work Entity work\_entity\_code as seen in  the ADTWORKE Form. 

Derived work\_entity\_data.work\_entity is loaded into    
maps006.default\_labour\_entity 

VARCHAR2 1 employee\_flag Must be Y or N, if Y then staff\_id must be entered Loaded into maps006.employee\_flag 

| VARCHAR2 | 10 |
| :---: | :---- |

  default\_stock\_entity Must be a valid Altera PAS Work Entity work\_entity\_code as seen in  the ADTWORKE Form. 

Derived work\_entity\_data.work\_entity is loaded into    
maps006.default\_stock\_entity 

VARCHAR2 40 Provider\_name Must be a valid Altera PAS Provider Name as seen in the  MAPSHEAD Form. 

Corresponding internal Provider unique identifier is loaded into    
maps006.hospital\_id 

| VARCHAR2 | 80 |
| :---: | :---- |

  staff\_security\_level Maps to: code type 10018 "SECURITY REQUIRED" Loaded as mapped into: maps006. staff\_security\_level 

VARCHAR2 20 phone\_no Users direct dial telephone number. 

Loaded into maps006.phone\_no 

| VARCHAR2 | 5 |   extension\_no | ~~Must be a valid Altera PAS Work Entity work\_entity\_code as seen in~~   Users telephone extension number  Loaded into maps006.extension\_no  |
| :---: | :---- | :---- | ----- |
| VARCHAR2 | 10 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  default\_login\_entity |  Default Work Entity used for work entity restriction checks.  the ADTWORKE Form.  Derived work\_entity\_data.work\_entity is loaded into  maps006.default\_login\_entity |

 8

| VARCHAR2 | 1 |
| :---: | :---- |

account will be able to log into Altera PAS Java Web App as well as    
  eoasis\_user Must be Y, N or Null. If NULL will be treated as N. If set to Y user  Oracle Forms.   
Loaded into maps006.sqlplus\_user (N.B. pre-existing column re   
purposed) 

VARCHAR2 1 allow\_logon Controls if user can log into Altera PAS application. Must be Y or N.  

Loaded into maps006.allow\_logon 

| VARCHAR2 | 10 |
| :---: | :---- |

  default\_executable Default Altera PAS Forms login form. Must be Null or a valid AlteraPAS form executable Short Name as seen in the MAPFUNCT form. 

Loaded into maps006.default\_executable 

VARCHAR2 10 gp\_national\_code National General Practitioner Code Maps to: GP\_MASTER.registration\_code 

Loaded as mapped into: maps006.gp\_id 

e.g. C0000048 , D2008756, G3293160 

| VARCHAR2 | 80 |
| :---: | :---- |

  type\_of\_user Type of User. 

Maps to: code type 10495 " EOASIS USER TYPES" 

Loaded as mapped into: maps006. type\_of\_user 

DATE 10 login\_from\_date Date after which user is permitted to log on to Altera PAS. If Null will be set to one hour after user account is created.  

Loaded into maps006.login\_from\_date 

| DATE | 10 |
| :---- | :---- |

  login\_to\_date Date after which user may not log onto Altera PAS.  Loaded into maps006.login\_to\_date 

VARCHAR2 10 practice\_national\_code National Practice Code for the GP Maps to: GP\_PRACTICE\_MASTER.gp\_practice\_code 

Loaded as mapped into: maps006.practice\_id 

e.g. A81006, D82076, K81022

| VARCHAR2 | 80 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved.~~  email\_address |  Users e-mail address.  Loaded into maps006.email\_address |
| :---: | :---- | :---- | ----- |
| VARCHAR2 | 1 |   can\_log\_support\_calls |  Legacy field, not used except as documentation.  Must be Y or N. If supplied as NULL will be set to N |

 9

| VARCHAR2 | 1 |
| :---: | :---- |

~~prompt will be displayed on login to Altera PAS forms asking if the~~    
Loaded into maps006.can\_log\_support\_calls 

  ask\_review\_warnings Must be Y or N. If Y then if user has un-reviewed clinical warnings a  user wishes to see them.   
Loaded into maps006.ask\_review\_warnings 

NUMBER 4 from\_time Time of day after which user is permitted to log on to AlteraPAS,  expressed as the number of minutes after midnight. Must be  

between 0 and 1439\. If Null then defaults to 0 \= 00:00. 

| NUMBER | 4 |
| :---- | :---- |

  to\_time Time of day after which user is not permitted to log on to AlteraPAS, expressed as the number of minutes after midnight. Must be  between 0 and 1439\. If Null then defaults to 1439 \= 23:59. 

VARCHAR2 1 mon\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

| VARCHAR2 | 1 |
| :---: | :---- |

  tue\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

VARCHAR2 1 wed\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

| VARCHAR2 | 1 |
| :---: | :---- |

  thu\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

VARCHAR2 1 fri\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

 

 

 

| VARCHAR2 | 1 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved.~~  sat\_allowed |  Must be Y, N or Null. If Null is on load file then it will be set to Y.Determines if user is allowed to logon on this day of the meek.Loaded into maps006 field of same name. |
| :---: | :---- | :---- | ----- |
| VARCHAR2 | 1 |   sun\_allowed |  Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek.Loaded into maps006 field of same name. |

 10

| VARCHAR2 | 80 |   default\_team |  ~~Maps to: code type 10721~~ "TEAMS FOR DATALOAD MAPPING" Loaded as mapped into: maps006.default\_team\_id |
| ----- | :---- | ----- | ----- |
| VARCHAR2US ERS | 80Altera PAS Application User data.  |   client\_user  | Maps to: code type 10768 " SUPPORT CATEGORIES" Loaded as mapped into: maps006.client\_user |

 11   
 

 

| TABLE NAME: LOAD\_USERS   MAPS006  EOASIS\_PAGE\_LINKS  Creates an Oracle User Account for the application user.Loaded via:   OASLOADUSER\_PACKAGE.load\_user |
| :---- |

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER  | 42 |
| :---- | :---- |

 record\_number Unique identifier for this extracted record. 

VARCHAR2 10 system\_code Unique identifier for the originating system.  

| VARCHAR2 | 100 |
| :---: | :---- |

  external\_system\_id Maps to: code type 10599 "Dataload System" 

VARCHAR2 20 user\_name Unique identifier for user, the name used to log in with. Uppercase  

Loaded into maps006.user\_name

| VARCHAR2 | 40 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved.~~  first\_name |  Fore name   Uppercase  Loaded into maps006.first\_name |
| :---: | :---- | :---- | :---- |
| VARCHAR2 | 40 |   middle\_name |  Fore name 2   Uppercase  Loaded into maps006.middle\_name |

| VARCHAR2 | 40 |
| :---: | :---- |

  family\_name Family name  

Uppercase 

Loaded into maps006.family\_name 

~~Not held in Altera PAS application tables.~~   
VARCHAR2 10 Department\_code Must be a valid Altera PAS Work Entity work\_entity\_code as seen in  the ADTWORKE Form. 

The first 40 characters of the related work entity description will be    
derived and loaded into maps006.department. 

| NUMBER | 6 |
| :---- | :---- |

  job\_id Must be a valid Altera PAS Job Group Job ID as seen in the  MAPJOBS form. 

Loaded into maps006.job\_id 

VARCHAR2 80 Password Password for user account. 

| NUMBER | 6 |
| :---- | :---- |

  psswd\_life\_months Must be a non-negative integer not exceeding 1200\. Loaded into maps006.psswd\_life\_months 

DATE psswd\_expiry\_date Date after which user logon will be disallowed. Loaded into maps006.psswd\_expiry\_date 

| NUMBER | 2 |
| :---- | :---- |

  language\_id Language ID used for error messages. Must be a valid AlteraPAS  Language ID as seen in the MAPFLANG form. 

Loaded into maps006.language\_id 

VARCHAR2 10 staff\_id Must be an Altera PAS Staff Master Staff ID as seen in the STFFSCRN  Form. 

Required if employee flag is set to Y 

Loaded into maps006.staff\_id 

 

| VARCHAR2 | 10 |   default\_parts\_entity |  Must be a valid Altera PAS Work Entity work\_entity\_code as seen in the ADTWORKE Form.  Derived work\_entity\_data.work\_entity is loaded into  maps006.default\_parts\_entity |
| :---: | :---- | :---- | :---- |
| VARCHAR2 | 10 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  default\_tools\_entity |  Must be a valid Altera PAS Work Entity work\_entity\_code as seen in the ADTWORKE Form.  Derived work\_entity\_data.work\_entity is loaded into  maps006.default\_tools\_entity |

 12

| VARCHAR2 | 10 |
| :---: | :---- |

  default\_labour\_entity Must be a valid Altera PAS Work Entity work\_entity\_code as seen in  the ADTWORKE Form. 

Derived work\_entity\_data.work\_entity is loaded into    
maps006.default\_labour\_entity 

VARCHAR2 1 employee\_flag Must be Y or N, if Y then staff\_id must be entered Loaded into maps006.employee\_flag 

| VARCHAR2 | 10 |
| :---: | :---- |

  default\_stock\_entity Must be a valid Altera PAS Work Entity work\_entity\_code as seen in  the ADTWORKE Form. 

Derived work\_entity\_data.work\_entity is loaded into    
maps006.default\_stock\_entity 

VARCHAR2 40 Provider\_name Must be a valid Altera PAS Provider Name as seen in the  MAPSHEAD Form. 

Corresponding internal Provider unique identifier is loaded into    
maps006.hospital\_id 

| VARCHAR2 | 80 |
| :---: | :---- |

  staff\_security\_level Maps to: code type 10018 "SECURITY REQUIRED" ~~Must be a valid Altera PAS Work Entity work\_entity\_code as seen in~~    
Loaded as mapped into: maps006. staff\_security\_level 

VARCHAR2 20 phone\_no Users direct dial telephone number. Loaded into maps006.phone\_no 

| VARCHAR2 | 5 |
| :---: | :---- |

  extension\_no Users telephone extension number account will be able to log into Altera PAS Java Web App as well as   
Loaded into maps006.extension\_no 

VARCHAR2 10 default\_login\_entity Default Work Entity used for work entity restriction checks. 

the ADTWORKE Form. 

Derived work\_entity\_data.work\_entity is loaded into    
maps006.default\_login\_entity 

~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 13

| VARCHAR2 | 1 |   eoasis\_user  | Must be Y, N or Null. If NULL will be treated as N. If set to Y user Oracle Forms.  Loaded into maps006.sqlplus\_user (N.B. pre-existing column re purposed) |
| :---: | :---- | :---: | :---- |

 

VARCHAR2 1 allow\_logon Controls if user can log into Altera PAS application. Must be Y or N.  

Loaded into maps006.allow\_logon 

| VARCHAR2 | 10 |
| :---: | :---- |

  default\_executable Default Altera PAS Forms login form. Must be Null or a valid AlteraPAS form executable Short Name as seen in the MAPFUNCT form. 

Loaded into maps006.default\_executable 

VARCHAR2 10 gp\_national\_code National General Practitioner Code Maps to: GP\_MASTER.registration\_code 

Loaded as mapped into: maps006.gp\_id 

e.g. C0000048 , D2008756, G3293160 

| VARCHAR2 | 80 |
| :---: | :---- |

  type\_of\_user Type of User. 

Maps to: code type 10495 " EOASIS USER TYPES" 

Loaded as mapped into: maps006. type\_of\_user 

DATE 10 login\_from\_date Date after which user is permitted to log on to Altera PAS. If Null will be set to one hour after user account is created.  

Loaded into maps006.login\_from\_date 

| DATE | 10 |
| :---- | :---- |

  login\_to\_date Date after which user may not log onto Altera PAS.  Loaded into maps006.login\_to\_date 

VARCHAR2 10 practice\_national\_code National Practice Code for the GP Maps to: GP\_PRACTICE\_MASTER.gp\_practice\_code 

Loaded as mapped into: maps006.practice\_id 

e.g. A81006, D82076, K81022 

| VARCHAR2 | 80 |
| :---: | :---- |

~~prompt will be displayed on login to Altera PAS forms asking if the~~   
  email\_address Users e-mail address. 

Loaded into maps006.email\_address 

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 14  
VARCHAR2 1 can\_log\_support\_calls Legacy field, not used except as documentation. Must be Y or N. If supplied as NULL will be set to N

Loaded into maps006.can\_log\_support\_calls 

| VARCHAR2 | 1 |   ask\_review\_warnings |  Must be Y or N. If Y then if user has un-reviewed clinical warnings a user wishes to see them.  Loaded into maps006.ask\_review\_warnings |
| :---: | :---- | :---- | :---- |

 

NUMBER 4 from\_time Time of day after which user is permitted to log on to AlteraPAS,  expressed as the number of minutes after midnight. Must be  

between 0 and 1439\. If Null then defaults to 0 \= 00:00. 

| NUMBER | 4 |
| :---- | :---- |

  to\_time Time of day after which user is not permitted to log on to AlteraPAS, expressed as the number of minutes after midnight. Must be  between 0 and 1439\. If Null then defaults to 1439 \= 23:59. 

VARCHAR2 1 mon\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

| VARCHAR2 | 1 |
| :---: | :---- |

  tue\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

VARCHAR2 1 wed\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

| VARCHAR2 | 1 |
| :---: | :---- |

  thu\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

VARCHAR2 1 fri\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

| VARCHAR2 | 1 |
| :---: | :---- |

  sat\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

   
VARCHAR2 1 sun\_allowed Must be Y, N or Null. If Null is on load file then it will be set to Y. Determines if user is allowed to logon on this day of the meek. 

Loaded into maps006 field of same name. 

| VARCHAR2 | 80 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved.~~  default\_team |  ~~Maps to: code type 10721~~ "TEAMS FOR DATALOAD MAPPING" Loaded as mapped into: maps006.default\_team\_id |
| :---: | :---- | ----- | ----- |
| VARCHAR2 | 80 |   client\_user  | Maps to: code type 10768 " SUPPORT CATEGORIES" Loaded as mapped into: maps006.client\_user |

 15  
S ITES 

| TABLE NAME: LOAD\_SITES  Sites codes, site addresses, and links from site code to provider.  One provider can have one or more site codes associated with it, but one site code can only be linked to a single provider. A site code can only have a single address. CODES  PROVIDER\_SITE\_CODES  SITE\_CODE\_CONTACTS  Loaded via:   OASLOADSITE\_PACKAGE.load\_sites  To simplify the load structure and migration process the following rules will be imposed on loaded data.  |
| :---- |

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER  | 42 |
| :---- | :---- |

 record\_number Unique identifier for this extracted record. 

VARCHAR2 10 system\_code Unique identifier for the originating system.  

| VARCHAR2 |  100 |
| :---: | :---- |

 external\_system\_id Maps to: code type 10599 "Dataload System" 

VARCHAR2 6 provider\_prefix Provider prefix as entered on MAPSHEAD  

Required to get hospital id from MAPS010 where matched on    
site\_prefix 

| VARCHAR2 |  15 |
| :---: | :---- |

 site\_code User site\_code linked to a provider 

Loaded into CODES.user\_code under code\_type 10454 Must be a unique value. 

Must be uppercase. 

VARCHAR2 80 site\_description Description of the site   
~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 16  
Loaded into CODES.description 

Must be uppercase. 

| DATE | 10 |   site\_link\_applies\_start |  The start date of the linked site  Must be in format: DD/MM/YYYY, cannot be in the futureLoaded into: PROVIDER\_SITE\_CODES.applies\_start |
| :---- | :---- | :---- | :---- |

DATE 10 site\_link\_applies\_end The end date of the linked site 

Must be in format: DD/MM/YYYY, If provided, , cannot be in the    
future and must be greater then start\_date 

Loaded into: PROVIDER\_SITE\_CODES.applies\_end 

| VARCHAR2 | 80 |
| :---: | :---- |

  ADDRESS\_1 Loaded into: SITECODE\_CONTACTS.address\_1 

VARCHAR2 80 ADDRESS\_2 Loaded into: SITE\_CODE\_CONTACTS.address\_2 

| VARCHAR2 | 80 |
| :---: | :---- |

  ADDRESS\_3 Loaded into: SITE\_CODE\_CONTACTS.address\_3 

VARCHAR2 80 ADDRESS\_4 Loaded into: SITE\_CODE\_CONTACTS.address\_4 

| VARCHAR2 | 20 |
| :---: | :---- |

  POST\_CODE Loaded into: SITE \_CODE\_CONTACTS.post\_code 

VARCHAR2 20 PHONE\_1 Loaded into: SITE\_ SITE \_CONTACTS.phone\_1 

| VARCHAR2 | 20 |
| :---: | :---- |

  PHONE\_2 Loaded into: SITE\_ SITE \_CONTACTS.phone\_2 

VARCHAR2 80 EMAIL Loaded into: SITE\_ SITE \_CONTACTS.EMAIL 

| DATE | 10 |   APPLIES\_START |  Must be in format: DD/MM/YYYY. cannot be before  site\_link\_applies\_start  Loaded into: SITE\_CODE\_CONTACTS.applies\_start |
| :---- | :---- | :---- | :---- |
| DATE | 10 |   APPLIES\_END |  Must be in format: DD/MM/YYYY. If provided, cannot be in the future and must be greater then applies\_start date Loaded into: SITE\_CODE\_CONTACTS.applies\_end |

 

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 17  
PAT IENT DEMOGRAPHIC DATA 

| TABLE NAME: LOAD\_PMI  Main patient demographic data.   PATIENT\_IDS  PATIENT\_MASTER PATIENT\_NAMES  PATIENT\_CONTACTS PATIENT\_XTRA\_INFO  Loaded via:   OASLOADPMI\_PACKAGE.load\_patient |
| :---- |

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

VARCHAR2 10 SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

| VARCHAR2 | 100 |
| :---- | :---- |

  EXTERNAL\_SYSTEM\_ID Unique patient id from the source system. 

VARCHAR2 80 MAIN\_CRN\_TYPE Main Hospital Number Id Type Maps to: code type 9 \- 

Loaded as mapped into: PATIENT\_IDS.id\_type\_code 

| VARCHAR2 | 30 |
| :---- | :---- |

  MAIN\_CRN 

Loaded into: PATIENT\_IDS.id\_number 

DATE 10 DATE\_REGISTERED Must be in format: DD/MM/YYYY 

If not currently held in source system, recommend loading date of    
birth. 

Loaded into: PATIENT\_MASTER.date\_registered 

| VARCHAR2 | 30 |   NHS\_NUMBER |  Loaded into: PATIENT\_IDS.ID\_NUMBER for code type 9, prog code 4,  |
| :---- | :---- | :---- | ----- |
| VARCHAR2 | 80 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  NHS\_NUMBER\_STATUS |  NHS Number Tracing Status  Maps to: code type 10366 "NHS Number Status Code" |

 18

| VARCHAR2 | 80 |
| :---- | :---- |

Loaded as mapped into: PATIENT\_IDS.status\_code 

NATIONAL CODES can be found at: 

http://www.datadictionary.nhs.uk/data\_dictionary/data\_field\_notes/ n/nhs\_number\_status\_indicator\_de.asp?shownav=1 

  SEX Maps to: code type 3 "Sex" 

Loaded as mapped into: PATIENT\_MASTER.sex 

VARCHAR2 80 TITLE Maps to: code type 29 "Title" Loaded as mapped into: PATIENT\_MASTER.title 

| VARCHAR2 | 40 |
| :---- | :---- |

  PAT\_NAME\_1 Loaded into: PATIENT\_MASTER.pat\_name\_1 

VARCHAR2 40 PAT\_NAME\_2 Loaded into: PATIENT\_MASTER.pat\_name\_2 

| VARCHAR2 | 40 |
| :---- | :---- |

  PAT\_NAME\_3 Loaded into: PATIENT\_MASTER.pat\_name\_3 

VARCHAR2 40 PAT\_NAME\_FAMILY Loaded into: PATIENT\_MASTER.pat\_name\_family 

| VARCHAR2 | 40 |
| :---- | :---- |

  MAIDEN\_NAME Loaded into: PATIENT\_MASTER.maiden\_name Will also trigger a record to be created in PATIENT\_NAMES. 

DATE 10 DATE\_OF\_BIRTH Must be in format: DD/MM/YYYY Loaded into: PATIENT\_MASTER.date\_of\_birth 

| VARCHAR2 | 80 |
| :---- | :---- |

  PLACE\_BORN Maps to: code type 333 "Country Codes" Loaded as mapped into: PATIENT\_MASTER.place\_born\_code

DATE 10 DATE\_ENTERED\_COUN   
Must be in format: DD/MM/YYYY   
TRY   
Loaded into: PATIENT\_MASTER.date\_entered\_country 

| VARCHAR2 | 80 |
| :---- | :---- |

  NATIONALITY Maps to: code type 5 "Nationality" Loaded as mapped into: PATIENT\_MASTER.nationality\_code  
~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 19  
VARCHAR2 80 ETHNIC\_GROUP Maps to: code type 10028 "Ethnic Origin" Loaded as mapped into: PATIENT\_MASTER.ethnic\_origin

| VARCHAR2 | 80 |   PREFERRED\_LANGUAGE | Maps to: code type 10658 "Preferred Language"   Loaded as mapped into: PATIENT\_MASTER.preferred\_language\_id |
| :---- | :---- | :---- | :---- |

VARCHAR2 80 RELIGION\_CODE Maps to: code type 1 "Religion" Loaded as mapped into: PATIENT\_MASTER.religion\_code 

| VARCHAR2 | 80 |
| :---- | :---- |

  MARITAL\_STATUS Maps to: code type 2 "Marital Status" Loaded as mapped into: PATIENT\_MASTER.marital\_status 

VARCHAR2 80 OCCUPATION\_CODE Maps to: code type 4 "Occupation" Loaded as mapped into: PATIENT\_MASTER.occupation\_code

| VARCHAR2 | 80 |
| :---- | :---- |

  WHERE\_HEARD\_OF\_S 

Maps to: code type 10753 "Where Heard Of Service"   
ERVICE 

Loaded as mapped into: PATIENT\_MASTER.where\_heard\_of\_code

VARCHAR2 80 PAT\_ADDRESS\_1 Patient Permanent Address Line 1 Loaded into: PATIENT\_CONTACTS.address\_1 

| VARCHAR2 | 80 |
| :---- | :---- |

  PAT\_ADDRESS\_2 Patient Permanent Address Line 2 Loaded into: PATIENT\_CONTACTS. address \_2 

VARCHAR2 80 PAT\_ADDRESS\_3 Patient Permanent Address Line 3 Loaded into: PATIENT\_CONTACTS. address \_3 

| VARCHAR2 | 80 |
| :---- | :---- |

  PAT\_ADDRESS\_4 Patient Permanent Address Line 4 Loaded into: PATIENT\_CONTACTS. address \_4 

VARCHAR2 20 POST\_CODE Patient Permanent Address Post Code Loaded into: PATIENT\_CONTACTS.post\_code 

| VARCHAR2 | 20 |
| :---- | :---- |

  TELEPHONE\_NO Patient Permanent Address Phone 1 Loaded into: PATIENT\_CONTACTS.phone\_1 

VARCHAR2 20 TELEPHONE\_NO\_2 Patient Permanent Address Phone 2 Loaded into: PATIENT\_CONTACTS.phone\_2

| VARCHAR2 | 20 |   TELEPHONE\_NO\_3 |  Patient Permanent Address Phone 3  Loaded into: PATIENT\_CONTACTS.phone\_3 |
| :---- | :---- | :---- | ----- |
| VARCHAR2 | 80 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  PAT\_EMAIL\_ADDRESS |  Patient Email Address  Loaded into: PATIENT\_MASTER.email\_address |

 20

| VARCHAR2 | 1 |
| :---- | :---- |

  PAT\_LIVES\_ALONE Patient lives alone at permanent address. 

Only two accepted values: Y for Yes OR N for No 

Loaded into: PATIENT\_CONTACTS.lives\_alone\_flag 

VARCHAR2 1 PAT\_PERMISSION\_TO\_   
Permission to send correspondence to permanent address.   
CONTACT   
Only two accepted values: Y for Yes OR N for No 

Loaded into: PATIENT\_CONTACTS.permission\_to\_contact\_flag

| VARCHAR2 | 1 |
| :---- | :---- |

  PAT\_PERMISSION\_TO\_ 

Permission to phone permanent address.   
PHONE 

Only two accepted values: Y for Yes OR N for No 

Loaded into: PATIENT\_CONTACTS.permission\_to\_phone\_flag

DATE 10 PAT\_ADDRESS\_FROM Patient Permanent Address Applies FromMust be in format: DD/MM/YYYY 

Loaded into: PATIENT\_CONTACTS.applies\_start 

| DATE |  10 |
| :---- | :---: |

 DATE\_OF\_DEATH Must be in format: DD/MM/YYYY HH24:MI PATIENT\_MASTER.date\_of\_death 

VARCHAR2 80 WHERE\_DIED Maps to: code type 274 "Where Died" Loaded as mapped into: DEATHS.where\_died 

e.g. Ambulance, Emergency Room, Operating Theatre, Ward

| VARCHAR2 | 80 |
| :---- | :---- |

  CAUSE\_OF\_DEATH Maps to: code type 10752 "Causes of Death" Loaded as mapped into: DEATHS.cause\_of\_death 

e.g. Cardiac Failure, Drug Intoxication, Multi Organ Failure, Trauma

VARCHAR2 1 DEATH\_TREATMENT\_R   
Only two accepted values: Y for Yes OR N for No   
ELATED   
Loaded into: DEATHS.death\_treatment\_related 

| VARCHAR2 | 1 |
| :---- | :---- |

  DEATH\_HIV\_RELATED Only two accepted values: Y for Yes OR N for No Loaded into: DEATHS.death\_hiv\_related   
~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 21  
VARCHAR2 80 EXTRA\_INFO\_1\_TYPE Maps to: code type 23 \- "Extra Information (Patient)" Loaded into: PATIENT\_XTRA\_INFO.info\_code 

e.g. Orthoptic Printing Required?, Smoker?

| VARCHAR2 | 80 |   EXTRA\_INFO\_1 |  Loaded into: PATIENT\_XTRA\_INFO.description |
| :---- | :---- | :---- | :---- |

VARCHAR2 80 EXTRA\_INFO\_2\_TYPE Maps to: code type 23 \- "Extra Information (Patient)" Loaded into: PATIENT\_XTRA\_INFO.info\_code 

| VARCHAR2 | 80 |
| :---- | :---- |

  EXTRA\_INFO\_2 Loaded into: PATIENT\_XTRA\_INFO.description 

VARCHAR2 80 EXTRA\_INFO\_3\_TYPE Maps to: code type 23 \- "Extra Information (Patient)" Loaded into: PATIENT\_XTRA\_INFO.info\_code 

| VARCHAR2 | 80 |
| :---- | :---- |

  EXTRA\_INFO\_3 Loaded into: PATIENT\_XTRA\_INFO.description 

VARCHAR2 80 EXTRA\_INFO\_4\_TYPE Maps to: code type 23 \- "Extra Information (Patient)" Loaded into: PATIENT\_XTRA\_INFO.info\_code 

| VARCHAR2 | 80 |
| :---- | :---- |

  EXTRA\_INFO\_4 Loaded into: PATIENT\_XTRA\_INFO.description 

VARCHAR2 80 EXTRA\_INFO\_5\_TYPE Maps to: code type 23 \- "Extra Information (Patient)" Loaded into: PATIENT\_XTRA\_INFO.info\_code 

| VARCHAR2 | 80 |
| :---- | :---- |

  EXTRA\_INFO\_5 Loaded into: PATIENT\_XTRA\_INFO.description 

VARCHAR2 80 EXTRA\_INFO\_6\_TYPE Maps to: code type 23 \- "Extra Information (Patient)" Loaded into: PATIENT\_XTRA\_INFO.info\_code 

| VARCHAR2 | 80 |
| :---- | :---- |

  EXTRA\_INFO\_6 Loaded into: PATIENT\_XTRA\_INFO.description 

VARCHAR2 80 EXTRA\_INFO\_7\_TYPE Maps to: code type 23 \- "Extra Information (Patient)" Loaded into: PATIENT\_XTRA\_INFO.info\_code 

| VARCHAR2 | 80 |
| :---- | :---- |

  EXTRA\_INFO\_7 Loaded into: PATIENT\_XTRA\_INFO.description 

VARCHAR2 80 EXTRA\_INFO\_8\_TYPE Maps to: code type 23 \- "Extra Information (Patient)" Loaded into: PATIENT\_XTRA\_INFO.info\_code 

~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 22

| VARCHAR2 | 80 |
| :---- | :---- |

  EXTRA\_INFO\_8 Loaded into: PATIENT\_XTRA\_INFO.description 

VARCHAR2 80 EXTRA\_INFO\_9\_TYPE Maps to: code type 23 \- "Extra Information (Patient)" Loaded into: PATIENT\_XTRA\_INFO.info\_code

| VARCHAR2 | 80 |   EXTRA\_INFO\_9 |  Loaded into: PATIENT\_XTRA\_INFO.description |
| :---- | :---- | :---- | :---- |

~~Note type \= "40" \- "Patient Registration Notes"~~    
VARCHAR2 80 EXTRA\_INFO\_10\_TYPE Maps to: code type 23 \- "Extra Information (Patient)" Loaded into: PATIENT\_XTRA\_INFO.info\_code 

| VARCHAR2 | 80 |
| :---- | :---- |

~~Note type \= "40" \- "Patient Registration Notes"~~   
  EXTRA\_INFO\_10 Loaded into: PATIENT\_XTRA\_INFO.description 

VARCHAR2 2000 COMMENTS Maps to: code type 297 "Multiple Note Types" ~~Note type \= "40" \- "Patient Registration Notes"~~   
Subject \= "Registration Notes" 

Loaded into: OASIS\_MULTIPLE\_NOTES.text 

| VARCHAR2 | 80 |
| :---- | :---- |

~~Note type \= "40" \- "Patient Registration Notes"~~   
  NOTE\_1\_SUBJECT Maps to: code type 297 "Multiple Note Types" 

Loaded into: OASIS\_MULTIPLE\_NOTES.subject 

~~Note type \= "40" \- "Patient Registration Notes"~~   
VARCHAR2 2000 NOTE\_1\_TEXT Maps to: code type 297 "Multiple Note Types" Loaded into: OASIS\_MULTIPLE\_NOTES.text 

| VARCHAR2 | 80 |
| :---- | :---- |

  NOTE\_2\_SUBJECT Maps to: code type 297 "Multiple Note Types" Loaded into: OASIS\_MULTIPLE\_NOTES.subject 

VARCHAR2 2000 NOTE\_2\_TEXT Maps to: code type 297 "Multiple Note Types" Loaded into: OASIS\_MULTIPLE\_NOTES.text 

| VARCHAR2 | 80 |
| :---- | :---- |

  NOK\_RELATIONSHIP Next of Kin Relationship to Patient Maps to: code type 17 "Contact Relationship" 

Loaded into: PATIENT\_CONTACTS.relationship 

VARCHAR2 80 NOK\_TITLE Next of Kin Title Maps to: code type 29 "Title" 

Loaded into: PATIENT\_CONTACTS.title

| VARCHAR2 | 40 | © 2026 Altera Digital Health Inc. and/or its ~~subsidiaries. All rights reserved.~~  NOK\_NAME\_1 |  Next of Kin First Name  Loaded into: PATIENT\_CONTACTS.name\_1 |
| :---- | :---- | :---- | :---- |
| VARCHAR2 | 40 |   NOK\_NAME\_FAMILY |  Next of Kin Surname  Loaded into: PATIENT\_CONTACTS.name\_family |

 23

| VARCHAR2 | 80 |
| :---- | :---- |

  NOK\_ADDRESS\_1 Next of Kin Address Line 1 

Loaded into: PATIENT\_CONTACTS.address\_1 

VARCHAR2 80 NOK\_ADDRESS\_2 Next of Kin Address Line 2 Loaded into: PATIENT\_CONTACTS.address\_2 

| VARCHAR2 | 80 |
| :---- | :---- |

  NOK\_ADDRESS\_3 Next of Kin Address Line 3 Loaded into: PATIENT\_CONTACTS.address\_3 

VARCHAR2 80 NOK\_ADDRESS\_4 Next of Kin Address Line 4 Loaded into: PATIENT\_CONTACTS.address\_4 

| VARCHAR2 | 20 |
| :---- | :---- |

  NOK\_POST\_CODE Next of Kin Address Post Code ~~Note type \= "60561" \- "Next Of Kin Notes", Subject \= "Next Of Kin~~    
Loaded into: PATIENT\_CONTACTS.POST\_CODE 

VARCHAR2 20 NOK\_TELEPHONE\_1 Next of Kin Address Phone 1 Loaded into: PATIENT\_CONTACTS.PHONE\_1 

| VARCHAR2 | 20 |
| :---- | :---- |

  NOK\_TELEPHONE\_2 Next of Kin Address Phone 2 Loaded into: PATIENT\_CONTACTS.PHONE\_2 

VARCHAR2 2000 NOK\_COMMENTS Maps to: code type 297 "Multiple Note Types" 

Notes" 

Loaded into: OASIS\_MULTIPLE\_NOTES.text 

| VARCHAR2 | 1 |
| :---- | :---- |

  PAT\_PERMISSION\_TO\_ 

Permission to contact current GP.   
COPY\_GP 

Only two accepted values: Y for Yes OR N for No 

Loaded into: PATIENT\_GP\_LINK.cc\_letter\_flag 

VARCHAR2 10 GP\_NATIONAL\_CODE National General Practitioner Code Maps to: GP\_MASTER.gp\_registration\_code 

Loaded as mapped into: PATIENT\_MASTER.gp\_id 

e.g. C0000048 , D2008756, G3293160 

 

| VARCHAR2 | 10 | © 2026 Altera Digital Health Inc. and/or its ~~subsidiaries. All rights reserved.~~  PRACTICE\_NATIONAL\_CODE | National Practice Code for the GP   Maps to: GP\_PRACTICE\_MASTER.gp\_practice\_code Loaded as mapped into: PATIENT\_MASTER.practice\_ide.g. A81006, D82076, K81022 |
| :---- | :---- | :---- | :---- |

 24

VARCHAR2 20 PRACTICE\_POST\_COD   
Practice Post Code for the GP   
E   
Not loaded but used when mapping to distinguish between sub practices which may have the same National Practice Code. 

| DATE |  10 |
| :---- | :---: |

 PRACTICE\_APPLIES\_FR 

Date Patient Joined GP Practice    
OM 

Must be in format: DD/MM/YYYY, must be populated if gp    
populated. 

Loaded into: PATIENT\_MASTER.practice\_applies\_start 

VARCHAR2 10 GDP\_NATIONAL\_CODE National General Dental Practitioner Code Maps to: GP\_MASTER.registration\_code 

Loaded as mapped into: PATIENT\_GP\_LINK.gp\_id 

| VARCHAR2 | 10 |
| :---- | :---- |

  GDP\_PRACTICE\_NATIO   
National Practice Code for the GDP   
NAL\_CODE   
Maps to: GP\_PRACTICE\_MASTER.gp\_practice\_code 

Loaded as mapped into: PATIENT\_GP\_LINK.practice\_id 

VARCHAR2 20 GDP\_PRACTICE\_POST\_   
Practice Post Code for the GDP   
CODE   
Not loaded but used when mapping to distinguish between sub   
practices which may have the same National Practice Code. 

| DATE |  10 |  GDP\_PRACTICE\_APPLI ES\_FROM | Date Patient Joined GDP Practice     Must be in format: DD/MM/YYYY, must be populated if gdp populated.  Loaded into: PATIENT\_MASTER.practice\_applies\_start |
| :---- | :---: | ----- | :---- |

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 25

| TABLE NAME: LOAD\_PMIIDS  Additional patient identifiers.   Linked to LOAD\_PMI via loadpmi\_record\_number  Case Note Identifiers: all identifiers, combination of additional\_id\_type, additional\_id and volume, must be loaded into LOAD\_PMIIDS to allow for the case note tracking history to be successfully migrated from LOAD\_PMICASENOTEHISTORY.  Creates records in:  PATIENT\_IDS  Loaded via:   OASLOADPMI\_PACKAGE.load\_patient\_ids |
| :---- |

 26   
 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADPMI\_RECORD\_NUMBER Foreign key to LOAD\_PMI.record\_number 

| VARCHAR2 | 10 |
| :---: | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique patient identifier id from the source system. 

| VARCHAR2 | 30 |
| :---: | :---- |

  MAIN\_CRN 

LOAD\_PMI.main\_crn. 

VARCHAR2 80 ADDITIONAL\_ID\_TYPE Additional Id Type Maps to: code type 9 \- 

Loaded as mapped into: PATIENT\_IDS.id\_type\_code   
e.g. MIU for "A\&E Number", TEMP for "Temporary Case Note    
File" 

 

| VARCHAR2 | 30 |   ADDITIONAL\_ID |  Additional id as related to the above id type. Loaded into: PATIENT\_IDS.id\_number |
| ----- | :---- | :---- | :---- |
| NUMBER | 42 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  VOLUME |  Volume Number   Used for case note files. Must not be blank for case note identifiers.   If not currently held in source system, recommend loading 1.Loaded into: PATIENT\_IDS.volume\_seq |

| TABLE NAME: LOAD\_PMIALIASES  Patient aliases.   Linked to LOAD\_PMI via loadpmi\_record\_number.  Creates records in:  PATIENT\_NAMES  Loaded via:   OASLOADPMI\_PACKAGE.load\_patient\_aliases |
| :---- |

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADPMI\_RECORD\_NUMBER Foreign key to LOAD\_PMI.record\_number 

| VARCHAR2 | 10 |
| :---: | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique alias id from the source system. 

| VARCHAR2 | 30 |
| :---: | :---- |

  MAIN\_CRN 

LOAD\_PMI.main\_crn. 

VARCHAR2 80 SEX Maps to: code type 3 "Sex" Loaded as mapped into: PATIENT\_NAMES.sex 

| VARCHAR2 | 80 |
| :---: | :---- |

  TITLE Maps to: code type 29 "Title" 

Loaded as mapped into: PATIENT\_NAMES.title 

VARCHAR2 40 PAT\_NAME\_1 Loaded into: PATIENT\_NAMES.pat\_name\_1 ~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 27

| VARCHAR2 | 40 |
| :---: | :---- |

  PAT\_NAME\_2 Loaded into: PATIENT\_NAMES.pat\_name\_2 

VARCHAR2 40 PAT\_NAME\_3 Loaded into: PATIENT\_NAMES.pat\_name\_3

| VARCHAR2 | 40 |   PAT\_NAME\_FAMILY |  Loaded into: PATIENT\_NAMES.pat\_name\_family |
| :---: | :---- | :---- | :---- |

DATE 10 DATE\_OF\_BIRTH Must be in format: DD/MM/YYYY Loaded into: PATIENT\_NAMES.date\_of\_birth 

| VARCHAR2 | 80 |
| :---: | :---- |

  MARITAL\_CODE Maps to: code type 2 "Marital Status" Loaded as mapped into: PATIENT\_NAMES.marital\_code

DATE 10 APPLIES\_START Must be in format: DD/MM/YYYY Loaded into: PATIENT\_NAMES.applies\_start 

| DATE | 10 |   APPLIES\_END |  Must be in format: DD/MM/YYYY  Loaded into: PATIENT\_NAMES.applies\_end |
| :---- | :---- | :---- | ----- |

 

| TABLE NAME: LOAD\_PMIADDRS Alternative address details.   Linked to LOAD\_PMI via loadpmi\_record\_number. Creates records in:  PATIENT\_CONTACTS  Loaded via:   OASLOADPMI\_PACKAGE.load\_patient\_addresses |
| :---- |

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADPMI\_RECORD\_NUMBER Foreign key to LOAD\_PMI.record\_number 

| VARCHAR2 | 10 |
| :---: | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.    
~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 28  
Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique address id from the source system.

| VARCHAR2 | 30 |   MAIN\_CRN | LOAD\_PMI.main\_crn. |
| :---: | :---- | :---- | :---- |

VARCHAR2 1 ADDRESS\_TYPE Only two accepted values: P for Permanent OR C for TemporaryLoaded into: PATIENT\_CONTACTS.address\_type 

| VARCHAR2 | 80 |
| :---: | :---- |

  ADDRESS\_1 Loaded into: PATIENT\_CONTACTS.address\_1 

VARCHAR2 80 ADDRESS\_2 Loaded into: PATIENT\_CONTACTS.address\_2 

| VARCHAR2 | 80 |
| :---: | :---- |

  ADDRESS\_3 Loaded into: PATIENT\_CONTACTS.address\_3 

VARCHAR2 80 ADDRESS\_4 Loaded into: PATIENT\_CONTACTS.address\_4 

| VARCHAR2 | 20 |
| :---: | :---- |

  POST\_CODE Loaded into: PATIENT\_CONTACTS.post\_code 

VARCHAR2 80 COUNTRY\_CODE Maps to: code type 333 "Country Codes" Loaded as mapped into: PATIENT\_CONTACTS.country\_code

| VARCHAR2 | 20 |
| :---: | :---- |

  PHONE\_1 Loaded into: PATIENT\_CONTACTS.phone\_1 

VARCHAR2 20 PHONE\_2 Loaded into: PATIENT\_CONTACTS.phone\_2 

| VARCHAR2 | 20 |
| :---: | :---- |

  PHONE\_3 Loaded into: PATIENT\_CONTACTS.phone\_3 

DATE 10 APPLIES\_START Must be in format: DD/MM/YYYY Loaded into: PATIENT\_CONTACTS.applies\_start

| DATE | 10 |   APPLIES\_END |  Must be in format: DD/MM/YYYY  Must be populated if address\_type \= P.  Loaded into: PATIENT\_CONTACTS.applies\_end |
| :---- | :---- | :---- | ----- |

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 29

| TABLE NAME: LOAD\_PMICONTACTS Alternative person contact details.  Linked to LOAD\_PMI via loadpmi\_record\_number.Creates records in:  PATIENT\_CONTACTS  Loaded via:   OASLOADPMI\_PACKAGE.load\_patient\_contacts |
| :---- |

 30   
 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADPMI\_RECORD\_NUMBER Foreign key to LOAD\_PMI.record\_number 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique contact id from the source system. 

| VARCHAR2 | 30 |
| :---- | :---- |

  MAIN\_CRN 

LOAD\_PMI.main\_crn. 

   
VARCHAR2 80 CONTACT\_TYPE Maps to: code type 18 "Contact Type" Loaded into: PATIENT\_CONTACTS.contact\_type 

e.g. Carer, Emergency, Guardian, School 

| VARCHAR2 | 80 |   RELATIONSHIP |  Contact's relationship to the patient.  Maps to: code type 17 "Contact Relationship" Loaded into: PATIENT\_CONTACTS.relationship |
| :---- | :---- | :---- | ----- |
| VARCHAR2 | 1 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  PARENTAL\_RESPONSIBILITY |  Contact has parental responsibiity for the patient.  Only two accepted values: Y for Yes OR N for No Loaded into: PATIENT\_CONTACTS.parental\_responsibility\_flag |

| VARCHAR2 | 80 |
| :---- | :---- |

  TITLE Maps to: code type 29 "Title" 

Loaded as mapped into: PATIENT\_CONTACTS.title 

VARCHAR2 40 NAME\_1 Loaded into: PATIENT\_CONTACTS.name\_1 

| VARCHAR2 | 40 |
| :---- | :---- |

  NAME\_FAMILY Loaded into: PATIENT\_CONTACTS.name\_family 

VARCHAR2 80 ADDRESS\_1 Loaded into: PATIENT\_CONTACTS.address\_1 

| VARCHAR2 | 80 |
| :---- | :---- |

  ADDRESS\_2 Loaded into: PATIENT\_CONTACTS.address\_2 

VARCHAR2 80 ADDRESS\_3 Loaded into: PATIENT\_CONTACTS.address\_3 

| VARCHAR2 | 80 |
| :---- | :---- |

  ADDRESS\_4 Loaded into: PATIENT\_CONTACTS.address\_4 

VARCHAR2 20 POST\_CODE Loaded into: PATIENT\_CONTACTS.post\_code 

| VARCHAR2 | 80 |
| :---- | :---- |

  COUNTRY\_CODE Maps to: code type 333 "Country Codes" ~~Note type \= "38456" \- "Notes For Contacts", Subject \= "Contact~~    
Loaded as mapped into: PATIENT\_CONTACTS.country\_code

VARCHAR2 20 PHONE\_1 Loaded into: PATIENT\_CONTACTS.phone\_1 

| VARCHAR2 | 20 |
| :---- | :---- |

  PHONE\_2 Loaded into: PATIENT\_CONTACTS.phone\_2 

VARCHAR2 20 PHONE\_3 Loaded into: PATIENT\_CONTACTS.phone\_3 

| VARCHAR2 | 2000 |
| :---- | :---- |

  COMMENTS Maps to: code type 297 "Multiple Note Types" 

Notes" 

Loaded into: OASIS\_MULTIPLE\_NOTES.text 

~~© 2026 Altera Digita~~l ~~Health Inc. and/or~~ ~~its subsidiaries. All rights reserved.~~ 31  
DATE 10 APPLIES\_START Must be in format: DD/MM/YYYY Loaded into: PATIENT\_CONTACTS.applies\_start

| DATE | 10 |   APPLIES\_END |  Must be in format: DD/MM/YYYY  Loaded into: PATIENT\_CONTACTS.applies\_end |
| :---- | :---- | :---- | ----- |

| TABLE NAME: LOAD\_PMIALLERGIES Patient allergy details.   Linked to LOAD\_PMI via loadpmi\_record\_number.Creates records in:  PATIENT\_WARNINGS  Loaded via:   OASLOADPMI\_PACKAGE.load\_patient\_allergies |
| :---- |

~~© 2026 Altera Digita~~l ~~Health Inc. and/or~~ ~~its subsidiaries. All rights reserved.~~ 32   
 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADPMI\_RECORD\_NUMBER Foreign key to LOAD\_PMI.record\_number 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique allergy id from the source system. 

| VARCHAR2 | 30 |
| :---- | :---- |

~~Note type \= "72" \- "Allergies", Subject \= "Allergy"~~   
  MAIN\_CRN 

LOAD\_PMI.main\_crn. 

VARCHAR2 80 ALLERGY\_CODE Maps to: code type 299 "Allergies" Loaded into: PATIENT\_WARNINGS.warning\_code 

e.g. Latex, Magnesium, Nuts, Penicillin G 

| VARCHAR2 | 80 |
| :---- | :---- |

  ALLERGY\_COMMENT Maps to: code type 297 "Multiple Note Types" Loaded into: OASIS\_MULTIPLE\_NOTES.text 

DATE 10 APPLIES\_START Must be in format: DD/MM/YYYY Loaded into: PATIENT\_WARNINGS.applies\_start

| DATE | 10 |   APPLIES\_END |  Must be in format: DD/MM/YYYY  Loaded into: PATIENT\_WARNINGS.applies\_end |
| :---- | :---- | :---- | ----- |

| TABLE NAME: LOAD\_PMISTAFFWARNINGS Information staff should be aware of with regard to the patient.   Linked to LOAD\_PMI via loadpmi\_record\_number.Creates records in:  PATIENT\_WARNINGS  Loaded via:   OASLOADPMI\_PACKAGE.load\_staff\_warnings |
| :---- |

~~© 2026 Altera Digital~~ ~~Health Inc. and/or~~ ~~its subsidiaries. All rights reserved.~~ 33   
 

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADPMI\_RECORD\_NUMBER Foreign key to LOAD\_PMI.record\_number 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique warning id from the source system. 

| VARCHAR2 | 30 |
| :---- | :---- |

~~Note type \= "16456" \- "Patient Warnings: To Staff", Subject~~    
  MAIN\_CRN 

LOAD\_PMI.main\_crn. 

VARCHAR2 80 WARNING\_CODE Maps to: code type 10174 "Patient Warnings: To Staff" Loaded into: PATIENT\_WARNINGS.warning\_code

e.g. Blind, Deaf, HIV, Munchausen's Syndrome, Suicide    
Risk, Violent 

| VARCHAR2 | 80 |
| :---- | :---- |

  WARNING\_COMMENT Maps to: code type 297 "Multiple Note Types" 

\= "Staff Warning" 

Loaded into: OASIS\_MULTIPLE\_NOTES.text 

DATE 10 APPLIES\_START Must be in format: DD/MM/YYYY Loaded into: PATIENT\_WARNINGS.applies\_start

| DATE | 10 |   APPLIES\_END |  Must be in format: DD/MM/YYYY Loaded into: PATIENT\_WARNINGS.applies\_end |
| :---- | :---- | :---- | :---- |

| TABLE NAME: LOAD\_PMIGPAUDIT Patient GP history, i.e. previous GPs and practices.  Linked to LOAD\_PMI via loadpmi\_record\_number. Creates records in:  PATIENT\_GP\_AUDIT  PATIENT\_GP\_LINK  Loaded via:   OASLOADPMI\_PACKAGE.load\_gp\_audit |
| :---- |

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADPMI\_RECORD\_NUMBER Foreign key to LOAD\_PMI.record\_number 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  

Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique audit id from the source system. 

| VARCHAR2 | 30 |
| :---- | :---- |

  MAIN\_CRN   
LOAD\_PMI.main\_crn. 

VARCHAR2 10 GP\_NATIONAL\_CODE National General Practitioner Code Maps to: GP\_MASTER.registration\_code 

Loaded as mapped into:  

PATIENT\_GP\_AUDIT.gp\_id 

PATIENT\_GP\_LINK.gp\_id 

e.g. C0000048 , D2008756, G3293160 

| VARCHAR2 | 10 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved.~~  PRACTICE\_NATIONAL\_CODE |  National Practice Code for the GP Maps to: GP\_PRACTICE\_MASTER.gp\_practice\_codeLoaded as mapped into:   PATIENT\_GP\_AUDIT.practice\_id PATIENT\_GP\_LINK.practice\_id e.g. A81006, D82076, K81022 |
| :---- | :---- | :---- | :---- |

 34

VARCHAR2 20 PRACTICE\_POST\_CODE Practice Post Code for the GP 

Not loaded but used when mapping to distinguish    
between sub-practices which may have the same    
National Practice Code. 

| DATE | 10 |   APPLIES\_START |  Date Patient Joined GP Practice   Must be in format: DD/MM/YYYY Loaded into:   PATIENT\_GP\_AUDIT.applies\_start PATIENT\_GP\_LINK.applies\_start |
| :---- | :---- | :---- | ----- |
| DATE | 10 |   APPLIES\_END |  Date Patient Left GP Practice  Must be in format: DD/MM/YYYY Loaded into:   PATIENT\_GP\_AUDIT.applies\_end PATIENT\_GP\_LINK.applies\_end |

| TABLE NAME: LOAD\_CASENOTELOCS Locations to which case notes can be tracked and/or stored.   Creates records in:  OASIS\_LOCATIONS  Loaded via:   OASLOADPMI\_PACKAGE.load\_casenote\_locations |
| :---- |

 

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

~~© 2026 Altera Digital~~ ~~Health Inc. and/or~~ ~~its subsidiaries. All rights reserved.~~ 35  
VARCHAR2 10 SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System"

| VARCHAR2 | 100 |   EXTERNAL\_SYSTEM\_ID |  Unique location id from the source system. |
| :---- | :---- | :---- | :---: |

VARCHAR2 30 HOSPITAL\_CODE For use in multi-provider implementations to identify  hospital provider. 

Maps to: code type 10638 "Oasis Hospital Site Code For    
Dataload" 

Loaded as mapped into: OASIS\_LOCATIONS.hospital\_id

e.g. Hospital Group 1, Hospital Group 2 

| VARCHAR2 | 80 |
| :---- | :---- |

  SITE Hospital site within the hospital provider. Maps to: code type 10454 "Site Codes" 

Loaded as mapped into: OASIS\_LOCATIONS.site\_code

e.g. Site A in Hospital Group 1, Site B in Hospital Group 1 

VARCHAR2 80 LOCATION\_TYPE Type of hospital location. Maps to: code type 302 "Location Type" 

Loaded as mapped into: OASIS\_LOCATIONS.location\_type

e.g. Assessment Area, MIU, Operating Area, Ward

| VARCHAR2 | 10 |
| :---- | :---- |

  USER\_CODE Short code for the location. 

Loaded into: OASIS\_LOCATIONS.user\_code 

VARCHAR2 80 DESCRIPTION Long name of the location. 

Loaded into: OASIS\_LOCATIONS.descripton 

| VARCHAR2 | 1 |   ACTIVE\_FLAG |  Whether or not the location is active, allows for migration of historic locations.  Only two accepted values: Y for Yes OR N for NoLoaded into: OASIS\_LOCATIONS.active\_flag |
| :---- | :---- | :---- | :---- |

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 36

| TABLE NAME: LOAD\_PMICASENOTEHISTORY  Case note tracking history including current and home location.   Case Note Identifiers: all identifiers, combination of id\_type, id\_number and volume must previously have been loaded into LOAD\_PMIIDS to allow for the successful migration of tracking history.  Home Location: is derived from the first tracking record. This is assumed to be where the case note was raised.  Current Location: is derived from the last tracking record. The end\_datefield should be blank on this record.  Tracking Locations: all tracking locations must have been either loaded using LOAD\_CASENOTELOCS or manually entered via SYSLOCAT to allow for the successful migration of tracking history.  Creates records in:  PATIENT\_ID\_LOCATIONS  Loaded via:   OASLOADPMI\_PACKAGE.load\_casenote\_history  |
| :---- |

 37   
 


 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

VARCHAR2 10 SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

| VARCHAR2 | 100 |
| :---- | :---- |

  EXTERNAL\_SYSTEM\_ID Unique tracking id from the source system. 

VARCHAR2 80 ID\_TYPE For the purpose of mapping id. 

As previously loaded into    
LOAD\_PMIIDS.addtional\_id\_type 

Maps to: PATIENT\_IDS.id\_type\_code 

Loaded as mapped into:    
PATIENT\_ID\_LOCATIONS.patient\_ids\_id 

| VARCHAR2 | 30 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved.~~  ID\_NUMBER |  For the purpose of mapping id.  As previously loaded into LOAD\_PMIIDS.id\_numberMaps to: PATIENT\_IDS.id\_number  Loaded as mapped into:   PATIENT\_ID\_LOCATIONS.patient\_ids\_id |
| :---- | :---- | :---- | :---- |

NUMBER 42 VOLUME For the purpose of mapping id. As previously loaded into LOAD\_PMIIDS.volume

Maps to: PATIENT\_IDS.volume\_seq 

Loaded as mapped into:    
PATIENT\_ID\_LOCATIONS.patient\_ids\_id 

| VARCHAR2 | 30 |
| :---- | :---- |

  HOSPITAL\_CODE For the purpose of mapping location. 

As previously loaded into    
LOAD\_CASENOTELOCS.hospital\_code 

Maps to: OASIS\_LOCATIONS.hosptial\_id 

Loaded as mapped into:    
PATIENT\_ID\_LOCATIONS.location\_id 

VARCHAR2 80 SITE For the purpose of mapping location. As previously loaded into LOAD\_CASENOTELOCS.site

Maps to: OASIS\_LOCATIONS.site\_code 

Loaded as mapped into:    
PATIENT\_ID\_LOCATIONS.location\_id 

| VARCHAR2 | 10 |
| :---- | :---- |

  LOCATION\_CODE For the purpose of mapping location. 

As previously loaded into    
LOAD\_CASENOTELOCS.user\_code 

Maps to: OASIS\_LOCATIONS.user\_code 

Loaded as mapped into:    
PATIENT\_ID\_LOCATIONS.location\_id 

DATE 10 START\_DATE Date Case Note Tracked To Location Must be in format: DD/MM/YYYY HH24:MI 

Loaded into: PATIENT\_ID\_LOCATIONS.start\_date

| DATE | 10 |
| :---- | :---- |

  END\_DATE Date Case Note Tracked From Location Must be in format: DD/MM/YYYY HH24:MI 

Loaded into: PATIENT\_ID\_LOCATIONS.end\_date

VARCHAR2 80 SHORT\_NOTE Short tracking note. 

Loaded into: PATIENT\_ID\_LOCATIONS.short\_note 

| VARCHAR2 | 2000 |   COMMENT\_1  | Maps to: code type 297 "Multiple Note Types"Note type \= "55333" \- "File Tracking Notes", Subject \= "Case File Notes"  Loaded into: OASIS\_MULTIPLE\_NOTES.text |
| :---- | :---- | :---- | :---- |
| VARCHAR2 | 2000 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  COMMENT\_2  | Maps to: code type 297 "Multiple Note Types" Note type \= "55333" \- "File Tracking Notes", Subject \= "Case File Notes"  Loaded into: OASIS\_MULTIPLE\_NOTES.text |

 

 

 38

REFERRAL TO TREATMENT PATHWAYS 

| TABLE NAME: LOAD\_RTT\_PATHWAYS  Referral to treat pathway details. Pathways link to activity via the referralCreates records in:  REFERRAL\_TO\_TREAT\_PATHWAYS  Loaded via:   OASLOADREF\_PACKAGE.load\_rtt\_pathways  |
| :---- |

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

VARCHAR2 10 SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

| VARCHAR2 | 100 |
| :---- | :---- |

  EXTERNAL\_SYSTEM\_ID Unique pathway id from the source system. 

VARCHAR2 80 MAIN\_CRN\_TYPE Main hospital number id type as loaded into  LOAD\_PMI.main\_crn\_type 

| VARCHAR2 | 30 |
| :---- | :---- |

  MAIN\_CRN Main hospital number as loaded into LOAD\_PMI.main\_crn

VARCHAR2 20 PATHWAY\_ID Unique pathway id used in CDS reporting. Loaded into: REFERRAL\_TO\_TREAT\_PATHWAYS.pathway\_id

| VARCHAR2 | 20 |
| :---- | :---- |

  UBRN Connecting for Health Unique Booking Reference Number Loaded into: REFERRAL\_TO\_TREAT\_PATHWAYS.ubrn 

DATE 10 PATHWAY\_START\_DATE Must be in format: DD/MM/YYYY HH24:MI Loaded into: REFERRAL\_TO\_TREAT\_PATHWAYS.pathway\_start\_date

© ~~2026 Altera Digital Health Inc. and/~~o~~r its subsidiaries. All rights reserved.~~ 39

| DATE | 10 |
| :---- | :---- |

  PATHWAY\_END\_DATE Must be in format: DD/MM/YYYY HH24:MI Loaded into: REFERRAL\_TO\_TREAT\_PATHWAYS.pathway\_end\_date

VARCHAR2 80 DESCRIPTION Short pathway description. 

Loaded into: REFERRAL\_TO\_TREAT\_PATHWAYS.description

| VARCHAR2 | 80 |   PATHWAY\_CODED\_DESC\_CODE | Maps to: code type 10869 "PATHWAY CODED DESCRIPTIONS"Loaded as mapped into:    REFERRAL\_TO\_TREAT\_PATHWAYS.PATHWAY\_CODED\_DESC\_CODE |
| :---- | :---- | :---- | :---- |

VARCHAR2 80 PATHWAY\_END\_EVENT The event that ended the pathway Maps to: code type 10833 " RTT STOP EVENT REASON CODES " 

Loaded as mapped into:    
REFERRAL\_TO\_TREAT\_PATHWAYS.PATHWAY\_END\_EVENT   
~~e.g. First Activity \- First Activity In A Referral To Treatment Period,~~    
e.g. Patient Request, Admin, Error Correction, Clinician Request 

| VARCHAR2 | 80 |
| :---- | :---- |

  PATHWAY\_SPECIALTY The initial specialty that the pathway is linked to. Maps to: code type 10025 " SPECIALTY" 

Loaded as mapped into:    
REFERRAL\_TO\_TREAT\_PATHWAYS.PATHWAY\_SPECIALTY 

VARCHAR2 80 PATHWAY\_STATUS The status of the pathway .  
Maps to: code type 10844 " REFERRAL TO TREAT (RTT) STATUS " 

Loaded as mapped into:    
REFERRAL\_TO\_TREAT\_PATHWAYS.PATHWAY\_STATUS 

Start Of Active Monitoring Initiated By The Patient, Patient Declined    
Offered Treatment 

| VARCHAR2 | 50 |   PATHWAY\_TYPE |  Pathway Type only two values allowed either RTT or NON-RTT |
| :---- | :---- | :---- | ----: |

REFERRALS 

| TABLE NAME: LOAD\_REFERRALSInpatient and outpatient referrals. Creates records in:  APPOINTMENT\_REFERRALS Loaded via:   OASLOADREF\_PACKAGE.load\_referrals |
| :---- |

 

 

 

DATATYPE LENGTH NAME COMMENTS 

| Datatype | Length |
| :---- | :---- |

  Name Comments   
~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 40  
NUMBER 42 RECORD\_NUMBER Unique identifier for this extracted record.

| NUMBER | 42 |   LOADRTTPWY\_RECORD\_NUMBER | Foreign key to LOAD\_RTT\_PATHWAYS.record\_number   |
| :---- | :---- | :---- | :---- |
| VARCHAR2 | 10 |   SYSTEM\_CODE |  Unique identifier for the originating system.   Maps to: code type 10599 "Dataload System" |

| VARCHAR2 | 100 |
| :---- | :---- |

  EXTERNAL\_SYSTEM\_ID Unique referral id from the source system. 

VARCHAR2 80 MAIN\_CRN\_TYPE Main hospital number id type as loaded into  LOAD\_PMI.main\_crn\_type 

| VARCHAR2 | 30 |
| :---- | :---- |

  MAIN\_CRN Main hospital number as loaded into LOAD\_PMI.main\_crn

VARCHAR2 80 PATIENT\_CATEGORY Maps to: code type 10087 "Patient Contract Category" Loaded as mapped into:  

APPOINTMENT\_REFERRALS.patient\_category 

e.g. NHS, Private, Overseas Visitor 

| DATE | 10 |
| :---- | :---- |

  FIRST\_SEEN Must be in format: DD/MM/YYYY Loaded into: APPOINTMENT\_REFERRALS.patient\_firstseen\_date

DATE 10 OVERRIDE\_WAIT\_RESET   
Used for calculating waiting time if not loading cancelled bookings.   
\_DATE   
Must be in format: DD/MM/YYYY 

Loaded into: APPOINTMENT\_REFERRALS.override\_waitreset\_date

| VARCHAR2 | 1 |
| :---- | :---- |

  REF\_NEW\_FOLLOWUP\_   
Only two accepted values: N for New OR F for Followup   
FLAG   
Loaded into: APPOINTMENT\_REFERRALS.new\_followup\_flag

 

   
 

 

 

 

   
DATE 10 REF\_DATE Must be in format: DD/MM/YYYY Loaded into:  

APPOINTMENT\_REFERRALS.ref\_date 

| DATE | 10 |   REF\_RECEIVED\_DATE |  Must be in format: DD/MM/YYYY Loaded into: APPOINTMENT\_REFERRALS.date\_received |
| :---- | :---- | :---- | ----- |
| VARCHAR2 | 80 |   REF\_SOURCE © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. |  Maps to: code depending on value of encounter\_type User   Encounter   Referral   Referral Source Code  Code  Type   Source   Type Description Description  Code   Type  A WARD   10228 REFERRAL SOURCE   ATTENDER  (WARD ATTENDER)  C SERVICE   10138 ORDER ENCOUNTERS  ORDERING  REF SOURCE D DAYCASE 10107 INPATIENT REFERRAL SOURCE E EMERGENCY 10082 A\&E REFERRED FROM TYPES  H THERAPIES 10472 REFERRAL SOURCE  (THERAPIES) |

 41

| VARCHAR2 | 10 |
| :---- | :---- |

I IN-PATIENT 10107 INPATIENT REFERRAL  

SOURCE 

L OUT-PATIENT  

10034 REFERRAL SOURCE  

WAITING LIST   
(OUTPATIENT) 

O OUT-PATIENT 10034 REFERRAL SOURCE  

(OUTPATIENT) 

R RADIOLOGY 10229 REFERRAL SOURCE  

(RADIOLOGY) 

S RESIDENTIAL  

10107 INPATIENT REFERRAL  

CARE   
SOURCE 

T THEATRE 10231 REFERRAL SOURCE  

(THEATRES) 

U COMMUNITY  

10379 COMMUNITY CARE REF  

CARE   
SOURCE 

W TREATMENT  

10107 INPATIENT REFERRAL  

WAITING LIST   
SOURCE 

X EXTERNAL Undefine 

No ref\_source selectable  

d   
in OASIS 

Y DAY CARE 10230 REFERRAL SOURCE (DAY  

CARE) 

| Z |  REFERRAL |  Undefine d | No ref\_source  |
| :---- | ----: | ----- | :---- |

Loaded as mapped into:    
APPOINTMENT\_REFERRALS.ref\_source   
APPOINTMENTS.ref\_source   
e.g. Consultant Within Trust, Dentist, GP, Midwife 

  REF\_GP\_CODE National General Practitioner Code of Referring GP Maps to: GP\_MASTER.registration\_code 

Loaded as mapped into: APPOINTMENT\_REFERRALS.ref\_gp  
e.g. C0000048 , D2008756, G3293160 

VARCHAR2 10 REF\_PRACTICE\_CODE National Practice Code for the Referring GP Maps to: GP\_PRACTICE\_MASTER.gp\_practice\_code 

Loaded as mapped into: APPOINTMENT\_REFERRALS.ref\_practice  
e.g. A81006, D82076, K81022 

| VARCHAR2 | 20 |
| :---- | :---- |

  REF\_PRACTICE\_POSTCO 

Practice Post Code for the GP   
DE   
Not loaded but used when mapping to distinguish between sub practices which may have the same National Practice Code. 

VARCHAR2 80 REF\_URGENCY Maps to: code type 10449 "Outpatient Waiting List Urgency" ~~© 2026 Altera Digital Health Inc. and/~~o~~r its subsidiaries. All rights reserve~~d~~.~~ 42  
Loaded as mapped into: APPOINTMENT\_REFERRALS.ref\_urgency

e.g. Routine, Soon, Urgent

| VARCHAR2 | 80 |   REF\_TYPE |  Maps to: code type 10092 "Referral Type" Loaded as mapped into: APPOINTMENT\_REFERRALS.ref\_typee.g. Critical, Rapid Access, Standard |
| :---- | :---- | :---- | :---- |

VARCHAR2 80 REF\_REASON Maps to: code type 10093 "Outpatient Referral Reason" Loaded as mapped into: APPOINTMENT\_REFERRALS.ref\_reason

e.g. Advice/Consultation, Specific Procedure 

| VARCHAR2 | 80 |
| :---- | :---- |

  REF\_SPECIALTY Maps to: code type 10025 "Specialty" Loaded as mapped into: APPOINTMENT\_REFERRALS.specialty\_code

VARCHAR2 80 REF\_TEAM Maps to: code type 10721 "Teams For Dataload Mapping" Mapped value must exist in: TEAMS.user\_code 

Loaded as mapped into: APPOINTMENT\_REFERRALS.team\_id

| VARCHAR2 | 30 |
| :---- | :---- |

  REF\_CONSULTANT Maps to: STAFF\_IDS.id\_number Loaded as mapped into:  

APPOINTMENT\_REFERRALS.consultant\_code 

~~Note type \= "101" \- "Appointment Referral Notes"~~   
VARCHAR2 80 REF\_OUTCOME Maps to: code type 10728 "Appointment Referral Outcome Codes" Loaded as mapped into: APPOINTMENT\_REFERRALS.outcome\_code

e.g. Rejected, Treatment Complete 

| DATE | 10 |
| :---- | :---- |

  REF\_DISCHARGE\_DATE Must be in format: DD/MM/YYYY Loaded into: APPOINTMENT\_REFERRALS.discharged\_date 

   
VARCHAR2 2000 REF\_COMMENT Maps to: code type 297 "Multiple Note Types" 

Subject \= "Appointment Referral Notes" 

Loaded into: OASIS\_MULTIPLE\_NOTES.text 

| VARCHAR2 | 1 |   ENCOUNTER\_TYPE © 2026 Altera Digital Health Inc. and/o~~r its subsidiaries. All rights reserved~~. |  Must be one of  Encounter Type Encounter Type Description A WARD ATTENDER C SERVICE ORDERING D DAYCASE E EMERGENCY H THERAPIES  I IN-PATIENT |
| :---: | :---- | :---- | :---- |

 43

|  |  |  | L OUT-PATIENT WAITING LIST O OUT-PATIENT R RADIOLOGY S RESIDENTIAL CARE  T THEATRE U COMMUNITY CARE W TREATMENT WAITING LIST X EXTERNAL Y DAY CARE  Z REFERRAL |
| :---- | :---- | :---- | :---- |

© ~~2026 Altera Digital Health Inc. and/~~o~~r its subsidiaries. All rights reserved.~~ 44   
 

REFERRAL TO TREATMENT PERIODS 

| TABLE NAME: LOAD\_RTT\_PERIODS Referral to treat periods  Creates records in:  REFERRAL\_TO\_TREAT\_PERIODS Loaded via:   OASLOADREF\_PACKAGE.load\_rtt\_periods |
| :---- |

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADRTTPWY\_RECORD\_   
Foreign key to LOAD\_RTT\_PATHWAYS.record\_number 

NUMBER 

| NUMBER | 42 |
| :---- | :---- |

  LOADREF\_RECORD\_NU   
Foreign key to LOAD\_REFERRALS.RECORD\_NUMBER 

MBER 

VARCHAR2 10 SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System"

| VARCHAR2 | 100 |   EXTERNAL\_SYSTEM\_ID |  Unique period id from the source system. |
| :---- | :---- | ----: | :---- |

DATE 10 CLOCK\_START Must be in format: DD/MM/YYYY HH24:MI Loaded into: REFERRAL\_TO\_TREAT\_PERIODS.clock\_start 

| VARCHAR2 | 80 |
| :---- | :---- |

  START\_EVENT\_REASON\_   
Maps to: code type 10832 "RTT Event Codes" 

CODE   
Loaded as mapped into:  

REFERRAL\_TO\_TREAT\_PERIODS.start\_even\_reason\_code 

e.g. Elective Trauma, Investigations Complete, IPT 

DATE 10 CLOCK\_STOP Must be in format: DD/MM/YYYY HH24:MI Loaded into: REFERRAL\_TO\_TREAT\_PERIODS.clock\_stop

| VARCHAR2 | 80 |
| :---- | :---- |

  STOP\_EVENT\_REASON\_C   
Maps to: code type 10833 "RTT Stop Event Reason Codes" 

ODE   
Loaded as mapped into:  

REFERRAL\_TO\_TREAT\_PERIODS.stop\_even\_reason\_code 

e.g. Admited, Regular F/UP, Treatment Given, Watchful Wait 

VARCHAR2 80 BREACH\_REASON\_CODE Coded reason this period has passed its breach date. Maps to: code type 10884 

Loaded as mapped into:  

REFERRAL\_TO\_TREAT\_PERIODS.BREACH\_REASON\_CODE 

| VARCHAR2 | 500 |   BREACH\_REASON\_TEXT |  Free format text recording the reason why this period has passed its  breach date. |
| :---- | :---- | ----- | ----- |
| VARCHAR2 | 1 |   REFERRAL\_AS\_START\_ENCOUNTER | Y or N    If Y then parent referral\_id is assigned to   referral\_to\_treat\_periods.start\_encounter\_id, otherwise the field is left blank. |

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 45  
REFERRAL TO TREATMENT EVE NTS 

| TABLE NAME: LOAD\_RTT\_EVENTS Referral to treat events.  Creates records in:  REFERRAL\_TO\_TREAT\_EVENTS Loaded via:   OASLOADREF\_PACKAGE.load\_rtt\_events |
| :---- |

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADRTTPRD\_RECORD\_   
Foreign key to LOAD\_RTT\_PERIODS.record\_number 

NUMBER 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique RTT Event Id from the source system. 

| VARCHAR2 | 19 |
| :---- | :---- |

  EVENT\_DATE Mandatory Field 

The date/time the event occurred. 

Must be in format: DD/MM/YYYY HH24:MI:SS   
Loaded into referral\_to\_treat\_events.event\_date 

 

 

 

   
VARCHAR2 80 EVENT\_ACTION\_CODE The type of event. 

Maps to: code type 10883  

| VARCHAR2 | 80 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  EVENT\_REASON\_CODE | then the Event Reason Code must be mapped to a valid code of code ~~type 10833 \- RTT STOP EVENT REASON CODES.~~  The reason for the event:  If the Event Action Code (code type 10883\) is one of CONTINUE, END\_PAUSE, NOACTION, PAUSE, START, START\_STOP then the Event Reason Code must be mapped to a valid code of code type 10832 \-RTT START EVENT REASON CODES.  If the Event Action Code (code type 10883\) is either ENDRTT or STOP  |
| :---- | :---- | :---- | ----- |

 46  
~~e.g. First Activity \- First Activity In A Referral To Treatment Period,~~    
VARCHAR2 80 RTT\_STATUS REFERRAL\_TO\_TREAT\_PATHWAYS.PATHWAY\_STATUS at the time  the event was created. 

Maps to: code type 10844 " REFERRAL TO TREAT (RTT) STATUS " 

Loaded as mapped into:    
V A L I D A T I O N R U L E S A P P L I E D T O P E R I O D S A N D E V E N T S A R E :   
REFERRAL\_TO\_TREAT\_PATHWAYS.PATHWAY\_STATUS 

Start Of Active Monitoring Initiated By The Patient, Patient Declined    
~~If a period has a START\_STOP event, then it can have no other events.~~   
Offered Treatment 

| VARCHAR2 | 80 |   EVENT\_TEXT |  Short text note detailing event, this allows debug etc (Replaces start\_event\_text and stop\_event\_text on referral\_to\_treat\_periods) |
| :---- | :---- | :---- | :---- |

 

 

Event types not in START, STOP, START\_STOP and ENDRTT must lie within the parent period start and end    
Each period cannot have more than one event of each event\_action\_code type START, STOP, START\_STOP,  ENDRTT, and also cannot have both a STOP and an ENDRTT. 

A period with events must have a START or START\_STOP event. 

If a period has both a START and a STOP event, the event\_date of the START must not fall after that of the  STOP event. 

Event date must lie between pathway start and end dates. 

START, STOP, START\_STOP and ENDRTT events with event\_date before SYSTEM date/time must not overlap other periods date ranges within the same pathway. 

dates.

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 47  
OUTPATIEN TS WAIT ING L IST DATA 

| Either clinic wait list groups are configured manually in Altera PAS prior to Data migration, and the   TABLE NAME: LOAD\_OPDWAITLIST  Outpatient waiting list entries.   Clinic Waitlist Groups:  There are two possible ways of linking waiting list entries to Clinic Wait List groups:  LIST\_CODE field is mapped to the Clinic Wait List Group user code via code type 10662, or these are created from the load\_opdwaitlist records from distinct combinations of:  hospital\_code  site  list\_code  list\_name  encounter\_type  specialty  where the list code must be a unique identifier for the combination.  Creates records in:  OPD\_WAIT\_LIST  Optionally CLINIC\_WAITLIST\_GROUPS  Loaded via:   OASLOADOPDWAITLIST\_PACKAGE.load\_opdwaitlist  |
| ----- |

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADREF\_RECORD\_NU   
Mandatory field   
MBER   
Foreign key to LOAD\_REFERRALS.RECORD\_NUMBER 

| NUMBER | 42 |   RTTPWY\_RECNO\_OUT\_ENCOUNTER | Foreign key to load\_referral\_to\_treat\_pathways.RECORD\_NUMBER  Used to set referral\_to\_treat\_pathways.outcome\_encounter\_id to record that outcomming this encounter caused the pathway to be ended.  Can only be set if the encounter is outcommed and if the pathway is ended. |
| :---- | :---- | :---- | :---- |
| NUMBER | 42 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  LOADRTTPRD\_RECORD\_NUMBER | Foreign key to load\_referral\_to\_treat\_periods.RECORD\_NUMBER  Used to set referral\_to\_treat\_periods. start\_encounter\_id ,  start\_encounter\_type (if LOADRTTPRD\_ACTION is START or BOTH), stop\_encounter\_id , stop\_encounter\_type (if LOADRTTPRD\_ACTION is STOP or BOTH) to waiting list Id and encounter type. |

   
 

 

 

 48

| VARCHAR2 | 5 |
| :---- | :---- |

  LOADRTTPRD\_ACTION Type of RTT action this activity should be linked to. 

Only four accepted values: START for Start Clock, STOP for Stop Clock,  BOTH for both StartClock and StopClock, and NULL for no RTT action  

NUMBER 42 RTTEVENT\_RECNO\_ENC   
Foreign key to load\_referral\_to\_treat\_events.RECORD\_NUMBER  
OUNTER   
Used to set referral\_to\_treat\_events.encounter\_id to record that this    
encounter caused the event to be recorded. 

| NUMBER | 42 |
| :---- | :---- |

  RTTEVENT\_RECNO\_OUT   
Foreign key to load\_referral\_to\_treat\_events.RECORD\_NUMBER  
COME   
Used to set referral\_to\_treat\_events.outcome\_encounter\_id to record    
that the outcome of this encounter caused the event to be recorded. 

Only set if encounter is outcomed. 

VARCHAR2 10 SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

| VARCHAR2 | 100 |
| :---- | :---- |

  EXTERNAL\_SYSTEM\_ID Unique wait list id from the source system. 

VARCHAR2 80 MAIN\_CRN\_TYPE Main hospital number id type as loaded into  LOAD\_PMI.main\_crn\_type 

| VARCHAR2 | 30 |
| :---- | :---- |

  MAIN\_CRN Main hospital number as loaded into LOAD\_PMI.main\_crn

VARCHAR2 30 HOSPITAL\_CODE For use in multi-provider implementations to identify hospital  provider. 

Maps to: code type 10638 "Oasis Hospital Site Code For Dataload"  

Loaded as mapped into: CLINIC\_WAITLIST\_GROUPS.hospital\_id

e.g. Hospital Group 1, Hospital Group 2 

| VARCHAR2 | 80 |   SITE |  Hospital site within the hospital provider.  Maps to: code type 10454 "Site Codes"  Loaded as mapped into: CLINIC\_WAITLIST\_GROUPS.site\_codee.g. Site A in Hospital Group 1, Site B in Hospital Group 1 |
| :---- | :---- | :---- | :---- |
| VARCHAR2 | 10 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  LIST\_CODE |  Short code for the group.  Optionally Loaded into CLINIC\_WAITLIST\_GROUPS.user\_code if group generated from load data |

 49

| VARCHAR2 | 80 |
| :---- | :---- |

Otherwise if mapped then Maps to code type 10662 " CLINIC    
GROUPS TRANSLATIONS FOR DATALOAD " 

Loaded as mapped into:  

OPD\_WAIT\_LIST.clinic\_waitlist\_group\_id 

  LIST\_NAME Short description for the group. 

Optionally Loaded into: CLINIC\_WAITLIST\_GROUPS.description if  group generated from load data. 

VARCHAR2 1 ENCOUNTER\_TYPE Type of Encounter 

Must exist as a codes.user\_code of code type 34 " ENCOUNTER    
TYPES" 

\- Daycase. 

Loaded into: CLINIC\_WAITLIST\_GROUPS.encounter\_type,  

Opd\_wait\_list.encounter\_type,    
referral\_to\_treat\_periods.start\_encounter\_type/stop\_encounter\_type. 

| VARCHAR2 | 80 |
| :---- | :---- |

  SPECIALTY Maps to: code type 10025 "Specialty" Loaded as mapped into:  

CLINIC\_WAITLIST\_GROUPS.specialty\_code 

OPD\_WAIT\_LIST.specialty\_code 

VARCHAR2 1 NEW\_FOLLOWUP\_FLAG ~~N New or F~~ Follow-Up Only one New allowed per referral. 

| VARCHAR2 | 1 |
| :---- | :---- |

  SHORT\_NOTICE\_FLAG Only two accepted values: Y for Yes OR N for No Loaded into: OPD\_WAIT\_LIST.short\_notice\_flag 

VARCHAR2 1 STATUS Only the following values accepted: W for On List 

D for Suspended 

L for Appointment Booked 

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 50  
A for Completed 

C for Cancelled 

Loaded into: OPD\_WAIT\_LIST.status

| DATE | 10 |   TARGET\_DATE |  Must be in format: DD/MM/YYYY Loaded into: OPD\_WAIT\_LIST.target\_date If new\_followup\_flag is F then this field is mandatory. |
| :---- | :---- | :---- | :---- |

VARCHAR2 30 CONSULTANT Maps to: STAFF\_IDS.id\_number Loaded as mapped into: OPD\_WAIT\_LIST.consultant\_code 

| VARCHAR2 | 80 |
| :---- | :---- |

~~Note type \= "19784" \- "OPD Waitlist Notes"~~    
  OUTCOME Maps to: code type 10078 "Outpatient Waiting List Outcome" Loaded as mapped into: OPD\_WAIT\_LIST.outcome\_code e.g. Booked, Cancelled By Hospital, Cancelled By Patient 

DATE 10 DATE\_REMOVED Must be in format: DD/MM/YYYY Loaded into: OPD\_WAIT\_LIST.date\_removed 

| VARCHAR2 | 2000 |
| :---- | :---- |

  WL\_COMMENT Maps to: code type 297 "Multiple Note Types" 

Subject \= "OWL Notes" 

Loaded into: OASIS\_MULTIPLE\_NOTES.text 

VARCHAR2 80 IOS\_USERCODE Maps to ios\_master.ios via ios\_ids where  ios\_ids.id\_number=load\_opdwaitlist.ios\_usercode 

And ios\_ids.id\_type\_code \= code.code  

where codes.code\_type=10410 \- 

Loaded into opd\_wait\_list.ios 

| VARCHAR2 | 80 |   TRANSPORT\_REQUIRED |  ~~Deprecated~~ value from referral used instead.  Maps to: code type 10053 " TRANSPORT TYPES (PATIENT) "Loaded as mapped into:   OPD\_WAIT\_LIST.transport\_code |
| :---- | :---- | ----: | :---- |

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 51

| TABLE NAME: LOAD\_OPDWAITLISTDEF  Outpatient waiting list suspensions. All recorded suspensions must be loaded to ensure correct calculation of wait times.  Creates records in:  OPD\_WAIT\_DEFERRALS  Loaded via:   OASLOADOPDWAITLIST\_PACKAGE.load\_opdwaitlist  |
| :---- |

 52   
DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADOWL\_RECORD\_NU   
Foreign key to LOAD\_OPDWAITLIST.record\_number   
MBER 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique suspension id from the source system. 

| DATE | 10 |
| :---- | :---- |

  DEFERRAL\_START Must be in format: DD/MM/YYYY Loaded into: OPD\_WAIT\_DEFERRALS.start\_date 

DATE 10 DEFERRAL\_END Must be in format: DD/MM/YYYY Loaded into: OPD\_WAIT\_DEFERRALS.end\_date 

| VARCHAR2 | 80 |   DEFERRAL\_REASON | e.g. At Patient's Request, On Consultant's Instruction, Medically Unfit~~Note type \= " 63178" \- "PB Suspension Notes"~~  Maps to: code type 10054 "Waitlist Suspension Reasons" Loaded as mapped into:   OPD\_WAIT\_DEFERRALS.deferred\_reason\_code  |
| :---- | :---- | ----- | ----- |
| VARCHAR2 | 2000 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  DEFERRAL\_COMMENT |  Maps to: code type 297 "Multiple Note Types"    Subject \= "OWL Suspension Notes"  Loaded into: OASIS\_MULTIPLE\_NOTES.text |

OUTPATIEN T DATA   
~~To ensure correct calc~~ulation of wait times, all cancelled bookings must be loaded, or  

| If migrating Choose and Book appointments, all C\&B service and party ids must first have been loaded into Altera PAS.  TABLE NAME: LOAD\_OPD\_APPOINTMENTS  Outpatient bookings and attendances.    override\_waitreset\_date must be supplied.  Creates records in:  APPOINTMENT\_REFERRALS  APPOINTMENTS  PATIENT\_CARE\_EPISODES  Loaded via:   OASLOADOPD\_PACKAGE.load\_opd\_appointments |
| ----- |

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADREF\_RECORD\_N   
Mandatory field   
UMBER   
Foreign key to LOAD\_REFERRALS.RECORD\_NUMBER 

| NUMBER | 42 |
| :---- | :---- |

  LOADOWL\_RECORD\_N 

Foreign key to LOAD\_OPDWAITLIST.record\_number   
UMBER 

NUMBER 42 RTTPWY\_RECNO\_OUT\_   
Foreign key to load\_referral\_to\_treat\_pathways.RECORD\_NUMBER  
ENCOUNTER   
Used to set referral\_to\_treat\_pathways.outcome\_encounter\_id to    
record that outcomming this encounter caused the pathway to be    
ended. 

Can only be set if the encounter is outcommed and if the pathway is    
ended. 

 

| NUMBER | 42 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved~~.  LOADRTTPRD\_RECORD\_NUMBER | Foreign key to load\_referral\_to\_treat\_periods.RECORD\_NUMBER  Used to set referral\_to\_treat\_periods. start\_encounter\_id ,  start\_encounter\_type (if LOADRTTPRD\_ACTION is START or BOTH), stop\_encounter\_id , stop\_encounter\_type (if LOADRTTPRD\_ACTION is STOP or BOTH) to waiting list Id and encounter type. |
| :---- | :---- | ----- | ----- |
| VARCHAR2 | 5 |   LOADRTTPRD\_ACTION |  Type of RTT action this activity should be linked to. |

 53

| NUMBER | 42 |
| :---- | :---- |

Only four accepted values: START for Start Clock, STOP for Stop Clock,  BOTH for both StartClock and StopClock, and NULL for no RTT action  

  RTTEVENT\_RECNO\_EN   
Foreign key to load\_referral\_to\_treat\_events.RECORD\_NUMBER  
COUNTER   
Used to set referral\_to\_treat\_events.encounter\_id to record that this    
encounter caused the event to be recorded. 

NUMBER 42 RTTEVENT\_RECNO\_OU   
Foreign key to load\_referral\_to\_treat\_events.RECORD\_NUMBER  
TCOME   
Used to set referral\_to\_treat\_events.outcome\_encounter\_id to record    
that the outcome of this encounter caused the event to be recorded. 

Only set if encounter is outcomed. 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique booking id from the source system. 

| VARCHAR2 | 80 |
| :---- | :---- |

  MAIN\_CRN\_TYPE Main hospital number id type as loaded into  LOAD\_PMI.main\_crn\_type 

VARCHAR2 30 MAIN\_CRN Main hospital number as loaded into LOAD\_PMI.main\_crn

| VARCHAR2 | 1 |
| :---- | :---- |

  NEW\_FOLLOWUP\_FLA   
Only two accepted values: N for New OR F for Followup G   
Loaded into: APPOINTMENTS.new\_followup\_flag 

VARCHAR2 80 APPT\_TEAM Maps to: code type 10721 "Teams For Dataload Mapping" Mapped value must exist in: TEAMS.user\_code 

Loaded as mapped into: APPOINTMENTS.team\_id 

| DATE | 10 |
| :---- | :---- |

  APPT\_DATE Must be in format: DD/MM/YYYY HH24:MI Loaded into: APPOINTMENTS.start\_date   
© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 54  
DATE 10 BOOKED\_DATE Must be in format: DD/MM/YYYY Loaded into: APPOINTMENTS.date\_booked 

| VARCHAR2 | 80 |   BOOKING\_TYPE |  Maps to: code type 10581 "Outpatient Booking Types" Loaded as mapped into: APPOINTMENTS.booking\_typee.g. No Patient Choice, Partially Booked, Fully Booked |
| :---- | :---- | :---- | :---- |

~~system to the Altera PAS session and microsession.~~   
VARCHAR2 20 CLINIC\_CODE\_1 Short code from source system used for mapping to an AlteraPAS  microsession. This field is used in conjunction with CLINIC\_CODE\_2  

to provide a unique consultant session identifier from the source  

Maps to: session\_master.session\_code and    
session\_staff.session\_staff\_id 

| VARCHAR2 | 20 |
| :---- | :---- |

  CLINIC\_CODE\_2 Short code from source system used for mapping to Altera PAS  microsession. 

Maps to: session\_master.session\_code and    
session\_staff.session\_staff\_id 

VARCHAR2 20 APPT\_TYPE Short code from source system used for mapping the type of  appointment. 

Maps to: session\_staff\_ios.ios via ios\_ids linked to    
ios\_master.user\_code 

| VARCHAR2 | 30 |
| :---- | :---- |

~~e.g. Ambulance \- Wheelchair & Escort, Stretcher with Escort, Tall Lift~~  
  CONSULTANT\_IN\_CHA 

Maps to: STAFF\_IDS.id\_number   
RGE 

Loaded as mapped into: PATIENT\_CARE\_EPISODES.consultant\_code

Only used if value not already configured against appointment slot

VARCHAR2 30 CONSULTANT\_TAKING\_   
Maps to: STAFF\_IDS.id\_number   
APPT   
Loaded as mapped into: appointments.staff\_id  

| VARCHAR2 | 80 |
| :---- | :---- |

  TRANSPORT\_REQUIRE   
Maps to: code type 10053 "Transport Types"   
D   
Loaded as mapped into: APPOINTMENTS.transport\_code 

VARCHAR2 1 WALKIN\_FLAG Only two accepted values: Y for Yes OR N for No Loaded into: APPOINTMENTS.walkin\_flag 

| DATE | 10 |
| :---- | :---- |

  TIME\_ARRIVED Must be in format: DD/MM/YYYY HH24:MI Loaded into: APPOINTMENTS.time\_arrived 

DATE 10 TIME\_SEEN Must be in format: DD/MM/YYYY HH24:MI ~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserve~~d~~.~~ 55  
Loaded into: APPOINTMENTS.time\_seen

| DATE | 10 |   TIME\_COMPLETE |  Must be in format: DD/MM/YYYY HH24:MI  Loaded into: APPOINTMENTS.time\_complete |
| :---- | :---- | :---- | ----- |

VARCHAR2 80 OUTCOME Maps to codes, the code type is determined by the encounter type  defined for the clinic that the appointment is booked to: 

Encounter Type Description Code Type  

O Outpatient 21  

R Radiology 10237 

T Theatre 10238 

Y Day care 10239 

A Ward attender 10240 

U Community care 10380 

| DATE | 10 |
| :---- | :---- |

~~Note type \= "10233" \- "Clinic Appointment"~~    
 

| H |  Therapies |  10473 |
| :---- | ----: | :---- |

Loaded into: APPOINTMENTS.outcome\_code 

e.g. Added to IWL, Book FUP, DNA, Rescheduled By Hospital 

  CANCELLED\_DATE Must be in format: DD/MM/YYYY Loaded into: APPOINTMENTS.cancelled\_date 

VARCHAR2 2000 APPT\_COMMENT Maps to: code type 297 "Multiple Note Types" 

Subject \= "Appointment Notes" 

Loaded into: OASIS\_MULTIPLE\_NOTES.text 

| VARCHAR2 | 20 |
| :---- | :---- |

  CAB\_UBRN Choose and Book Unique Booking Reference Number Mandatory but only to be supplied for C\&B appointments. 

Loaded into: APPOINTMENTS.ebs\_ebsrn 

VARCHAR2 10 CAB\_SERVICE Choose and Book Care Service Mandatory but only to be supplied for C\&B appointments. 

Loaded into: CAB\_APPOINTMENT\_SERVICE.service\_id

| VARCHAR2 | 36 |   CAB\_USRN |  Choose and Book Unique Slot Reference Number  Mandatory but only to be supplied for C\&B appointments. Loaded into: OASIS\_GUIDS.guid\_id |
| :---- | :---- | :---- | ----- |

~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserve~~d~~.~~ 56

| TABLE NAME: LOAD\_OPD\_CODING Administrative coding of diagnoses and procedures for outpatient episodes of care.  Creates records in:  PATIENT\_DIAGNOSIS\_NOTES DIAGNOSIS\_CARE\_EPISODES  Loaded via:   OASLOADOPD\_PACKAGE.load\_opd\_appointments |
| :---- |

 57   
 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOAD\_OPD\_RECORD\_   
Foreign key to LOAD\_OPD\_APPOINTMENTS.record\_number   
NUMBER 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique coding id from the source system. 

| VARCHAR2 | 80 |
| :---- | :---- |

  DIAGNOSIS\_DIVISION ~~Maps to: code type 292~~ "Diagnosis Division" 

Loaded as mapped into:    
PATIENT\_DIAGNOSIS\_NOTES.diagnosis\_division e.g. Diagnoses, Procedures 

VARCHAR2 80 NOTE\_TYPE Maps to: code type 313 "Diagnosis Note Types" Loaded as mapped into: PATIENT\_DIAGNOSIS\_NOTES.note\_type

e.g. Primary, Secondary, Associated 

| VARCHAR2 | 25 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved~~.  DIAGNOSIS |  Maps to: DIAGNOSIS\_CODES.hosp\_code for ICD OR OPCS Loaded as mapped into: PATIENT\_DIAGNOSIS\_NOTES.diag\_codee.g. A00, A159, E22, G002 |
| :---- | :---- | :---- | :---- |
| VARCHAR2 | 200 |   DIAGNOSIS\_NOTE |  Free text diagnosis/procedure desription.  Loaded into: PATIENT\_DIAGNOSIS\_NOTES.diagnosis\_note |

| VARCHAR2C~~OMMU NIT~~Y DA TA | 30 |   DIAGNOSED\_BY |  Maps to: STAFF\_IDS.id\_number  Loaded as mapped into PATIENT\_DIAGNOSIS\_NOTES.staff\_id |
| ----- | :---- | :---- | ----- |
| DATE | 10 |   DIAGNOSIS\_DATECommunity care appointments. To ensure correct calculation of wait  |  Must be in format: DD/MM/YYYY  PATIENT\_DIAGNOSIS\_NOTES.date\_recorded |

 58 

| TABLE NAME: LOAD\_CMTY\_APPOINTMENTS  times, all cancelled bookings must be loaded or override\_waitreset\_date must be supplied.  Creates records in:  APPOINTMENT\_REFERRALS  APPOINTMENTS  PATIENT\_CARE\_EPISODES  Loaded via:   OASLOADCMTY\_PACKAGE.load\_cmty\_appointments  |
| :---- |

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADOWL\_RECORD\_N   
Foreign key to LOAD\_OPDWAITLIST.record\_number   
UMBER 

| NUMBER | 42 |
| :---- | :---- |

  LOADRTTPWY\_RECOR 

Foreign key to LOAD\_RTT\_PATHWAYS.record\_number   
D\_NUMBER 

NUMBER 42 LOADRTTPRD\_RECOR   
Foreign key to LOAD\_RTT\_PERIODS.record\_number  
D\_NUMBER 

| VARCHAR2 | 20 |   LOADRTTPRD\_ACTION |  Type of RTT action this activity should be linked to.  Only two accepted values: START for Start Clock, STOP for Stop Clock |
| :---- | :---- | ----- | ----- |
| VARCHAR2 | 10 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  SYSTEM\_CODE |  Unique identifier for the originating system.   Maps to: code type 10599 "Dataload System" |

| VARCHAR2 | 100 |
| :---- | :---- |

  EXTERNAL\_SYSTEM\_ID Unique booking id from the source system. 

VARCHAR2 80 MAIN\_CRN\_TYPE Main hospital number id type as loaded into  LOAD\_PMI.main\_crn\_type 

| VARCHAR2 | 30 |
| :---- | :---- |

  MAIN\_CRN Main hospital number as loaded into LOAD\_PMI.main\_crn

VARCHAR2 80 PATIENT\_CATEGORY Maps to: code type 10087 "Patient Contract Category" Loaded as mapped into:  

APPOINTMENT\_REFERRALS.patient\_category 

e.g. NHS, Private, Overseas Visitor 

| DATE | 10 |
| :---- | :---- |

  FIRST\_SEEN Must be in format: DD/MM/YYYY Loaded into: APPOINTMENT\_REFERRALS.patient\_firstseen\_date

DATE 10 OVERRIDE\_WAIT\_RESE   
Used for calculating waiting time if not loading cancelled bookings.   
T\_DATE   
Must be in format: DD/MM/YYYY 

Loaded into: APPOINTMENT\_REFERRALS.override\_waitreset\_date

| VARCHAR2 | 1 |
| :---- | :---- |

  REF\_NEW\_FOLLOWUP   
Only two accepted values: N for New OR F for Followup \_FLAG   
Loaded into: APPOINTMENT\_REFERRALS.new\_followup\_flag

DATE 10 REF\_DATE Must be in format: DD/MM/YYYY Loaded into:  

APPOINTMENT\_REFERRALS.ref\_date 

APPOINTMENTS.ref\_date 

| DATE | 10 |   REF\_RECEIVED\_DATE |  Must be in format: DD/MM/YYYY  Loaded into: APPOINTMENT\_REFERRALS.date\_received |
| :---- | :---- | :---- | ----- |
| VARCHAR2 | 80 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  REF\_SOURCE |  Maps to: code type 10107 "Inpatient Referral Source" Loaded as mapped into:   APPOINTMENT\_REFERRALS.ref\_source APPOINTMENTS.ref\_source  e.g. Consultant Within Trust, Dentist, GP, Midwife |

 59

| VARCHAR2 | 10 |
| :---- | :---- |

  REF\_GP\_CODE National General Practitioner Code of Referring GP Maps to: GP\_MASTER.registration\_code 

Loaded as mapped into:  

APPOINTMENT\_REFERRALS.ref\_gp 

e.g. C0000048 , D2008756, G3293160 

VARCHAR2 10 REF\_PRACTICE\_CODE National Practice Code for the Referring GP Maps to: GP\_PRACTICE\_MASTER.gp\_practice\_code 

Loaded as mapped into:  

APPOINTMENT\_REFERRALS.ref\_practice 

e.g. A81006, D82076, K81022 

| VARCHAR2 | 20 |
| :---- | :---- |

  REF\_PRACTICE\_POSTC 

Practice Post Code for the GP   
ODE 

Not loaded but used when mapping to distinguish between sub   
practices which may have the same National Practice Code. 

VARCHAR2 80 REF\_URGENCY Maps to: code type 10449 "Outpatient Waiting List Urgency" Loaded as mapped into: APPOINTMENT\_REFERRALS.ref\_urgency

e.g. Routine, Soon, Urgent 

| VARCHAR2 | 80 |
| :---- | :---- |

  REF\_TYPE Maps to: code type 10092 "Referral Type" Loaded as mapped into: APPOINTMENT\_REFERRALS.ref\_type

e.g. Critical, Rapid Access, Standard 

VARCHAR2 80 REF\_REASON Maps to: code type 10093 "Outpatient Referral Reason" Loaded as mapped into: APPOINTMENT\_REFERRALS.ref\_reason

e.g. Advice/Consultation, Specific Procedure 

| VARCHAR2 | 80 |
| :---- | :---- |

  REF\_SPECIALTY Maps to: code type 10025 "Specialty" Loaded as mapped into: APPOINTMENT\_REFERRALS.specialty\_code

VARCHAR2 80 REF\_TEAM Maps to: code type 10721 "Teams For Dataload Mapping" ~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserve~~d~~.~~ 60  
Mapped value must exist in: TEAMS.user\_code 

Loaded as mapped into: APPOINTMENT\_REFERRALS.team\_id

| VARCHAR2 | 30 |   REF\_CONSULTANT |  Maps to: STAFF\_IDS.id\_number  Loaded as mapped into:   APPOINTMENT\_REFERRALS.consultant\_code |
| :---- | :---- | :---- | :---- |

VARCHAR2 80 REF\_OUTCOME Maps to: code type 10728 "Appointment Referral Outcome Codes" Loaded as mapped into: APPOINTMENT\_REFERRALS.outcome\_code

e.g. Rejected, Treatment Complete 

| DATE | 10 |
| :---- | :---- |

  REF\_DISCHARGE\_DAT 

Must be in format: DD/MM/YYYY   
E   
Loaded into: APPOINTMENT\_REFERRALS.discharged\_date 

DATE 10 APPT\_DATE Must be in format: DD/MM/YYYY HH24:MI Loaded into: APPOINTMENTS.start\_date 

| DATE | 10 |
| :---- | :---- |

~~system to the Altera PAS session and microsession.~~   
  BOOKED\_DATE Must be in format: DD/MM/YYYY Loaded into: APPOINTMENTS.date\_booked 

VARCHAR2 80 BOOKING\_TYPE Maps to: code type 10581 "Outpatient Booking Types" Loaded as mapped into: APPOINTMENTS.booking\_type 

e.g. No Patient Choice, Partially Booked, Fully Booked 

| VARCHAR2 | 20 |
| :---- | :---- |

  CLINIC\_CODE\_1 Short code from source system used for mapping to an AlteraPAS  microsession. This field is used in conjunction with CLINIC\_CODE\_2  to provide a unique consultant session identifier from the source  

Maps to: session\_master.session\_code and    
session\_staff.session\_staff\_id 

VARCHAR2 20 CLINIC\_CODE\_2 Short code from source system used for mapping to Altera PAS  microsession. 

Maps to: session\_master.session\_code and    
session\_staff.session\_staff\_id 

| VARCHAR2 | 20 |
| :---- | :---- |

~~e.g. Ambulance \- Wheelchair & Escort, Stretcher with Escort, Tall Lift~~  
  APPT\_TYPE Short code from source system used for mapping the type of  appointment. 

Maps to: session\_staff\_ios.ios via ios\_master.user\_code 

VARCHAR2 30 CONSULTANT\_CODE Maps to: STAFF\_IDS.id\_number 

~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserve~~d~~.~~ 61  
Loaded as mapped into: PATIENT\_CARE\_EPISODES.consultant\_id 

| VARCHAR2 | 80 |   TRANSPORT\_REQUIRED | Maps to: code type 10053 "Transport Types"   Loaded as mapped into: APPOINTMENTS.transport\_code |
| :---- | :---- | :---- | :---- |

VARCHAR2 1 WALKIN\_FLAG Only two accepted values: Y for Yes OR N for No Loaded into: APPOINTMENTS.walkin\_flag 

| DATE | 10 |
| :---- | :---- |

  TIME\_ARRIVED Must be in format: DD/MM/YYYY HH24:MI Loaded into: APPOINTMENTS.time\_arrived 

DATE 10 TIME\_SEEN Must be in format: DD/MM/YYYY HH24:MI Loaded into: APPOINTMENTS.time\_seen 

| DATE | 10 |
| :---- | :---- |

  TIME\_COMPLETE Must be in format: DD/MM/YYYY HH24:MI Loaded into: APPOINTMENTS.time\_complete   
~~Note type \= "101" \- "Appointment Referral Notes"~~   
VARCHAR2 80 OUTCOME Maps to: code type 10380 "Community Care Outcome Codes" Loaded into: APPOINTMENTS.outcome\_code 

e.g. Another appointment given, Discharged from consultant's care

| DATE | 10 |
| :---- | :---- |

~~Note type \= "10233" \- "Clinic Appointment"~~   
  CANCELLED\_DATE Must be in format: DD/MM/YYYY Loaded into: APPOINTMENTS.cancelled\_date 

VARCHAR2 2000 REF\_COMMENT Maps to: code type 297 "Multiple Note Types" 

Subject \= "Appointment Referral Notes" 

Loaded into: OASIS\_MULTIPLE\_NOTES.text 

| VARCHAR2 | 2000 |   APPT\_COMMENT |  Maps to: code type 297 "Multiple Note Types"    Subject \= "Appointment Notes"  Loaded into: OASIS\_MULTIPLE\_NOTES.text |
| :---- | :---- | :---- | ----- |

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 62  
I MPA T IENT WAITING LIST DA TA 

| TABLE NAME: LOAD\_IWL\_PROFILES  Treatment profiles for the inpatient waiting list. These will link to individual waiting list entries to provide a standard profile of treatment.  Creates records in:  TREATMENT\_MASTER  TREATMENT\_STAFF  Loaded via:   OASLOADIWL\_PACKAGE.load\_iwl\_profiles |
| :---- |

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

VARCHAR2 10 SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

| VARCHAR2 | 100 |
| :---- | :---- |

  EXTERNAL\_SYSTEM\_ID Unique profile id from the source system. 

VARCHAR2 15 WAITLIST\_PROFILE Short code for the profile. 

Loaded into: TREATMENT\_MASTER.user\_code 

| VARCHAR2 | 40 |
| :---- | :---- |

  DESCRIPTION Short profile description. 

Loaded into: TREATMENT\_MASTER.description 

VARCHAR2 2 LIST\_NO Consultant list number. 

Loaded into: TREATMENT\_STAFF.list\_no 

| VARCHAR2 | 30 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved~~.  CONSULTANT\_CODE |  Consultant using this profile.  Maps to: STAFF\_IDS.id\_number  Loaded as mapped into: TREATMENT\_STAFF.staff\_id |
| :---- | :---- | :---- | :---- |
| VARCHAR2 | 1 |   TREATMENT\_TYPE |  Type of profile.  Only three accepted values: D for Diagnosis, P for Procedure, O for Other |

 

 63

Loaded into: TREATMENT\_MASTER.treatment\_type 

| VARCHAR2 | 1 |
| :---- | :---- |

  ADMIT\_TYPE Type of admission. 

Only two accepted values: I for Inpatient, D for Day case 

Loaded into: TREATMENT\_MASTER.admit\_type 

NUMBER 42 MAX\_WAIT\_MONTHS For this profile: maximum wait time in months. Loaded into: TREATMENT\_MASTER.max\_wait\_months 

| NUMBER | 42 |
| :---- | :---- |

  AVG\_LENGTH\_STAY For this profile: average length of hospital stay in days. 

Loaded into: TREATMENT\_MASTER.avg\_length\_stay 

NUMBER 42 ADMIT\_DURATION\_HO   
For this profile and consultant: expected admission duration \- in  

URS   
hours. 

Loaded into: TREATMENT\_STAFF.admit\_duration\_hours 

| NUMBER | 42 |   OPERATION\_DURATIO N\_MINS | For this profile and consultant: expected operation duration \- in minutes.    Loaded into: TREATMENT\_STAFF.operation\_duration\_mins |
| :---- | :---- | ----- | :---- |

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 64

| TABLE NAME: LOAD\_IWL Inpatient waiting list entries.  Creates records in:  APPOINTMENT\_REFERRALS TREATMENT\_WAIT\_LIST Loaded via:   OASLOADIWL\_PACKAGE.load\_iwl |
| :---- |

 65   
 

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADREF\_RECORD\_N   
Mandatory field 

UMBER   
Foreign key to LOAD\_REFERRALS.RECORD\_NUMBER 

| NUMBER | 42 |
| :---- | :---- |

  RTTPWY\_RECNO\_OUT\_   
Foreign key to load\_referral\_to\_treat\_pathways.RECORD\_NUMBER

ENCOUNTER   
Used to set referral\_to\_treat\_pathways.outcome\_encounter\_id to  

record that outcomming this encounter caused the pathway to be  

ended. 

Can only be set if the encounter is outcommed and if the pathway is  

ended. 

 

   
NUMBER 42 LOADRTTPRD\_RECOR 

Foreign key to load\_referral\_to\_treat\_periods.RECORD\_NUMBER

D\_NUMBER 

Used to set referral\_to\_treat\_periods. start\_encounter\_id ,  

start\_encounter\_type (if LOADRTTPRD\_ACTION is START or BOTH),  

stop\_encounter\_id , stop\_encounter\_type (if LOADRTTPRD\_ACTION  

is STOP or BOTH) to waiting list Id and encounter type. 

| VARCHAR2 | 5 |   LOADRTTPRD\_ACTION |  Type of RTT action this activity should be linked to.  Only four accepted values: START for Start Clock, STOP for Stop Clock, BOTH for both StartClock and StopClock, and NULL for no RTT action  |
| :---- | :---- | ----- | ----- |
| NUMBER | 42 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  RTTEVENT\_RECNO\_ENCOUNTER | Foreign key to load\_referral\_to\_treat\_events.RECORD\_NUMBER  Used to set referral\_to\_treat\_events.encounter\_id to record that this encounter caused the event to be recorded. |

| NUMBER | 42 |
| :---- | :---- |

  RTTEVENT\_RECNO\_OU   
Foreign key to load\_referral\_to\_treat\_events.RECORD\_NUMBER

TCOME   
Used to set referral\_to\_treat\_events.outcome\_encounter\_id to record  

that the outcome of this encounter caused the event to be recorded. 

Only set if encounter is outcomed. 

VARCHAR2 10 SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

| VARCHAR2 | 100 |
| :---- | :---- |

  EXTERNAL\_SYSTEM\_ID Unique wait list id from the source system. 

VARCHAR2 80 MAIN\_CRN\_TYPE Main hospital number id type as loaded into  LOAD\_PMI.main\_crn\_type 

| VARCHAR2 | 30 |
| :---- | :---- |

  MAIN\_CRN Main hospital number as loaded into LOAD\_PMI.main\_crn

DATE 10 WAITLIST\_DATE Must be in format: DD/MM/YYYY Loaded into: TREATMENT\_WAIT\_LIST.date\_added\_to\_list 

| VARCHAR2 | 80 |
| :---- | :---- |

  URGENCY Maps to: code type 25 "Treatment Waiting List Urgency" Loaded as mapped into: TREATMENT\_WAIT\_LIST.urgency e.g. Routine, Soon, Urgent 

VARCHAR2 1 SHORT\_NOTICE\_FLAG Only two accepted values: Y for Yes OR N for No Loaded into: TREATMENT\_WAIT\_LIST.short\_notice\_flag

| VARCHAR2 | 1 |   STATUS © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. |  Only the following values accepted:  W for Waiting  D for Suspended  L for Planned Admit  A for Admitted  N for Admitted Not Treated  C for Cancelled  Loaded into: TREATMENT\_WAIT\_LIST.status |
| :---- | :---- | :---- | :---- |

 66

VARCHAR2 80 WAITLIST\_TYPE Maps to: code type 10036 "Waitlist Type" Loaded as mapped into: TREATMENT\_WAIT\_LIST.waitlist\_type

e.g. Fully Booked, Partially Booked, Deferred 

| VARCHAR2 | 15 |
| :---- | :---- |

  WAITLIST\_PROFILE Short code as previously loaded into  LOAD\_IWL\_PROFILES.waitlist\_profile 

Maps to: TREATMENT\_MASTER.user\_code 

Loaded as mapped into: TREATMENT\_WAIT\_LIST.treatment\_code

VARCHAR2 80 SITE\_CODE Hospital site within the hospital provider. Maps to: code type 10454 "Site Codes" 

Loaded as mapped into: TREATMENT\_WAIT\_LIST.site\_code 

e.g. Site A in Hospital Group 1, Site B in Hospital Group 1 

| VARCHAR2 | 80 |
| :---- | :---- |

  SPECIALTY Maps to: code type 10025 "Specialty" Loaded as mapped into: TREATMENT\_WAIT\_LIST.specialty\_code

VARCHAR2 30 CONSULTANT\_CODE Maps to: STAFF\_IDS.id\_number Loaded as mapped into: TREATMENT\_WAIT\_LIST.transport\_required~~e.g. Ambulance \- Wheelchair & Escort, Stretcher with Escort, Tall Lift~~  
Loaded as mapped into: TREATMENT\_WAIT\_LIST.consultant\_id

| VARCHAR2 | 80 |
| :---- | :---- |

  INTENDED\_MANAGEM 

Maps to: code type 10033 "Patient Management Codes" 

ENT   
Loaded as mapped into: TREATMENT\_WAIT\_LIST.management\_codee.g. Inpatient, Day case 

VARCHAR2 80 TRANSPORT\_REQUIRE   
Maps to: code type 10053 "Transport Types" 

D 

| VARCHAR2 | 80 |
| :---- | :---- |

  PROVISIONAL\_DIAGNO Free text preliminary diagnosis.   
SIS   
Loaded into: TREATMENT\_WAIT\_LIST.prov\_diagnosis   
© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 67  
VARCHAR2 200 PROVISIONAL\_PROCE   
Free text preliminary procedure. 

DURE   
Loaded into: TREATMENT\_WAIT\_LIST.prov\_procedure

| VARCHAR2 | 25 |   INTENDED\_PROCEDU RE\_CODE | Maps to: DIAGNOSIS\_CODES.hosp\_code for OPCS   |
| :---- | :---- | ----- | :---- |

|  |  |
| :---- | :---- |

Loaded as mapped into:  

TREATMENT\_WAIT\_LIST.intended\_procedure\_code e.g. A09, E402, F164, H13 

VARCHAR2 25 INTENDED\_PROCEDU   
Maps to: DIAGNOSIS\_CODES.hosp\_code for OPCS 

RE\_CODE2   
Loaded as mapped into:  

TREATMENT\_WAIT\_LIST.intended\_procedure\_code2 

e.g. A09, E402, F164, H13 

| NUMBER | 42 |
| :---- | :---- |

  EST\_THEATRE\_TIME For this entry: expected operation duration \- in minutes. Overrides  profile. 

TREATMENT\_WAITLIST.operation\_duration\_mins 

NUMBER 42 ADMISSION\_DURATIO   
For this entry: expected admission duration \- in hours. Overrides    
~~e.g. Remain On List, Removed \- Patient Request, Removed \- No~~    
N   
profile. 

TREATMENT\_WAITLIST.admit\_duration\_hours 

| DATE | 10 |
| :---- | :---- |

  LAST\_REVIEW\_DATE Must be in format: DD/MM/YYYY Loaded into: TREATMENT\_WAIT\_LIST.reviewed\_date 

VARCHAR2 80 LAST\_REVIEW\_RESPO   
Maps to: code type 10156 " Waiting List Review Outcomes" 

NSE   
Loaded into: TREATMENT\_WAIT\_LIST.review\_outcome 

Response 

| VARCHAR2 | 80 |
| :---- | :---- |

  WL\_OUTCOME Maps to: code type 10064 " Waitlist Outcome Codes" ~~Note type \= "61188" \- "General Treatment Waitlist Note"~~  
Loaded into: TREATMENT\_WAIT\_LIST.outcome\_code 

e.g. Admitted As Planned, Removed Not Treated, Treated As An  

Emergency 

DATE 10 DATE\_REMOVED Must be in format: DD/MM/YYYY Loaded into: TREATMENT\_WAIT\_LIST.date\_removed 

| VARCHAR2 | 2000 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved~~.  WL\_ENTRY\_COMMENT |  Maps to: code type 297 "Multiple Note Types"    Subject \= "TWL Notes"  Loaded into: OASIS\_MULTIPLE\_NOTES.text |
| :---- | :---- | :---- | ----- |

 68  
Note type \= "50" \- "Treatment Waiting List Notes (Ward Notes)"   
Note type \= "50" \- " Trea~~tm~~ent Waiting List Notes (Ward Notes)"   
VARCHAR2 2000 ADMISSION\_REASON\_   
Maps to: code type 297 "Multiple Note Types" 

COMMENT 

Subject \= "TWL Admission Notes" 

Loaded into: OASIS\_MULTIPLE\_NOTES.text 

| VARCHAR2 | 2000 |   OPERATION\_TEXT |  Maps to: code type 297 "Multiple Note Types"  Subject \= "TWL Operation Notes"  Loaded into: OASIS\_MULTIPLE\_NOTES.text |
| :---- | :---- | :---- | ----- |

| TABLE NAME: LOAD\_IWL\_DEFERRALS  Inpatient waiting list suspensions. All recorded  suspensions must be loaded to ensure correct calculation of wait times.  Creates records in:  WAIT\_LIST\_DEFERRALS  Loaded via:   OASLOADIWL\_PACKAGE.load\_iwl\_deferrals |
| ----- |

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADIWL\_RECORD\_N   
Foreign key to LOAD\_IWL.record\_number 

UMBER 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.    
© ~~2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 69  
Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique suspension id from the source system.

| DATE | 10 |   DEFERRAL\_START |  Must be in format: DD/MM/YYYY  Loaded into: WAIT\_LIST\_DEFERRALS.deferred\_date |
| :---- | :---- | :---- | ----- |

DATE 10 DEFERRAL\_END Must be in format: DD/MM/YYYY Loaded into: WAIT\_LIST\_DEFERRALS.deferred\_end 

| VARCHAR2 | 80 |   DEFERRAL\_REASON | e.g. At Patient's Request, On Consultant's Instruction, Medically Unfit~~Note type \= " 63183" \- "TWL Suspension Notes"~~  Maps to: code type 10054 "Waitlist Suspension Reasons" Loaded as mapped into:   WAIT\_LIST\_DEFERRALS.deferred\_reason\_code  |
| :---- | :---- | ----- | ----- |
| VARCHAR2 | 2000 |   DEFERRAL\_COMMENT |  Maps to: code type 297 "Multiple Note Types"    Subject \= "TWL Suspension Notes"  Loaded into: OASIS\_MULTIPLE\_NOTES.text |

 

| TABLE NAME: LOAD\_IWL\_TCIS  Inpatient waiting list planned admissions. All cancelled TCIs must be loaded to ensure correct calculation of wait times. Creates records in:  PLANNED\_ADMIT  Loaded via:   OASLOADIWL\_PACKAGE.load\_iwl\_tcis |
| :---- |

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADIWL\_RECORD\_N   
Foreign key to LOAD\_IWL.record\_number

UMBER 

| VARCHAR2 | 10 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved~~.  SYSTEM\_CODE |  Unique identifier for the originating system.   Maps to: code type 10599 "Dataload System" |
| :---- | :---- | ----- | ----- |
| VARCHAR2 | 100 |   EXTERNAL\_SYSTEM\_ID |  Unique suspension id from the source system. |

 70

| VARCHAR2 | 1 |
| :---- | :---- |

  STATUS Only the following values accepted: 

L for Planned Admit 

A for Admitted 

N for Admitted Not Treated 

C for Cancelled 

Loaded as mapped into: TREATMENT\_WAIT\_LIST.status 

VARCHAR2 80 BOOKING\_TYPE Maps to: code type 10582 "Inpatient Booking Types" Loaded as mapped into: TREATMENT\_WAIT\_LIST.booking\_type

e.g. No Patient Choice, Partially Booked, Fully Booked 

| VARCHAR2 | 30 |
| :---- | :---- |

  CONSULTANT\_CODE Maps to: STAFF\_IDS.id\_number Loaded as mapped into: PLANNED\_ADMIT.consultant\_code

DATE 10 OFFER\_DATE Must be in format: DD/MM/YYYY Loaded into: PLANNED\_ADMIT.offer\_date 

| DATE | 10 |
| :---- | :---- |

  AGREED\_DATE Must be in format: DD/MM/YYYY Loaded into: PLANNED\_ADMIT.agreed\_date 

VARCHAR2 1 AGREED\_FLAG Only two accepted values: Y for Yes OR N for No Loaded into: PLANNED\_ADMIT.agreed\_flag 

| DATE | 10 |
| :---- | :---- |

  PREASSESSMENT\_DAT 

Must be in format: DD/MM/YYYY HH24:MI 

E   
Loaded into: PLANNED\_ADMIT.preop\_date 

DATE 10 TCI\_DATE Must be in format: DD/MM/YYYY HH24:MI Loaded into: PLANNED\_ADMIT.planned\_admit\_date

| DATE | 10 | © 2026 Altera Digital Health Inc. and/or ~~its subsidiaries. All rights reserved~~.  OPERATION\_DATE |  Must be in format: DD/MM/YYYY HH24:MI  Loaded into: PLANNED\_ADMIT.operation\_date |
| :---- | :---- | :---- | ----- |
| DATE | 10 |   ESTIMATED\_DISCHARGE\_DATE | Must be in format: DD/MM/YYYY HH24:MI    Loaded into: PLANNED\_ADMIT.est\_discharge\_date |

 71

| VARCHAR2 | 80 |
| :---- | :---- |

  WARD Maps to: code type 10591 "Ward Translations For Dataload" Mapped value must exist in: WORK\_ENTITY\_DATA.work\_entity\_code

Loaded as mapped into: PLANNED\_ADMIT.work\_entity 

I NPATIENT DATA   
VARCHAR2 80 TCI\_OUTCOME Maps to: code type 10065 "Planned Admit Outcome Codes" Loaded as mapped into: PLANNED\_ADMIT.outcome\_code 

e.g. Admitted, Cancelled By Hospital, Cancelled By Patient 

| DATE | 10 |   CANCELLED\_DATE |  Must be in format: DD/MM/YYYY  Loaded into: PLANNED\_ADMIT.cancelled\_date |
| :---- | :---- | :---- | ----- |

| TABLE NAME: LOAD\_ADT\_ADMISSIONSPatient admission details.  Creates records in:  PATIENT\_AD Loaded via:   OASLOADADT\_PACKAGE.load\_adt |
| :---- |

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 LOADIWL\_RECORD\_N   
Foreign key to LOAD\_IWL.record\_number 

UMBER 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.    
© ~~2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.~~ 72  
Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique admission id from the source system.

| VARCHAR2 | 80 |   MAIN\_CRN\_TYPE |  Main hospital number id type as loaded into   LOAD\_PMI.main\_crn\_type |
| :---- | :---- | :---- | ----- |

VARCHAR2 30 MAIN\_CRN Main hospital number as loaded into LOAD\_PMI.main\_crn

| VARCHAR2 | 10 |
| :---- | :---- |

  REF\_GP\_CODE National General Practitioner Code of Referring GP Maps to: GP\_MASTER.registration\_code 

Loaded as mapped into: PATIENT\_AD.referring\_gp\_id e.g. C0000048 , D2008756, G3293160 

VARCHAR2 10 REF\_PRACTICE\_CODE National Practice Code for the Referring GP Maps to: GP\_PRACTICE\_MASTER.gp\_practice\_code 

Loaded as mapped into: PATIENT\_AD.referring\_practice\_id

e.g. A81006, D82076, K81022 

| VARCHAR2 | 20 |
| :---- | :---- |

  REF\_PRACTICE\_POSTC 

Practice Post Code for the GP 

ODE 

Not loaded but used when mapping to distinguish between sub 

practices which may have the same National Practice Code. 

VARCHAR2 80 INTENDED\_MANAGEM   
Maps to: code type 10033 "Patient Management Codes" 

ENT   
Loaded as mapped into: PATIENT\_AD.intended\_management e.g. Inpatient, Day case 

| DATE | 10 |
| :---- | :---- |

  WL\_DATE Must be in format: DD/MM/YYYY PATIENT\_AD.date\_added\_to\_waitlist 

DATE 10 ADMIT\_DATE Must be in format: DD/MM/YYYY HH24:MI PATIENT\_AD.admit\_date 

| DATE | 10 |   ESTIMATED\_DISCHARGE\_DATE | Must be in format: DD/MM/YYYY HH24:MI    If not currently held in source system, recommend loading  admit\_date \+ 1\.  PATIENT\_AD.est\_discharge\_date |
| :---- | :---- | :---- | ----- |
| VARCHAR2 | 80 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  ADMISSION\_TYPE |  Admission Method  Maps to: code type 10045 "Admission Type" Loaded as mapped into: PATIENT\_AD.admission\_type e.g. Elective Waiting List, Emergency GP, Maternity Ante-partum |

 73

| VARCHAR2 | 80 |
| :---- | :---- |

  ADMIT\_FROM Source of Admission Maps to: code type 10037 "Institution Type" 

Loaded as mapped into: PATIENT\_AD.admit\_from

e.g. LA Foster Care, Penal Establishment, Usual Place of Residence

VARCHAR2 30 ADMITTED\_BY Maps to: STAFF\_IDS.id\_number Loaded as mapped into: PATIENT\_AD.admitted\_by 

| DATE | 10 |
| :---- | :---- |

  DISCHARGE\_DATE Must be in format: DD/MM/YYYY HH24:MI PATIENT\_AD.physical\_discharge\_date 

VARCHAR2 80 DISCHARGE\_TYPE Discharge Method Maps to: code type 10046 "Discharge Type" 

Loaded as mapped into: PATIENT\_AD.discharge\_type 

e.g. Discharged To Mental Welfare, Patient Died, Regular Discharge

| VARCHAR2 | 80 |
| :---- | :---- |

  DISCHARGE\_TO Discharge Destination 

Maps to: code type 10106 "Discharge To" 

Loaded as mapped into: PATIENT\_AD.discharge\_to 

e.g. Court, NHS Run Care Home, Temporary Residence 

VARCHAR2 30 DISCHARGED\_BY Maps to: STAFF\_IDS.id\_number Loaded as mapped into: PATIENT\_AD.discharged\_by\_staff\_id

| VARCHAR2 | 80 |   ADMISSION\_OUTCOME |  ~~Maps to: code type 10~~ "Inpatient Outcome Codes"  Loaded as mapped into: PATIENT\_AD.outcome\_code e.g. Patient Died, Normal Discharge, Transferred |
| :---- | :---- | ----: | ----- |

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 74

| TABLE NAME: LOAD\_ADT\_EPISODES  Episodes of care. Blank end\_date indicates patient in hospital, current episode.   Validation:   All episode dates must fall within admission and discharge dates.  The first episode start\_date must equal admit\_date and the last episode end\_date must equal  discharge\_date.  The start\_date of one episode must equal the end\_date of the previous episode.   Creates records in:  PATIENT\_CARE\_EPISODES  PATIENT\_EPISODES  PATIENT\_ELIGIBILITY  Loaded via:   OASLOADADT\_PACKAGE.load\_adt |
| :---- |

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 ADT\_ADM\_RECORD\_N   
Foreign key to LOAD\_ADT.record\_number 

UMBER 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique episode id from the source system.

| VARCHAR2 | 80 |   PATIENT\_CATEGORY |  Maps to: code type 10087 "Patient Contract Category"  Loaded as mapped into: PATIENT\_CARE\_EPISODES.patient\_categorye.g. NHS, Private, Overseas Visitor |
| :---- | :---- | ----- | ----- |
| VARCHAR2 | 80 | © 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved.  ACTUAL\_MANAGEMENT | Maps to: code type 10033 "Patient Management Codes"  Loaded as mapped into:   PATIENT\_CARE\_EPISODES.management\_code e.g. Inpatient, Day case |

 75

| VARCHAR2 | 80 |
| :---- | :---- |

  SPECIALTY Maps to: code type 10025 "Specialty" Loaded as mapped into: PATIENT\_CARE\_EPISODES.specialty\_code

VARCHAR2 30 CONSULTANT\_CODE Maps to: STAFF\_IDS.id\_number Loaded as mapped into: PATIENT\_CARE\_EPISODES.consultant\_code 

| DATE | 10 |   START\_DATE |  Must be in format: DD/MM/YYYY HH24:MI  PATIENT\_CARE\_EPISODES.start\_date |
| :---- | :---- | :---- | :---- |
| DATE | 10 |   END\_DATE |  Must be in format: DD/MM/YYYY HH24:MI  PATIENT\_CARE\_EPISODES.end\_date |

| TABLE NAME: LOAD\_ADT\_WARDSTAYS Ward/bed transfers. Blank end\_date indicates patient in hospital, current location.  Creates records in:  BED\_DETAILS  Loaded via:   OASLOADADT\_PACKAGE.load\_adt |
| :---- |

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 ADT\_EPS\_RECORD\_NU   
Foreign key to LOAD\_ADT\_EPISODES.record\_number 

MBER 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.    
© ~~2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserve~~d~~.~~ 76  
Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique transfer id from the source system. 

| VARCHAR2 | 80 |   TEAM |  Maps to: code type 10721 "Teams For Dataload Mapping" Mapped value must exist in: TEAMS.user\_code |
| :---- | :---- | :---- | ----- |

|  |  |
| :---- | :---- |

Loaded as mapped into: BED\_DETAILS.team\_firm

VARCHAR2 80 WARD Maps to: code type 10591 "Ward Translations For Dataload" Mapped value must exist in: WORK\_ENTITY\_DATA.work\_entity\_code

Loaded as mapped into: BED\_DETAILS.work\_entity 

| VARCHAR2 | 1 |
| :---- | :---- |

  BED\_SEX Only three accepted values: M for Male, F for Female, U for Unknown

VARCHAR2 15 BED\_LOCATION Short code for bed location. 

| VARCHAR2 | 1 |
| :---- | :---- |

  IS\_HOME\_STAY Only two accepted values: Y for Yes OR N for No Maps to: code type 8 "Bed Status" 

Loaded as mapped into: BED\_DETAILS.bed\_status 

VARCHAR2 1 IS\_AWOL Only two accepted values: Y for Yes OR N for No Maps to: code type 8 "Bed Status" 

Loaded as mapped into: BED\_DETAILS.bed\_status 

| VARCHAR2 | 80 |
| :---- | :---- |

  LEAVE\_LOCATION\_CO 

Maps to: code type 10698 "On Pass Leave Location" 

DE 

Loaded as mapped into: BED\_DETAILS.leave\_location\_code

e.g. Home, NOK 

VARCHAR2 80 TRANSFER\_REASON Maps to: code type 10699 "Patient Transfer Reason Code" Loaded as mapped into: BED\_DETAILS.leave\_location\_code

e.g. Patient Status Change, Ward Full

| DATE | 10 |   START\_DATE |  Must be in format: DD/MM/YYYY HH24:MI  BED\_DETAILS.start\_date |
| :---- | :---- | :---- | :---- |
| DATE | 10 |   END\_DATE |  Must be in format: DD/MM/YYYY HH24:MI  BED\_DETAILS.end\_date |

~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserve~~d~~.~~ 77

| TABLE NAME: LOAD\_ADT\_CODING Administrative coding of diagnoses and procedures for inpatient episodes of care.  Creates records in:  PATIENT\_DIAGNOSIS\_NOTES DIAGNOSIS\_CARE\_EPISODES  Loaded via:   OASLOADADT\_PACKAGE.load\_adt |
| :---- |

~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserve~~d~~.~~ 78   
 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 ADT\_EPS\_RECORD\_NU   
Foreign key to LOAD\_ADT\_EPISODES.record\_number 

MBER 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique coding id from the source system. 

| VARCHAR2 | 80 |
| :---- | :---- |

  DIAGNOSIS\_DIVISION ~~Maps to: code type 292~~ "Diagnosis Division" 

Loaded as mapped into:  

PATIENT\_DIAGNOSIS\_NOTES.diagnosis\_division e.g. Diagnoses, Procedures 

VARCHAR2 80 NOTE\_TYPE Maps to: code type 313 "Diagnosis Note Types" Loaded as mapped into: PATIENT\_DIAGNOSIS\_NOTES.note\_type

e.g. Primary, Secondary, Associated 

| VARCHAR2 | 25 |   DIAGNOSIS |  Maps to: DIAGNOSIS\_CODES.hosp\_code for ICD OR OPCS Loaded as mapped into: PATIENT\_DIAGNOSIS\_NOTES.diag\_codee.g. A00, A159, E22, G002 |
| :---- | :---- | :---- | :---- |

VARCHAR2 200 DIAGNOSIS\_NOTE Free text diagnosis/procedure desription. Loaded into: PATIENT\_DIAGNOSIS\_NOTES.diagnosis\_note 

| VARCHAR2 | 30 |   DIAGNOSED\_BY |  Maps to: STAFF\_IDS.id\_number  Loaded as mapped into PATIENT\_DIAGNOSIS\_NOTES.staff\_id |
| ----- | :---- | :---- | ----- |
| DATEMENTAL HEALT H DATA | 10 |   DIAGNOSIS\_DATE |  Must be in format: DD/MM/YYYY  PATIENT\_DIAGNOSIS\_NOTES.date\_recorded |

 

| TABLE NAME: LOAD\_MH\_DETENTION\_MASTERPatient detention details.  Creates records in:  PATIENT\_DETENTION\_MASTER Loaded via:   OASLOADMH\_PACKAGE.load\_detentions |
| :---- |

 

 

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 ADT\_ADM\_RECORD\_N   
Foreign key to LOAD\_ADT.record\_number 

UMBER 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserved. 79  
VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique admission id from the source system.

| VARCHAR2 | 80 |   MAIN\_CRN\_TYPE |  Main hospital number id type as loaded into   LOAD\_PMI.main\_crn\_type |
| :---- | :---- | :---- | ----- |
| VARCHAR2 | 30 |   MAIN\_CRN |  Main hospital number as loaded into LOAD\_PMI.main\_crn |

| DATE | 10 |
| :---- | :---- |

  START\_DATE Must be in format: DD/MM/YYYY HH24:MI PATIENT\_DETENTION\_MASTER.start\_date 

DATE 10 END\_DATE Must be in format: DD/MM/YYYY HH24:MI PATIENT\_DETENTION\_MASTER.end\_date 

| DATE | 10 |   EXPIRY\_DATE |  Must be in format: DD/MM/YYYY HH24:MI  PATIENT\_DETENTION\_MASTER.expiry\_date |
| :---- | :---- | :---- | :---- |

| TABLE NAME: LOAD\_MH\_DETENTION\_TRANSFERSPatient detention transfer details.  Creates records in:  PATIENT\_DETENTION\_TRANSFERS Loaded via:   OASLOADMH\_PACKAGE.load\_detentions  |
| :---- |

 

DATATYPE LENGTH NAME COMMENTS 

| NUMBER | 42 |
| :---- | :---- |

  RECORD\_NUMBER Unique identifier for this extracted record. 

NUMBER 42 MH\_DM\_RECORD\_NU   
Foreign key to LOAD\_MH\_DETENTION\_MASTER.record\_number 

MBER 

| VARCHAR2 | 10 |
| :---- | :---- |

  SYSTEM\_CODE Unique identifier for the originating system.  Maps to: code type 10599 "Dataload System" 

VARCHAR2 100 EXTERNAL\_SYSTEM\_ID Unique admission id from the source system.~~© 2026 Altera Digital Health Inc. and/or its subsidiaries. All rights reserve~~d~~.~~ 80

| VARCHAR2 | 80 |   MAIN\_CRN\_TYPE |  Main hospital number id type as loaded into   LOAD\_PMI.main\_crn\_type |
| :---- | :---- | :---- | ----- |
| VARCHAR2 | 30 |   MAIN\_CRN |  Main hospital number as loaded into LOAD\_PMI.main\_crn |

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAABFElEQVR4Xu3XsQ2AQBDAsF+JhiWRYOTjayYgkgs32SDrPJ4BAAAoWN8AAADwVwYGAADIMDAAAECGgQEAADIMDAAAkGFgAACADAMDAABkGBgAACDDwAAAABkGBgAAyDAwAABAhoEBAAAyDAwAAJBhYAAAgAwDAwAAZBgYAAAgw8AAAAAZBgYAAMgwMAAAQIaBAQAAMgwMAACQYWAAAIAMAwMAAGQYGAAAIMPAAAAAGQYGAADIMDAAAECGgQEAADIMDAAAkGFgAACADAMDAABkGBgAACDDwAAAABkGBgAAyNgDcw8AAEDBHphrAAAACgwMAACQYWAAAIAMAwMAAGQYGAAAIMPAAAAAGQYGAADIMDAAAEDGC5jVIB8iLOzDAAAAAElFTkSuQmCC>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAACZklEQVR4Xu3dMU7EABAEQT8JAnjkncSXjVO3JWJGqqCy3gdMtMf35/sEAABYcHx9vE4AAIAFBgwAADDDgAEAAGYYMAAAwAwDBgAAmGHAAAAAMwwYAABghgEDAADMuAbM+/zb8+iufbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tX+zoB59NW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+3vrgHzcwIAACwwYAAAgBkGDAAAMMOAAQAAZhgwAADADAMGAACYYcAAAAAzDBgAAGCGAQMAAMw4np8vAQAA/qdrwLxOAACABQYMAAAww4ABAABmGDAAAMAMAwYAAJhhwAAAADMMGAAAYIYBAwAAzDBgAACAGQYMAAAww4ABAABmGDAAAMAMAwYAAJhhwAAAADMMGAAAYIYBAwAAzDBgAACAGQYMAAAww4ABAABmGDAAAMAMAwYAAJhhwAAAADMMGAAAYMYv4zM2EpL9Jw0AAAAASUVORK5CYII=>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAABEklEQVR4Xu3XwQmAQBDAwK1IBLFHsem7vxUYmMd80kHmPt8FAABQMN8AAADwVwYGAADIMDAAAECGgQEAADIMDAAAkGFgAACADAMDAABkGBgAACDDwAAAABkGBgAAyDAwAABAhoEBAAAyDAwAAJBhYAAAgAwDAwAAZBgYAAAgw8AAAAAZBgYAAMgwMAAAQIaBAQAAMgwMAACQYWAAAIAMAwMAAGQYGAAAIGOu41kAAAAFBgYAAMgwMAAAQIaBAQAAMgwMAACQYWAAAIAMAwMAAGQYGAAAIMPAAAAAGQYGAADIMDAAAECGgQEAADIMDAAAkGFgAACADAMDAABkGBgAACDDwAAAABkGBgAAyDAwAABAxgaz1UfkxpMeigAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAABIUlEQVR4Xu3XyQ3CUBAFwUnILEakB0gO/OMzEdBSHWo0ehn0PLdjAQAAFMzvAAAA8K8EDAAAkCFgAACADAEDAABkCBgAACBDwAAAABkCBgAAyBAwAABAhoABAAAyBAwAAJAhYAAAgAwBAwAAZAgYAAAgQ8AAAAAZ8zgPAABAweyXYwEAABQIGAAAIEPAAAAAGQIGAADIEDAAAECGgAEAADIEDAAAkCFgAACADAEDAABknAHzWQAAAAUCBgAAyJj9ej4AAAABAgYAAMgQMAAAQIaAAQAAMgQMAACQIWAAAIAMAQMAAGQIGAAAIEPAAAAAGQIGAADImPvlvQAAAAoEDAAAkDG37bUAAAAKBAwAAJAhYAAAgAwBAwAAZAgYAAAg4wtAQI1K1AXG/QAAAABJRU5ErkJggg==>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAABGUlEQVR4Xu3XwQ2DUAwFQbeTRBDaS5qHf6YCVprDPFnuYGf//E8AAICCuT8AAACeSsAAAAAZAgYAAMgQMAAAQIaAAQAAMgQMAACQIWAAAIAMAQMAAGQIGAAAIEPAAAAAGQIGAADIEDAAAECGgAEAADIEDAAAkCFgAACADAEDAABkzPb+nQAAAAUCBgAAyBAwAABAhoABAAAyBAwAAJAhYAAAgAwBAwAAZAgYAAAgQ8AAAAAZAgYAAMgQMAAAQIaAAQAAMgQMAACQIWAAAIAMAQMAAGQIGAAAIEPAAAAAGQIGAADIEDAAAECGgAEAADIEDAAAkCFgAACADAEDAABkzPZaBwAAQMB81wAAABQIGAAAIGOONQAAAAUXFRZiwyfsiPEAAAAASUVORK5CYII=>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAACeklEQVR4Xu3cMUolQQBF0dqM+r+6NQfG/UNPxzfQdB6c4BRFczfwgq7z+fJ9AQAALDj9AAAA8L8yYAAAgBkGDAAAMON83AcAAMCC83z9vgAAABYYMAAAwIzzfLsvAAAAAwwYAABghgEDAADMMGAAAIAZBgwAADDDgAEAAGYYMAAAwAwDBgAAmHHeX76vnzx/0b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+fzPgAAABYYMAAAwAwDBgAAmGHAAAAAM/zE/4v21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pfnlEGAABmGDAAAMAMAwYAAJhhwAAAADMMGAAAYIYBAwAAzDBgAACAGQYMAAAw4x4wfy8AAIAFBgwAADDjHjB/LgAAgAXn+bgvAAAAAwwYAABghgEDAADMMGAAAIAZBgwAADDjPN6+LgAAgAUGDAAAMMOAAQAAZpzH630BAAAYcN5fvi4AAIAFBgwAADDjfNwHAADAgn9InEtc8ICpKgAAAABJRU5ErkJggg==>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAAB1klEQVR4Xu3XMUpDURRF0T8XE1EyL0XF+Zc/ad2Fth5YxXo8LnsC57hdv08AAIAFRw8AAAD/lQEDAADMMGAAAIAZBgwAADDDgAEAAGYYMAAAwAwDBgAAmGHAAAAAMwwYAABghgEDAADMMGAAAIAZBgwAADDDgAEAAGYYMAAAwIzHgPk6f/f5h/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+5+O2/PHCQAAsOB4vbyfAAAACwwYAABghgEDAADMMGAAAIAZBgwAADDDgAEAAGYYMAAAwAwDBgAAmGHAAAAAMwwYAABghgEDAADMMGAAAIAZBgwAADDDgAEAAGYYMAAAwAwDBgAAmGHAAAAAMwwYAABgxvHy9HYCAAAsOK6PBwAAYMFxvTw+AAAAAwwYAABghgEDAADMMGAAAIAZBgwAADDDgAEAAGYYMAAAwIw77AOoqiAm734AAAAASUVORK5CYII=>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAABKUlEQVR4Xu3dsQ0CMRAAwWsFHiP6ekH/HTyOqYCVJpjTyR1sYHvW43MBAAAUzO8BAADAvxIwAABAhoABAAAyBAwAAJAhYAAAgAwBAwAAZAgYAAAgQ8AAAAAZs469AAAABAgYAAAgY157AAAAFAgYAAAgQ8AAAAAZAgYAAMiY5x4AAAAF/oEBAAAyBAwAAJAhYAAAgAwBAwAAZAgYAAAgQ8AAAAAZAgYAAMgQMAAAQIaAAQAAMnbAvC8AAIACAQMAAGTMWnsBAAAIEDAAAECGgAEAADIEDAAAkCFgAACADAEDAABkzHGcFwAAQIGAAQAAMua47wUAACBg1u28AAAACua5BwAAQIGAAQAAMgQMAACQ4Q4MAACQ4RUyAAAgQ8AAAAAZPrIEAAAyvgE325d4fgOMAAAAAElFTkSuQmCC>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAACe0lEQVR4Xu3Xu21cQRREwclkfwqLgEgp/xieaB9j5bKBMmowuDgJ9Hm9/l4AAAALTg8AAAA/lQEDAADMMGAAAIAZBgwAADDDgAEAAGYYMAAAwIzzfP65AAAAFpzH4+sCAABYYMAAAAAzDBgAAGCGAQMAAMwwYAAAgBkGDAAAMMOAAQAAZpzn7et65/Ef7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/2dX59PwAAAAsMGAAAYIYBAwAAzDBgAACAGQYMAAAww4ABAABmGDAAAMAMAwYAAJhhwAAAADMMGAAAYIYBAwAAzDBgAACAGQYMAAAww4ABAABmGDAAAMAMAwYAAJhhwAAAADMMGAAAYIYBAwAAzDBgAACAGQYMAAAww4ABAABmGDAAAMAMAwYAAJhxXrfP653n7fdb7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/21b7aV/tqX+2rfbWv9tW+2lf7al/tq321r/bVvtpX+2pf7at9ta/2de63jwsAAGCBAQMAAMw49/v3BwAAYMA/C8mVZIhdBU4AAAAASUVORK5CYII=>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAABJUlEQVR4Xu3XwU0EUQwFQSfCzGc3KyD/NAafiYCW6lBPljPoOefnAQAAKJi/DwAAgP9KwAAAABkCBgAAyJhz7wEAABAwrx0AAIACAQMAAGTMewcAAKBAwAAAABkCBgAAyBAwAABAhoABAAAyBAwAAJAhYAAAgAwBAwAAZAgYAAAgQ8AAAAAZAgYAAMgQMAAAQIaAAQAAMgQMAACQIWAAAIAMAQMAAGQIGAAAIEPAAAAAGQIGAADIEDAAAECGgAEAADIEDAAAkDGvHQAAgAIBAwAAZMzZAQAAKJhz9gAAAAgQMAAAQIaAAQAAMgQMAACQIWAAAICMue/vBwAAoEDAAAAAGXNdXw8AAEDBXB97AAAABMzZAQAAKBAwAABAxnzuAAAAFPwC/xZhYJDhWXIAAAAASUVORK5CYII=>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAABJklEQVR4Xu3XyQ3CUBQEwReIFxESEuD8I/n4TAS0VIeaw2TQ8ziuBQAAUDC/BwAAwL8SMAAAQIaAAQAAMgQMAACQIWAAAIAMAQMAAGQIGAAAIEPAAAAAGXPeAwAAUCBgAACAjDnOawEAABTMfnwWAABAwWz7ewEAABQIGAAAIEPAAAAAGQIGAADIEDAAAECGgAEAADIEDAAAkCFgAACADAEDAABkCBgAACBDwAAAABkCBgAAyBAwAABAhoABAAAyBAwAAJAhYAAAgIzZttcCAAAoEDAAAEDGHNtzAQAAFMx5DwAAQIGAAQAAMgQMAACQIWAAAICMO2BeCwAAoOAOmPcCAAAoEDAAAECGgAEAADIEDAAAkCFgAACADAEDAABkCBgAACDjC3OLtHfQkfzCAAAAAElFTkSuQmCC>

[image12]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAzAAAAAsCAYAAAC69F1mAAAC/ElEQVR4Xu3XsY0VSxRF0UmD/2YqE1IABHg/iA6CUAj00U1jbVBhco21peUdu0r3ZT2+PgGAEb7/8j8Af/TtZf3+eAIA/8ZxeZEk/bHzjXzvgAGAORwwkrRpOWAAYBQHjCRtWvcB8+W59/kvuq/uq/vqvrqv7qv76r66r+6r++q+uq/uq/vqvrqv7qv76r66r+6r++q+uq/uq/vqvrqv7qv76r66r+6r++q+uq/uq/vqvrqv7qv76r66r+6r++q+uq/uq/vqvrqv7qv76r66r+6r+5+OSz9sSdLd+X5eB8ynJwAwwnHphy1JujvfSAcMAAzigJGkTcsBAwCjOGAkadNywADAKA4YSdq0HDAAMIoDRpI2LQcMAIzigJGkTcsBAwCjOGAkadNywADAKA4YSdq0HDAAMIoDRpI2LQcMAIzigJGkTcsBAwCjOGAkadNywADAKA4YSdq0HDAAMIoDRpI2LQcMAIzigJGkTcsBAwCjOGAkadNywADAKA4YSdq0HDAAMIoDRpI2LQcMAIzigJGkTcsBAwCjOGAkadNywADAKA4YSdq0HDAAMIoDRpI2LQcMAIzigJGkTcsBAwCjOGAkadNywADAKA4YSdq0HDAAMIoDRpI2LQcMAIzigJGkTcsBAwCjOGAkadNywADAKA4YSdq0HDAAMIoDRpI2LQcMAIzigJGkTes6YN7OBxMAGOG49MOWJN29XQfM4/XTEwAY4bj0w5Yk3Z1v5HnAvJ0PJgAwwXHphy1JujvfSAcMAAzigJGkTQ8HDACM4oCRpE2PnwfM68fnzn9/0X11X91X99V9dV/dV/fVfXVf3Vf31X11X91X99V9dV/dV/fVfXVf3Vf31X11X91X99V9dV/dV/fVfXVf3Vf31X11X91X99V9dV/dV/fVfXVf3Vf31X11X91X99V9dV/dV/fVfXVf3f9yXPphS5LuzvfzPGDefXgCACMcl37YkqS78410wADAIA4YSdr0uA6Y1/PBBABGOC79sCVJd+cb+f4HfYw4tHiFp4oAAAAASUVORK5CYII=>
## Implementation Update (v0.0.2)

This requirement baseline is now implemented in the product control-plane with UI-first lifecycle orchestration:

1. Dynamic schema explorer (`/schemas`) for source and target table/column profiles.
2. Dynamic mapping contract explorer (`/mappings`) with class/table filtering.
3. Lifecycle step orchestration (`/lifecycle`) to execute each migration stage from UI.
4. Operational run console (`/runs`) with release profile controls and gate/reject review.
5. Connector configuration and discovery UI (`/connectors`) for CSV, emulators, and connector stubs.

Execution remains synchronized between UI and backend CLI because both invoke the same pipeline commands and write the same reports/artifacts.
