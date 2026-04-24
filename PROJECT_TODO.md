# Funds Transfer Pricing – Project TODO

This file is a living backlog for the prototype → parity build.

## Work completed so far (summary)

- **UI + navigation**
  - Sidebar grouped nav with child sections: **Input data**, **Mappings**, **Curves**.
  - `/runs/` now includes a **Data status** table showing latest import/recalc actions with row counts + timestamps.

- **Core tables + pages (SQLite-backed)**
  - `ReportingGroup` (from `extract/reporting_group.csv`; duplicates skipped on re-import).
  - `InputRefDataRow` (from `extract/input_refdata.csv`) with:
    - `lookup` and `helper = lookup + LCY/FCY` (concat, no separators).
    - `reporting_group_imported` restricted to dropdown values from `ReportingGroup`.
    - calculated `tenor_days` from (`tenor_number`, `tenor_units`) using 30/365 conventions.
    - placeholder `ftp_rate` column (blank for now, will be curve-interpolated later).
    - UI supports **add/edit rows** (`/reference-data/input-refdata/…`), paginated list.
  - `ConsolidatedDataRow` (from `extract/data_consolidated.csv`, 11k+ rows), paginated browser at `/input-data/consolidated/`.
    - Stores raw row in `payload` to tolerate messy CSV headers.
    - Added calculated columns per `extract/temp_calculatedcolumns_consoldata.csv` (LOOKUP1/BSISLOOKUP/Input RefData LOOKUP, rates, interests, etc.).
  - `BsIsMapping` (from `extract/bs_is_mapping.csv`, 4k+ rows), paginated browser at `/mappings/`.
    - Added computed numeric columns: `asset_liab_value`, `pnl_value`, `proportion`, `pnl_attributed`.

- **Curve management (DB editable)**
  - `CurvePoint` table (currency LCY/FCY, component BASE/SPREAD, tenor_days, rate).
  - UI pages: `/curves/lcy/` and `/curves/fcy/` with separate **Base curve** vs **Liquidity spread** sections.
  - Add/Edit/Delete curve points via forms.
  - Seed command from mock data: `seed_curves_from_mock`.

- **Recalc / import commands**
  - Imports:
    - `import_extract` (reporting_group + input_refdata)
    - `import_consolidated_data`
    - `import_bs_is_mapping`
    - `import_reporting_groups`
  - Recalcs:
    - `recalc_consolidated_data`
    - `recalc_bs_is_mapping`
  - **Important rule**: “first match wins” for VLOOKUP-style behavior (fixed P&L Interest mismatch by removing SUM behavior).
  - Commands log `DataEvent` entries for the `/runs/` status dashboard.

## Current state (already done)

- Django prototype running locally.
- Imports in place (CSV → SQLite + basic browse UIs):
  - `extract/reporting_group.csv` → `ReportingGroup`
  - `extract/input_refdata.csv` → `InputRefDataRow` (+ calculated `calc_key_1`, `helper`)
  - `extract/tmp_reporting_group.csv` → bulk-applied into `InputRefDataRow.reporting_group_imported`
  - `extract/bs_is_mapping.csv` → `BsIsMapping` (paginated)
  - `extract/data_consolidated.csv` → `ConsolidatedDataRow` (paginated; full row stored in JSON payload)
- Nav reorganized with grouped sections.

## Next: keep importing tables + calculated columns

### Imports to add (extract → DB → browse UI)

- [ ] `No FTP Accounts` (if/when extracted)
- [ ] Curves (LCY + FCY) when ready
- [ ] Any remaining reference tables needed for parity

### ConsolidatedData calculated columns (linking to prior tables)

Goal: enrich `ConsolidatedDataRow` using:
- `InputRefDataRow` (assumptions / reference attribution)
- `BsIsMapping` (BS→IS mapping)

- [ ] Define the join keys between `ConsolidatedDataRow` and `InputRefDataRow`
  - Likely uses `helper` (concat + LCY/FCY) or a close equivalent
- [ ] Add calculated/enriched fields onto `ConsolidatedDataRow` (DB columns), e.g.
  - reporting group
  - inclusion/exclusion flags
  - mapping target (P&L item)
  - tenor / target rate / etc. (as required by parity path)
- [ ] Backfill existing rows + ensure re-import pipeline recomputes deterministically
- [ ] Add “exceptions views” (unmatched keys / missing mapping / missing reporting group)

## UX: “pivot table” interaction (click → report refresh)

Goal: replicate the Excel UX where clicking a subcategory (or similar) refreshes a report view based on `ConsolidatedDataRow`.

- [ ] Decide the “pivot dimension” for the first iteration (e.g. `Sub-cat`, `MinorAccount`, `Reporting group`)
- [ ] Build a report page that:
  - lists pivot values + counts/sums
  - links each pivot row to a filtered detail view
- [ ] Implement “click-to-refresh” behavior
  - server-rendered: link with query params (`?sub_cat=...`)
  - optionally HTMX later for partial refresh without full reload
- [ ] Add drilldown: pivot summary → row-level table (paginated)
- [ ] Add export of the filtered dataset (CSV first)

## Parity foundations (later, but important)

- [ ] Lock down one “parity month” test pack (inputs + expected outputs)
- [ ] Implement core curve interpolation parity (`Saayman_Interpolate`) when curves are imported
- [ ] Start parity checks: row counts, totals, and a small number of report slices

