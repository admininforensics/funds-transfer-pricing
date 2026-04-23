from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ui.models import ConsolidatedDataRow


def _normalize_headers(raw_headers: list[str]) -> list[str]:
    out: list[str] = []
    seen: dict[str, int] = {}
    for i, h in enumerate(raw_headers):
        h2 = (h or "").strip()
        if not h2:
            h2 = f"_extra_{i}"
        if h2 in seen:
            seen[h2] += 1
            h2 = f"{h2}__{seen[h2]}"
        else:
            seen[h2] = 0
        out.append(h2)
    return out


class Command(BaseCommand):
    help = "Drop and re-import consolidated data from extract/data_consolidated.csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="extract/data_consolidated.csv",
            help="Path to data_consolidated.csv (default: extract/data_consolidated.csv).",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=2000,
            help="bulk_create batch size (default: 2000).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"]).resolve()
        batch_size: int = int(options["batch_size"])
        if not path.exists():
            raise CommandError(f"CSV not found: {path}")

        ConsolidatedDataRow.objects.all().delete()

        created = 0
        seen = 0
        buffer: list[ConsolidatedDataRow] = []

        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            try:
                raw_headers = next(reader)
            except StopIteration:
                raise CommandError(f"Empty CSV: {path}")

            headers = _normalize_headers(raw_headers)

            # Map known columns to canonical field names
            def get(row: list[str], col: str) -> str:
                try:
                    idx = headers.index(col)
                except ValueError:
                    return ""
                return (row[idx] if idx < len(row) else "").strip()

            for row in reader:
                seen += 1
                payload = {headers[i]: (row[i] if i < len(row) else "").strip() for i in range(len(headers))}
                obj = ConsolidatedDataRow(
                    row_number=seen,
                    month_english_name=get(row, "MonthEnglishName"),
                    line_code=get(row, "LINE_CODE"),
                    trial_balance_name=get(row, "TRIAL_BALANCE_NAME"),
                    tb_name2=get(row, "TB_NAME2"),
                    business_unit_name=get(row, "BusinessUnitName"),
                    branch_code_name=get(row, "BranchCodeName"),
                    rm_name=get(row, "RMName"),
                    assets_liabs=get(row, "Assets Liabs"),
                    num_and_name=get(row, "Num & Name"),
                    minor_account=get(row, "MinorAccount"),
                    major_account=get(row, "MajorAccount"),
                    currency_type=get(row, "Currency_Type"),
                    value_raw=get(row, "Value"),
                    tenor=get(row, "TENOR"),
                    sub_cat=get(row, "Sub-cat"),
                    payload=payload,
                )
                buffer.append(obj)

                if len(buffer) >= batch_size:
                    ConsolidatedDataRow.objects.bulk_create(buffer, batch_size=batch_size)
                    created += len(buffer)
                    buffer.clear()

        if buffer:
            ConsolidatedDataRow.objects.bulk_create(buffer, batch_size=batch_size)
            created += len(buffer)

        self.stdout.write(
            self.style.SUCCESS(
                "Consolidated data import complete\n"
                f"- rows seen: {seen}\n"
                f"- rows created: {created}\n"
                f"- total in DB: {ConsolidatedDataRow.objects.count()}"
            )
        )

