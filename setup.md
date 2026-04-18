# Funds Transfer Pricing Web App Build Specification

## Purpose of this document

This document is a reverse-engineered build specification for converting the Excel workbook **`NBS FTP Model July 2024 20240824.xlsm`** into a governed web application. It is written so it can be pasted into Cursor AI or used as a handoff document for implementation.

The goal is to preserve the approved business method of the current workbook while replacing fragile spreadsheet mechanics with a maintainable Python web application.

---

# 1. Executive Summary

## 1.1 What the current workbook does

The workbook is a monthly Funds Transfer Pricing (FTP) engine used to:

* import accounting and balance data from four monthly Excel source files
* consolidate them into a unified row-level data set
* assign FTP assumptions and product reference metadata to line items
* map balance sheet items to P&L items
* construct local and foreign currency FTP curves
* calculate target interest, actual interest, FTP rate, FTP interest, and attribution outputs
* produce treasury/management reports and reconciliations

## 1.2 What the web application should become

The target application is a **monthly treasury FTP processing system** with these modules:

* source file ingestion and validation
* governed reference data maintenance
* governed balance-sheet-to-P&L mapping
* curve maintenance and interpolation
* calculation engine
* control checks and reconciliation dashboard
* report viewing and export
* run history, audit trail, and versioning

## 1.3 Recommended technology

Recommended stack:

* **Backend:** Python + Django
* **Database:** PostgreSQL
* **Computation:** Pandas / NumPy + pure Python domain services
* **Frontend:** Django templates first, optional HTMX or lightweight JS, React only if later needed
* **Task processing:** optional Celery/RQ only if runs become heavy
* **Exports:** openpyxl / xlsxwriter

Reasoning:

* this is a master-data-heavy internal business application
* auditability and CRUD administration are more important than SPA richness for the MVP
* Django is well suited to controlled workflows, permissions, versioned reference tables, and report screens

---

# 2. FTP Domain Context

## 2.1 Plain language definition

Funds Transfer Pricing is an internal mechanism for assigning the cost or benefit of funding to the business units that generate assets and liabilities.

In practice:

* business units that originate loans should be charged an internal funding rate
* business units that gather deposits should receive internal funding credit
* treasury / central funding should own the value or cost of term funding, liquidity, and curve management

This workbook explicitly splits results into:

* **BU interest** = business unit commercial/product margin
* **CFU interest** = central funding unit effect from interest-rate curve management and funding structure

## 2.2 Business objective of the web app

The app must let treasury and finance answer questions such as:

* what FTP income/cost belongs to each product or reporting group?
* what portion of interest is commercial margin versus treasury/CFU effect?
* how do actual and target interest compare?
* what changed from last month?
* are all relevant accounts mapped and configured correctly?

---

# 3. Reverse-Engineered Workbook Anatomy

## 3.1 Workbook sheets identified

The workbook contains the following sheets:

1. `ReadMe`
2. `Control`
3. `FTP_Report`
4. `Recon on overall`
5. `Funding Report`
6. `FTP curves`
7. `FTP curves FCY`
8. `Input Refdata`
9. `Data`
10. `BS<->IS`
11. `No FTP Accounts`
12. `Unit Tests`

## 3.2 Logical modules represented by the sheets

### Module A: User run control

* `Control`
* stores run settings such as path/date/filter controls and macro triggers

### Module B: Imported and enriched calculation data

* `Data`
* central row-level engine table

### Module C: Reference/master data

* `Input Refdata`
* line-item assumptions for reporting group, tenor, rate, inclusion

### Module D: Balance sheet to P&L mapping

* `BS<->IS`
* links balance sheet items to P&L items and attribution proportions

### Module E: FTP curves

* `FTP curves`
* `FTP curves FCY`
* local and foreign currency rate curve inputs and interpolation logic

### Module F: Controls, reconciliation, and output

* `Unit Tests`
* `Recon on overall`
* `Funding Report`
* `FTP_Report`

### Module G: Explicit exclusions

* `No FTP Accounts`
* likely maintains accounts outside FTP scope or exception logic

---

# 4. Key Data Structures Identified in the Workbook

## 4.1 Main calculation table in `Data`

A structured table named `ConsolidatedData` exists on the `Data` sheet and spans approximately `A1:AG11673`.

This is the row-level engine table for the workbook.

### Columns identified in `Data`

The following column names were found:

