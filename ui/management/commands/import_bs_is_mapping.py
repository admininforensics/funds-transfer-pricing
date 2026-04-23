from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ui.models import BsIsMapping


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise CommandError(f"CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise CommandError(f"CSV has no header row: {path}")
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


class Command(BaseCommand):
    help = "Drop and re-import BS<->IS mappings from extract/bs_is_mapping.csv."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            default="extract/bs_is_mapping.csv",
            help="Path to bs_is_mapping.csv (default: extract/bs_is_mapping.csv).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"]).resolve()
        rows = _read_csv(path)

        BsIsMapping.objects.all().delete()

        seen = 0
        created = 0
        skipped_blank = 0
        skipped_dupe = 0
        seen_keys: set[tuple[str, str]] = set()

        for row in rows:
            seen += 1
            bs = row.get("Balance Sheet", "")
            pl = row.get("Prof & Loss", "")
            if not bs or not pl:
                skipped_blank += 1
                continue
            key = (bs, pl)
            if key in seen_keys:
                skipped_dupe += 1
                continue
            seen_keys.add(key)
            BsIsMapping.objects.create(balance_sheet=bs, prof_and_loss=pl)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                "BS<->IS mapping import complete\n"
                f"- source rows seen: {seen}\n"
                f"- created: {created}\n"
                f"- skipped blank: {skipped_blank}\n"
                f"- skipped duplicates: {skipped_dupe}\n"
                f"- total in DB: {BsIsMapping.objects.count()}"
            )
        )

