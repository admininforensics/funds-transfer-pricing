from __future__ import annotations

import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ui.management.commands._log import log_data_event
from ui.models import InputRefDataRow, ReportingGroup, _tenor_days


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise CommandError(f"CSV not found: {path}")
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise CommandError(f"CSV has no header row: {path}")
        return [{k: (v or "").strip() for k, v in row.items()} for row in reader]


class Command(BaseCommand):
    help = "Import extracted CSVs from ./extract into the dev database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-dir",
            default="extract",
            help="Directory containing extract CSVs (default: extract).",
        )
        parser.add_argument(
            "--truncate",
            action="store_true",
            help="Delete existing rows before import.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        base_dir = Path(options["base_dir"]).resolve()
        truncate: bool = bool(options["truncate"])

        reporting_group_path = base_dir / "reporting_group.csv"
        input_refdata_path = base_dir / "input_refdata.csv"

        reporting_rows = _read_csv(reporting_group_path)
        ref_rows = _read_csv(input_refdata_path)

        if truncate:
            ReportingGroup.objects.all().delete()
            InputRefDataRow.objects.all().delete()

        rg_created = 0
        rg_seen = 0
        for row in reporting_rows:
            rg_seen += 1
            group_type = row.get("Type", "")
            account = row.get("Account", "")
            if not group_type or not account:
                continue
            _, created = ReportingGroup.objects.get_or_create(
                group_type=group_type,
                account=account,
            )
            if created:
                rg_created += 1

        ir_created = 0
        ir_seen = 0
        for row in ref_rows:
            ir_seen += 1
            lookup = row.get("LOOKUP", "")
            assets_liabs = row.get("Assets Liabs", "")
            num_and_name = row.get("Num & Name", "")
            minor_account = row.get("MinorAccount", "")
            account_name = row.get("Name of account", "")
            sub_cat = row.get("Sub-cat", "")
            sub_sub_cat = row.get("Sub-Sub-Cat", "")
            currency_scope = row.get("LCY/FCY", "")
            reporting_group = row.get("ReportingGroup", "")
            target_rate = row.get("TargetRate", "")
            tenor_number = row.get("TenorNumber", "")
            tenor_units = row.get("TenorUnits", "")
            helper = row.get("Helper", "")
            calc_key_1 = lookup or ""
            if not helper:
                helper = f"{lookup}{currency_scope}" if lookup else ""

            # Minimum fields required to have a stable-ish row identity.
            if not (assets_liabs and num_and_name and minor_account and account_name and currency_scope):
                continue

            _, created = InputRefDataRow.objects.get_or_create(
                lookup=lookup,
                assets_liabs=assets_liabs,
                num_and_name=num_and_name,
                minor_account=minor_account,
                account_name=account_name,
                sub_cat=sub_cat,
                sub_sub_cat=sub_sub_cat,
                currency_scope=currency_scope,
                calc_key_1=calc_key_1,
                helper=helper,
                reporting_group_imported=reporting_group,
                target_rate=target_rate,
                tenor_number=tenor_number,
                tenor_units=tenor_units,
                tenor_days=_tenor_days(tenor_number, tenor_units),
            )
            if created:
                obj = InputRefDataRow.objects.get(
                    lookup=lookup,
                    assets_liabs=assets_liabs,
                    num_and_name=num_and_name,
                    minor_account=minor_account,
                    account_name=account_name,
                    sub_cat=sub_cat,
                    sub_sub_cat=sub_sub_cat,
                    currency_scope=currency_scope,
                )
                obj.recalc()
                obj.save(update_fields=["lookup", "calc_key_1", "helper", "tenor_days"])
            if created:
                ir_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Import complete\n"
                f"- reporting_group.csv: seen={rg_seen} created={rg_created} total={ReportingGroup.objects.count()}\n"
                f"- input_refdata.csv: seen={ir_seen} created={ir_created} total={InputRefDataRow.objects.count()}"
            )
        )
        log_data_event(table_key="reporting_group", action="import", row_count=ReportingGroup.objects.count())
        log_data_event(table_key="input_refdata", action="import", row_count=InputRefDataRow.objects.count())