* `Num & Name`
* `MinorAccount`
* `Name of account`
* `Sub-cat`
* `Sub-Sub-Cat`
* `Branch`
* `Currency`
* `Actual`
* `Balance`
* `Average Balance`
* `Lookup1`
* `BSISLOOKUP`
* `LOOKUP2`
* `Input RefData LOOKUP`
* `FTP BS Line`
* `ReportingGroup`
* `Tenor Days`
* `AverageBalance`
* `Target Rate`
* `Gross_Int`
* `FTP Rate`
* `FTP_Int`
* `P&L Item`
* `P&L Interest`
* `Actual Rate`
* `Reporting Helper`

Note: some column names appear duplicated or normalized differently in formulas. The implementation must confirm the final source dictionary during build.

## 4.2 Reference table in `Input Refdata`

The following columns were identified:

* `Assets Liabs`
* `Num & Name`
* `MinorAccount`
* `Name of account`
* `Sub-cat`
* `Sub-Sub-Cat`
* `LCY/FCY`
* `Helper`
* `ReportingGroup`
* `TargetRate`
* `TenorNumber`
* `TenorUnits`
* `TenorDays`
* `FTP_Rate`

This is effectively the product/line-item assumption table.

## 4.3 Mapping table in `BS<->IS`

The following fields were identified:

* `Balance Sheet`
* `Prof & Loss`
* `Asset/Liab`
* `P&L`
* `Proportion`
* `P&L attributed`

This sheet bridges balance-sheet line items to P&L interest line items.

## 4.4 Reporting sheet structure

A table-like block exists on `FTP_Report` approximately in range `AN10:BT7284`.

The report sheet appears to pull filtered and ranked results from the `Data` sheet using formula-driven extraction logic.

---

# 5. Reverse-Engineered Calculation Flow

## 5.1 Monthly run flow in the workbook

The current workbook performs the following monthly process:

1. User specifies run month and input folder.
2. VBA imports four monthly source files.
3. Imported data is appended/consolidated into the `Data` sheet.
4. The `Data` sheet derives helper keys and looks up assumptions from `Input Refdata`.
5. The `Data` sheet maps balance-sheet rows to P&L rows using `BS<->IS`.
6. FTP curves are read from curve sheets and interpolated.
7. FTP rates are assigned to line items using tenor and currency.
8. Interest metrics are calculated for each row.
9. Reports and reconciliations refresh.
10. Unit tests are checked for import/process integrity.

## 5.2 Conceptual target process in the web app

### Step 1: Create run

* select reporting month
* upload four required source files

### Step 2: Validate input files

* structure validation
* filename validation
* month/date consistency validation
* mandatory columns validation

### Step 3: Normalize imported data

* parse all source files
* standardize column names/types
* classify rows by source and record type
* create a unified normalized data set

### Step 4: Match to canonical line items

* create stable internal identifiers
* match imported rows to known line-item aliases/master records
* flag unmatched or ambiguous rows

### Step 5: Apply reference assumptions

* determine inclusion/exclusion
* assign reporting group
* assign tenor number/unit/days
* assign target rate
* assign currency grouping

### Step 6: Apply BS-to-IS mapping

* match line items to P&L accounts
* apply mapping proportions
* attribute P&L interest

### Step 7: Build FTP curves

* load curve points for LCY and FCY
* validate ordering and completeness
* interpolate curve values by tenor
* apply spread logic

### Step 8: Calculate FTP metrics

* gross interest
* target interest
* FTP rate
* FTP interest
* actual rate
* actual vs target comparisons
* BU / CFU attribution metrics

### Step 9: Reconcile and validate

* totals reconciliations
* unmapped rows
* missing assumptions
* unexpected sign checks
* output control checks

### Step 10: Publish results

* summary report
* detailed drilldown
* downloadable extracts
* run snapshot frozen for audit

---

# 6. Spreadsheet Fragilities That Must Be Fixed in the App

## 6.1 String-based keys

The workbook uses helper keys and concatenated text references because the source data lacks a clean stable identifier.

### Risks

* account name changes break matching
* structural changes in source reports silently corrupt output
* duplicate names create ambiguity

### Target solution

* create canonical internal IDs for line items
* maintain alias history for source-system names
* support matching rules and exception workflows
* store match confidence and override decisions

## 6.2 Manual synchronization across sheets

`Input Refdata` and `BS<->IS` must remain synchronized manually in the workbook.

### Risks

* orphan mappings
* inconsistent configuration
* missing new rows

