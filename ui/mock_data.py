from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MockRun:
    id: int
    month: str
    status: str
    created_by: str
    created_at: str
    validation_state: str
    calc_state: str
    publish_state: str


def get_run(run_id: int) -> MockRun:
    return MockRun(
        id=run_id,
        month="2026-03",
        status="Setup",
        created_by="gunther.marais",
        created_at="2026-04-17 10:12",
        validation_state="Issues found",
        calc_state="Not run",
        publish_state="Draft",
    )


def list_runs() -> list[MockRun]:
    return [
        get_run(101),
        MockRun(**{**get_run(100).__dict__, "month": "2026-02", "status": "Published", "validation_state": "Passed", "calc_state": "Complete"}),
        MockRun(**{**get_run(99).__dict__, "month": "2026-01", "status": "Complete", "validation_state": "Passed", "calc_state": "Complete"}),
    ]


def get_uploads() -> list[dict]:
    return [
        {"source_type": "Average balance sheet snapshot", "filename": "Avg_BS_2026-03.xlsx", "status": "Uploaded", "uploaded_at": "2026-04-17 10:21", "checksum": "demo"},
        {"source_type": "Average P&L", "filename": "", "status": "Missing", "uploaded_at": "", "checksum": ""},
        {"source_type": "Equity reserves", "filename": "Equity_Reserves_2026-03.xlsx", "status": "Uploaded", "uploaded_at": "2026-04-17 10:22", "checksum": "demo"},
        {"source_type": "Fixed assets", "filename": "", "status": "Missing", "uploaded_at": "", "checksum": ""},
    ]


def get_validation() -> dict:
    return {
        "missing_files": ["Average P&L", "Fixed assets"],
        "missing_columns": [{"file": "Avg_BS_2026-03.xlsx", "columns": ["Branch", "Sub-Sub-Cat"]}],
        "unmatched_line_items": [{"minor_account": "12345", "name": "Demo Unmatched Account"}],
        "missing_assumptions": [{"minor_account": "23456", "required": ["Reporting group", "Tenor", "Target rate"]}],
        "missing_mappings": [{"balance_sheet_item": "Loans: Retail", "needs": "P&L interest mapping"}],
        "curve_issues": ["FCY curve version missing for 2026-03", "Duplicate tenor on LCY curve: 365d"],
        "recon_warnings": ["Included + excluded rows ≠ total processed rows (demo warning)"],
    }


def list_assumptions() -> list[dict]:
    return [
        {"include_in_ftp": True, "minor_account": "11111", "reporting_group": "Retail loans", "target_rate": "Prime-1.00%", "tenor_number": 6, "tenor_unit": "M", "notes": ""},
        {"include_in_ftp": True, "minor_account": "22222", "reporting_group": "Corporate deposits", "target_rate": "JIBAR+0.50%", "tenor_number": 1, "tenor_unit": "M", "notes": "Review tenor"},
        {"include_in_ftp": False, "minor_account": "33333", "reporting_group": "", "target_rate": "", "tenor_number": "", "tenor_unit": "", "notes": "Excluded account"},
    ]


def list_mappings() -> list[dict]:
    return [
        {"balance_sheet_item": "Loans: Retail", "pnl_splits": [{"pnl_item": "Interest income: Retail", "proportion": 1.0}], "effective_from": "2025-01"},
        {"balance_sheet_item": "Deposits: Current accounts", "pnl_splits": [{"pnl_item": "Interest expense: Deposits", "proportion": 0.7}, {"pnl_item": "Fees/Other", "proportion": 0.3}], "effective_from": "2025-01"},
    ]


def get_curves() -> dict:
    return {
        "LCY": {"base_points": [{"tenor_days": 1, "rate": "8.25%"}, {"tenor_days": 30, "rate": "8.35%"}, {"tenor_days": 365, "rate": "8.60%"}], "spread_points": [{"tenor_days": 30, "spread": "0.10%"}]},
        "FCY": {"base_points": [{"tenor_days": 1, "rate": "5.10%"}, {"tenor_days": 30, "rate": "5.20%"}, {"tenor_days": 365, "rate": "5.55%"}], "spread_points": [{"tenor_days": 30, "spread": "0.05%"}]},
    }


def get_results() -> dict:
    return {
        "kpis": [
            {"label": "Total average balance", "value": "ZAR 12.3bn"},
            {"label": "Total FTP interest", "value": "ZAR 98.7m"},
            {"label": "BU interest", "value": "ZAR 54.2m"},
            {"label": "CFU interest", "value": "ZAR 44.5m"},
        ],
        "reporting_groups": [
            {"group": "Retail loans", "avg_balance": "ZAR 4.1bn", "ftp_interest": "ZAR 45.0m"},
            {"group": "Corporate deposits", "avg_balance": "ZAR 3.8bn", "ftp_interest": "ZAR (12.0m)"},
        ],
        "currencies": [
            {"currency": "LCY", "avg_balance": "ZAR 10.9bn", "ftp_interest": "ZAR 90.1m"},
            {"currency": "FCY", "avg_balance": "ZAR 1.4bn", "ftp_interest": "ZAR 8.6m"},
        ],
        "rows": [
            {"minor_account": "11111", "currency": "LCY", "avg_balance": "ZAR 120m", "tenor_days": 180, "target_rate": "Prime-1.00%", "ftp_rate": "8.40%", "ftp_interest": "ZAR 2.1m"},
            {"minor_account": "22222", "currency": "LCY", "avg_balance": "ZAR 95m", "tenor_days": 30, "target_rate": "JIBAR+0.50%", "ftp_rate": "8.35%", "ftp_interest": "ZAR (0.8m)"},
        ],
        "controls": [
            {"label": "Source totals vs engine totals", "status": "Warning", "detail": "Avg BS totals within 0.5% (demo)"},
            {"label": "Mapped vs unmapped rows", "status": "Fail", "detail": "12 unmapped rows require mapping"},
            {"label": "Included vs excluded totals", "status": "Pass", "detail": "Included + excluded = total"},
            {"label": "Prior month comparisons", "status": "Info", "detail": "Retail loans FTP interest up 3.1% (demo)"},
        ],
        "formats": ["Excel", "CSV", "PDF (optional)"],
    }

