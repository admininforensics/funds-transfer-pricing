from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ui.models import InputRefDataRow
from ui.models import ReportingGroup


def _read_reporting_groups(path: Path) -> list[str]:
    if not path.exists():
        raise CommandError(f"CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise CommandError(f"CSV has no header row: {path}")
        if "ReportingGroup" not in reader.fieldnames:
            raise CommandError(f"Expected column 'ReportingGroup' in {path.name}, got: {reader.fieldnames}")
        values: list[str] = []
        for row in reader:
            v = (row.get("ReportingGroup") or "").strip()
            values.append(v)
        return values


class Command(BaseCommand):
    help = "Apply extract/tmp_reporting_group.csv values onto InputRefDataRow.reporting_group_imported in row order."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="extract/tmp_reporting_group.csv",
            help="Path to tmp reporting group mapping CSV.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and show what would change without writing.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"]).resolve()
        dry_run = bool(options["dry_run"])

        values = _read_reporting_groups(path)
        rows = list(InputRefDataRow.objects.order_by("id").all())

        n_values = len(values)
        n_rows = len(rows)
        n_apply = min(n_values, n_rows)

        if n_apply == 0:
            raise CommandError("Nothing to apply (no values or no input_refdata rows).")

        assigned = 0
        cleared = 0
        reporting_groups_created = 0

        for i in range(n_apply):
            v = values[i]
            row = rows[i]

            if not v:
                # Blank = clear assignment
                if row.reporting_group_imported:
                    cleared += 1
                if not dry_run:
                    row.reporting_group_imported = ""
                    row.save(update_fields=["reporting_group_imported"])
                continue

            if row.reporting_group_imported != v:
                assigned += 1
                if not dry_run:
                    row.reporting_group_imported = v
                    row.save(update_fields=["reporting_group_imported"])

            # Ensure the selected value exists in the canonical ReportingGroup table
            if v and not dry_run:
                _, created = ReportingGroup.objects.get_or_create(group_type="Imported", account=v)
                if created:
                    reporting_groups_created += 1

        msg = (
            "Applied tmp reporting groups\n"
            f"- tmp values: {n_values}\n"
            f"- input_refdata rows: {n_rows}\n"
            f"- applied (min): {n_apply}\n"
            f"- rows assigned/changed: {assigned}\n"
            f"- rows cleared: {cleared}\n"
            f"- reporting groups created: {reporting_groups_created}\n"
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] " + msg))
            transaction.set_rollback(True)
        else:
            self.stdout.write(self.style.SUCCESS(msg))