### Target solution

* use relational tables with foreign keys and validations
* show exception queues for missing mapping or missing assumptions

## 6.3 Heavy formula coupling

The workbook relies on `MATCH`, `VLOOKUP`, `XLOOKUP`, `OFFSET`, `INDEX`, `SMALL`, `IFERROR`, and interpolation formulas across thousands of rows.

### Risks

* difficult to test
* expensive to maintain
* hard to trace and audit

### Target solution

* move logic to explicit Python services
* make each transformation step testable
* store intermediate results where needed

## 6.4 Macro-driven workflow

The current process depends on a specific sequence of macros and user discipline.

### Risks

* inconsistent execution
* partial refreshes
* user error

### Target solution

* explicit run lifecycle statuses
* deterministic validation and calculation stages
* immutable run outputs once published

---

# 7. Proposed Web Application Architecture

## 7.1 High-level architecture

### Presentation layer

* Django templates
* optional HTMX for dynamic partial refreshes
* optional charting library for report visuals

### Application layer

* Django apps for domains:

  * runs
    n  - ingestion
  * reference_data
  * mappings
  * curves
  * calculations
  * reports
  * audit

### Domain/calculation layer

* pure Python services for:

  * file parsing
  * normalization
  * line-item matching
  * curve construction
  * interpolation
  * FTP computations
  * reconciliations

### Persistence layer

* PostgreSQL tables for master data, run data, results, and audit logs

### Optional async layer

* Celery/RQ for long-running imports/calculations if needed

## 7.2 Recommended project structure

```text
ftp_app/
  manage.py
  config/
  apps/
    runs/
    ingestion/
    reference_data/
    mappings/
    curves/
    calculations/
    reports/
    audit/
    users/
  domain/
    parsers/
    matching/
    interpolation/
    ftp_engine/
    validations/
    reconciliations/
  tests/
  docs/
```

---

# 8. Proposed Database Schema

## 8.1 Core master/reference tables

### `canonical_line_item`

Represents a stable internal line item.

Fields:

* id
* code_internal
* asset_liability_type
* minor_account
* num_and_name
* account_name
* sub_category
* sub_sub_category
* default_currency_scope
* is_active
* effective_from
* effective_to
* created_at
* updated_at

### `line_item_alias`

Stores historical or source-specific naming variants.

Fields:

* id
* canonical_line_item_id
* source_system_name
* source_file_type
* alias_key_raw
* is_primary
* effective_from
* effective_to
* matching_notes

### `reporting_group`

Fields:

* id
* code
* name
* description
* is_active

### `line_item_ftp_assumption`

Reference assumptions for a line item.

Fields:

* id
* canonical_line_item_id
* currency_scope
* include_in_ftp
* reporting_group_id
* target_rate
* tenor_number
* tenor_unit
* tenor_days
* effective_from
* effective_to
* assumption_version_id
* notes

### `no_ftp_account_rule`

Explicit exclusion rules.

Fields:

* id
* canonical_line_item_id
* reason
* effective_from
* effective_to

## 8.2 Mapping tables

### `pnl_line_item`

Fields:

* id
* code_internal
* pnl_name
* source_alias
* is_active

### `bs_is_mapping`

Maps canonical balance-sheet items to P&L items.

Fields:

* id
* canonical_line_item_id
* pnl_line_item_id
* proportion
* asset_liability_type
* effective_from
* effective_to
* mapping_version_id
* notes

## 8.3 Curve tables

### `curve_definition`

Fields:

* id
* currency_code
* curve_type
* description
* active

### `curve_version`

Fields:

* id
* curve_definition_id
* run_month
* status
* notes
* created_by
* created_at

### `curve_point`

Fields:

* id
* curve_version_id
* tenor_days
* tenor_label
* rate_type
* rate_value
* point_order

Possible `rate_type` values:

* base_curve
* overnight
* liquidity_spread
* ftp_curve_derived

## 8.4 Run and ingestion tables

### `ftp_run`

Represents one monthly run.

Fields:

* id
* run_month
* status
* created_by
* created_at
* validated_at
* calculated_at
* published_at
* assumption_version_id
* mapping_version_id
* notes

Suggested statuses:

* draft
* files_uploaded
* validation_failed
* validation_passed
* mapping_exceptions
* ready_to_calculate
* calculated
* published
* archived

### `ftp_run_input_file`

Fields:

