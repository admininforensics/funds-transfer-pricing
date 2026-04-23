# Funds Transfer Pricing – Project TODO

This file is a living backlog for the prototype → parity build.

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

