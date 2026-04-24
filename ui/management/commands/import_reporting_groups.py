from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ui.models import ReportingGroup
from ui.management.commands._log import log_data_event


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise CommandError(f"CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise CommandError(f"CSV has no header row: {path}")
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


class Command(BaseCommand):
    help = "Drop and re-import ReportingGroup from extract/reporting_group.csv."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="extract/reporting_group.csv",
            help="Path to reporting_group.csv (default: extract/reporting_group.csv).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"]).resolve()
        rows = _read_csv(path)

        # Wipe table first (removes any mistakenly-added groups).
        ReportingGroup.objects.all().delete()

        created = 0
        seen = 0
        skipped_duplicates = 0
        seen_keys: set[tuple[str, str]] = set()
        for row in rows:
            seen += 1
            group_type = row.get("Type", "")
            account = row.get("Account", "")
            if not group_type or not account:
                continue
            key = (group_type, account)
            if key in seen_keys:
                skipped_duplicates += 1
                continue
            seen_keys.add(key)
            ReportingGroup.objects.create(group_type=group_type, account=account)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                "ReportingGroup import complete\n"
                f"- source rows seen: {seen}\n"
                f"- created: {created}\n"
                f"- duplicate rows skipped: {skipped_duplicates}\n"
                f"- total in DB: {ReportingGroup.objects.count()}"
            )
        )
        log_data_event(table_key="reporting_group", action="import", row_count=ReportingGroup.objects.count())