* id
* ftp_run_id
* source_file_type
* original_filename
* stored_path
* checksum
* upload_timestamp
* parsed_successfully
* parse_errors_json

Suggested source file types:

* avg_balance_sheet
* avg_pnl_mtd
* equity_reserves
* fixed_assets

### `ftp_run_raw_record`

Raw normalized imported rows.

Fields:

* id
* ftp_run_id
* source_file_type
* source_row_number
* raw_payload_json
* import_key
* record_type

### `ftp_run_normalized_record`

Unified row-level records used in the engine.

Fields:

* id
* ftp_run_id
* canonical_line_item_id nullable
* source_match_status
* source_key
* currency_code
* branch
* actual_amount
* balance_amount
* average_balance_amount
* pnl_amount
* source_attributes_json

## 8.5 Calculation result tables

### `ftp_run_line_result`

Stores row-level FTP results.

Fields:

* id
* ftp_run_id
* normalized_record_id
* include_in_ftp
* reporting_group_id
* tenor_days
* target_rate
* ftp_rate
* gross_interest
* ftp_interest
* pnl_interest
* actual_rate
* bu_interest
* cfu_interest
* reconciliation_flag
* calculation_payload_json

### `ftp_run_aggregate_result`

Aggregated results by dimension.

Fields:

* id
* ftp_run_id
* aggregation_level
* reporting_group_id nullable
* currency_code nullable
* branch nullable
* business_unit nullable
* metric_name
* metric_value

## 8.6 Audit/versioning tables

### `assumption_version`

Fields:

* id
* name
* description
* effective_from
* effective_to
* locked
* created_by
* created_at

### `mapping_version`

Fields:

* id
* name
* description
* effective_from
* effective_to
* locked
* created_by
* created_at

### `change_log`

Fields:

* id
* entity_type
* entity_id
* change_type
* changed_by
* changed_at
* old_value_json
* new_value_json

---

# 9. Key Domain Logic To Preserve From the Workbook

## 9.1 Input file requirements

The workbook expects exactly four source files per run:

1. average balance sheet snapshot
2. P&L MTD snapshot
3. equity and reserves snapshot
4. fixed assets snapshot

The app must preserve this run model unless business confirms a change.

## 9.2 Reference assumptions

Each included line item needs:

* reporting group
* tenor number
* tenor unit
* derived tenor days
* target rate
* currency classification
* inclusion/exclusion status

## 9.3 BS-to-IS mapping

The workbook manually maps balance sheet items to P&L items and stores a proportion.

The app must preserve:

* one-to-one
* one-to-many
* many-to-one
* proportion-based attribution

## 9.4 Curve logic

The workbook uses separate LCY and FCY curve sheets with interpolation.

Preserve:

* base curve points
* overnight rate handling
* liquidity spread points
* tenor ordering rules
* interpolation behavior
* treatment of points before the shortest tenor
* overnight liquidity spread = zero rule

## 9.5 Metrics calculated

At minimum preserve the following output concepts:

* target rate
* FTP rate
* gross interest
* FTP interest
* P&L interest
* actual rate
* BU interest
* CFU interest

---

# 10. Calculation Engine Specification

## 10.1 Canonical pipeline

Each normalized record should be processed in this order:

1. identify canonical line item
2. determine whether included in FTP
3. determine reporting group
4. determine tenor number / unit / days
5. determine target rate
6. select correct currency curve
7. interpolate FTP curve rate for tenor
8. calculate FTP interest
9. map to P&L item(s)
10. assign attributed P&L interest
11. calculate actual rate
12. derive BU and CFU decomposition
13. persist row result and aggregate summaries

## 10.2 Tenor normalization

The workbook stores tenor as number plus unit.

Target application should normalize all tenors into days for pricing.

Suggested conversion rules:

* days: 1 day = 1
* months: use a documented convention, e.g. 30.4375 average days or business-approved integer conversion
* years: use a documented convention, e.g. 365 or business-approved convention

Important: before implementation, confirm the workbook’s exact tenor day conversion logic and replicate it for parity.

## 10.3 FTP rate assignment

For each included line item:

* identify currency group (LCY / FCY)
* determine tenor days
* retrieve the active curve version for the run month
* interpolate FTP rate using the workbook-equivalent interpolation method
* store both the final FTP rate and the curve version used

## 10.4 Interest calculations

Exact formulas must be confirmed against workbook samples, but the engine should expose and test the following metrics:

* target interest
* actual interest
* FTP interest
* gross interest
* actual rate
* attribution deltas

Implementation note:
Do not assume all rates are annualized the same way. Confirm monthly/annual conventions from workbook formulas during parity phase.

## 10.5 BU vs CFU decomposition

The workbook description states:

* BU interest = interest from selling products at a premium
* CFU interest = interest from managing interest rate curve movements

The app should explicitly model BU and CFU as separate metrics, even if their exact derivation needs to be confirmed from formulas during parity testing.

---

# 11. Validation Rules

## 11.1 File-level validation

Validate on upload:

* all four required files are present
* filename patterns match expected run month
* no duplicate uploads for the same source type unless replacing intentionally
* workbook/sheet structure is parseable
* required columns exist
* no hidden structural changes in headers

## 11.2 Content-level validation

Validate after parsing:

* mandatory fields populated
* amounts numeric
* currency values valid
* no duplicate records where uniqueness is expected
* no unmapped new line items unless explicitly accepted
* no included rows missing tenor/reporting group/target rate
* no included rows missing BS-to-IS mapping where required

## 11.3 Curve validation

Validate curve versions:

* all mandatory base curve points present
* spread points are in ascending tenor order
* no duplicate tenors
* no overnight spread values except zero
* no invalid negative tenor values
* rate values numeric and within tolerance bands if desired

## 11.4 Reconciliation validation

Examples:

* balance totals reconcile to source totals
* P&L totals reconcile to imported P&L totals
* included + excluded = total processed rows
* sum of attributed P&L interest reconciles to mapped P&L totals
* report totals reconcile to row-level engine totals

## 11.5 Run-blocking validations

These should prevent calculation:

* missing required source file
* missing required curve version
* unmatched mandatory line items
* missing FTP assumptions for included rows
* missing required BS-to-IS mapping
* critical parser failure

---

# 12. Recommended Screen / UX Design

## 12.1 Screen: Run dashboard

Purpose:

* show monthly runs and statuses
* create new run
* drill into validation, exceptions, and results

Key elements:

* run month
* status
* created by
* validation outcome
* calculation timestamp
* publish status

## 12.2 Screen: Upload files

Purpose:

* upload the four monthly source files
* assign source type
* validate filenames and month

Key elements:

* drag/drop upload
* source type selector or auto-detect
* run month consistency warnings
* upload result summary

## 12.3 Screen: Validation results

Purpose:

* surface all data quality and setup issues before calculation

Sections:

* missing files
* missing columns
* unmatched line items
* missing assumptions
* missing BS-to-IS mappings
* curve issues
* reconciliation warnings

## 12.4 Screen: Reference data maintenance

Purpose:

* maintain line-item FTP assumptions

Fields editable:

* include in FTP
* reporting group
* target rate
* tenor number
* tenor unit
* notes

Must support:

* bulk edit
* clone previous month/version
* filter on unmatched/new items

## 12.5 Screen: BS-to-IS mapping maintenance

Purpose:

* maintain attribution between balance sheet items and P&L items

Must support:

* add new mapping
* one-to-many splits with proportions
* effective dating
* validation that proportions sum correctly where required

## 12.6 Screen: Curve maintenance

Purpose:

* maintain LCY and FCY curve inputs

Must support:

* entering base curve points
* entering spread points
* automatic interpolation preview
* version locking by run month

## 12.7 Screen: Calculation results

Purpose:

* show row-level and aggregated outputs

Views:

* summary KPI cards
* reporting group table
* currency table
* business unit/branch view
* drilldown to row detail

## 12.8 Screen: Reconciliation/control dashboard

Purpose:

* give treasury confidence in the run

Views:

* source totals vs engine totals
* mapped vs unmapped rows
* included vs excluded totals
* actual vs target anomalies
* prior month comparisons

## 12.9 Screen: Report export

Purpose:

* export management-ready reports

Formats:

* Excel
* CSV
* optional PDF for formatted report packs

---

# 13. API / Service Layer Specification

Even if the first version is server-rendered, define domain services cleanly.

## 13.1 Ingestion services

* `parse_avg_balance_sheet(file)`
* `parse_avg_pnl(file)`
* `parse_equity_reserves(file)`
* `parse_fixed_assets(file)`
* `normalize_imported_records(run_id)`

## 13.2 Matching services

* `build_source_match_key(record)`
* `match_record_to_canonical_line_item(record)`
* `resolve_unmatched_records(run_id)`

## 13.3 Curve services

* `validate_curve_version(curve_version_id)`
* `interpolate_curve_rate(curve_version_id, tenor_days)`
* `build_effective_ftp_curve(curve_version_id)`

## 13.4 Mapping services

* `get_pnl_mappings_for_line_item(canonical_line_item_id, run_month)`
* `attribute_pnl_interest(record, mappings)`

## 13.5 Calculation services

* `apply_ftp_assumptions(record, run_month)`
* `calculate_row_ftp_result(record, assumptions, curve_rate, attributed_pnl)`
* `aggregate_run_results(run_id)`
* `run_reconciliations(run_id)`

## 13.6 Reporting services

* `get_run_summary(run_id)`
* `get_reporting_group_breakdown(run_id)`
* `get_currency_breakdown(run_id)`
* `export_run_report_excel(run_id)`

---

# 14. Migration Strategy From Workbook to App

## 14.1 Phase 0: Reverse engineering and parity preparation

Deliverables:

* data dictionary
* formula dictionary
* mapping rules inventory
* curve rules inventory
* run process document
* sample month test pack

## 14.2 Phase 1: Python parity engine without UI

Goal:

* ingest source files and reproduce workbook outputs in Python

Deliverables:

* parsers
* normalization pipeline
* assumption application
* curve interpolation
* row-level result generation
* parity comparison scripts

## 14.3 Phase 2: Web app MVP

Goal:

* operationalize the process in a governed app

Deliverables:

* Django project
* auth/roles
* upload workflow
* validation screens
* reference data screens
* mapping screens
* curve screens
* calculation trigger
* results and export screens

## 14.4 Phase 3: Hardening and enhancement

Possible enhancements:

* workflow approvals
* prior month variance analysis
* scenario testing
* user comments on mapping exceptions
* detailed audit history
* multi-entity or multi-client support

---

# 15. Parity Testing Strategy

## 15.1 Core principle

The first implementation goal is not elegance. It is **numerical parity** with the workbook for one or more known months.

## 15.2 Required parity test packs

For at least one approved month, capture:

* the four source files
* workbook outputs
* workbook reference data snapshots
* workbook curve inputs
* workbook mappings

## 15.3 Levels of comparison

### Level 1: row counts and import integrity

* record counts by source
* total balances
* total P&L amounts

### Level 2: reference assignment parity

* reporting group assignment
* tenor assignment
* target rate assignment
* inclusion/exclusion assignment

### Level 3: curve parity

* interpolated FTP rates by sample tenors
* LCY and FCY sample points

### Level 4: row-level calculation parity

* FTP rate
* FTP interest
* actual rate
* attributed P&L interest
* BU / CFU results

### Level 5: aggregate/report parity

* reporting group totals
* currency totals
* final report totals
* reconciliation totals

## 15.4 Tolerance rules

Define tolerances explicitly for:

* rates
* interest values
* rounding
* percentages

---

# 16. Security, Audit, and Governance Requirements

## 16.1 Roles

Suggested roles:

* admin
* treasury analyst
* reviewer/approver
* read-only report viewer

## 16.2 Audit requirements

Must audit:

* file uploads
* mapping changes
* assumption changes
* curve changes
* calculation runs
* publish actions

## 16.3 Data retention

Store run snapshots immutably once published.

A published run should retain:

* input file metadata
* normalized records
* assumptions version used
* mapping version used
* curve version used
* calculation results
* reconciliations

---

# 17. Recommended Implementation Details for Cursor AI

## 17.1 Build order

Cursor should implement in this order:

1. Django project scaffolding
2. core models for runs, assumptions, mappings, curves
3. file upload and parser layer
4. normalized record persistence
5. matching layer
6. curve interpolation service
7. FTP calculation service
8. validation/reconciliation service
9. admin screens
10. user-facing run screens and report screens
11. Excel export
12. parity test suite

## 17.2 Coding principles

* keep business logic out of views
* use pure domain services for calculations
* version assumptions and mappings
* make every run reproducible
* store enough intermediate outputs for diagnostics
* write unit tests for interpolation and matching
* write integration tests for full monthly run

## 17.3 Non-negotiables

* no spreadsheet formulas in the app
* no hard-coded hidden assumptions
* no mutable published run results
* no silent fallback behavior for missing mappings
* all critical exceptions must be visible in the UI

---

# 18. Suggested Initial Django Apps

## `runs`

Models and workflow for FTP monthly runs.

## `ingestion`

Source file upload, parsing, normalization.

## `reference_data`

Line items, aliases, reporting groups, FTP assumptions, exclusions.

## `mappings`

Balance sheet to P&L mapping maintenance.

## `curves`

Curve definitions, versions, points, interpolation previews.

## `calculations`

Domain services and persistence of row-level and aggregate results.

## `reports`

Read-only output screens and exports.

## `audit`

Change logs and run history.

---

# 19. Open Questions To Resolve During Build

These questions should be answered during the parity/discovery phase.

## 19.1 Calculation questions

* exact formula for gross interest
* exact formula for FTP interest
* exact formula for actual rate
* exact decomposition of BU vs CFU
* sign conventions for assets and liabilities
* annualization/monthly accrual conventions

## 19.2 Curve questions

* exact interpolation methodology used by `Saayman_Interpolate`
* exact extrapolation behavior for long-end tenors
* exact treatment of tenors shorter than shortest point
* exact rate units and compounding assumptions

## 19.3 Mapping questions

* when can one balance-sheet line map to multiple P&L items?
* how should proportions behave if they do not sum to 1?
* which mappings are mandatory versus optional?

## 19.4 Operational questions

* who owns assumption maintenance?
* who owns mapping approval?
* should runs be editable after calculation but before publish?
* is there a need for maker-checker workflow?

---

# 20. Build-Ready Task List for Cursor AI

## Task 1: Scaffold project

Create a Django project with apps:

* runs
* ingestion
* reference_data
* mappings
* curves
* calculations
* reports
* audit

Add PostgreSQL configuration and base settings.

## Task 2: Implement models

Implement the core models described in Section 8 with migrations.

## Task 3: Build upload workflow

Implement:

* run creation page
* file upload model/form
* validation for required source file types
* storage and checksum handling

## Task 4: Build parsers

Create parser modules for the four source file types.

Each parser should:

* read Excel file
* validate required columns
* normalize field names
* emit standardized record objects

## Task 5: Build normalized record pipeline

Persist imported rows into raw and normalized record tables.

## Task 6: Build line-item matching layer

Implement canonical line-item matching with alias support and unmatched exception reporting.

## Task 7: Build assumption maintenance UI

Use Django admin or custom screens to maintain:

* reporting group
* target rate
* tenor number
* tenor unit
* include_in_ftp

## Task 8: Build BS-to-IS mapping UI

Support creation and editing of mapping rules and proportions.

## Task 9: Build curve maintenance UI

Implement curve versions and point maintenance for LCY and FCY.

## Task 10: Build interpolation service

Implement `interpolate_curve_rate()` with pluggable interpolation logic. Start with linear interpolation unless workbook parity requires a more specific algorithm.

## Task 11: Build calculation engine

Implement the row-level FTP pipeline and result persistence.

## Task 12: Build reconciliation engine

Implement control checks and exception summaries.

## Task 13: Build reporting screens

Implement:

* run summary
* reporting group breakdown
* currency breakdown
* detailed line-item view
* export to Excel

## Task 14: Build audit/versioning support

Track all changes to assumptions, mappings, and curve versions.

## Task 15: Build parity tests

Create fixtures for one approved run month and compare outputs to workbook results.

---

# 21. Suggested Definition of Done

The MVP is done when:

1. a user can create a monthly run
2. upload all four required files
3. validate file structure and content
4. resolve missing line-item assumptions/mappings
5. maintain LCY and FCY curves
6. calculate FTP outputs
7. view reconciled summary results
8. drill into row-level outputs
9. export final report data
10. reproduce workbook outputs within agreed tolerance

---

# 22. Final Recommendation

Do not rebuild Excel screens in a browser.

Instead, preserve the workbook’s approved financial logic while redesigning the operating model around:

* stable identifiers
* explicit master data
* explicit mappings
* explicit curve versions
* reproducible monthly runs
* validation gates
* auditability

The workbook is not random chaos. It is a useful prototype of a treasury FTP engine. The right move is to convert it into a structured application, not to mimic spreadsheet mechanics.

---

# 23. Optional Next Deliverables

The next useful deliverables that can be generated from this specification are:

1. a Django model code skeleton
2. a detailed field-by-field data dictionary
3. a Mermaid system flow diagram
4. a page-by-page UX wireframe specification
5. a Cursor-ready implementation backlog with tickets and acceptance criteria
