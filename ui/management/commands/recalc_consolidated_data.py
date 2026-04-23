from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction

from ui.models import BsIsMapping, ConsolidatedDataRow, InputRefDataRow


def _to_decimal(s: str) -> Decimal:
    try:
        return Decimal((s or "").strip())
    except (InvalidOperation, ValueError):
        return Decimal("0")


class Command(BaseCommand):
    help = "Recalculate consolidated data calculated columns."

    @transaction.atomic
    def handle(self, *args, **options):
        # Build lookup dict from InputRefDataRow by helper (first match wins = lowest id).
        # key: helper (input refdata lookup), value: (reporting_group, tenor_days, target_rate, ftp_rate)
        ref_by_helper: dict[str, tuple[str, int, Decimal, Decimal]] = {}
        for r in InputRefDataRow.objects.order_by("id").only(
            "helper",
            "reporting_group_imported",
            "tenor_days",
            "target_rate",
            "ftp_rate",
        ):
            key = (r.helper or "").strip()
            if not key or key in ref_by_helper:
                continue
            ref_by_helper[key] = (
                (r.reporting_group_imported or "").strip(),
                int(r.tenor_days or 0),
                _to_decimal(r.target_rate),
                _to_decimal(r.ftp_rate),
            )

        # Build bs->(pl, pnl_attributed) mapping dict (first match wins by id).
        mapping_by_bsislookup: dict[str, tuple[str, Decimal]] = {}
        for m in BsIsMapping.objects.order_by("id").only("balance_sheet", "prof_and_loss", "pnl_attributed"):
            k = (m.balance_sheet or "").strip()
            if not k or k in mapping_by_bsislookup:
                continue
            mapping_by_bsislookup[k] = ((m.prof_and_loss or "").strip(), m.pnl_attributed or Decimal("0"))

        updated = 0
        batch: list[ConsolidatedDataRow] = []
        batch_size = 1500

        qs = ConsolidatedDataRow.objects.order_by("row_number").only(
            "id",
            "row_number",
            "month_english_name",
            "line_code",
            "trial_balance_name",
            "tb_name2",
            "business_unit_name",
            "branch_code_name",
            "rm_name",
            "assets_liabs",
            "num_and_name",
            "minor_account",
            "major_account",
            "currency_type",
            "value_raw",
            "tenor",
            "sub_cat",
            "payload",
        )

        for r in qs.iterator(chunk_size=2000):
            # Direct copies
            r.sub_sub_cat = r.trial_balance_name or ""
            r.acct_num = r.line_code or ""

            # Concats (no separators)
            r.lookup1 = f"{r.assets_liabs}{r.minor_account}{r.major_account}{r.sub_cat}{r.sub_sub_cat}"
            r.bsislookup = f"{r.lookup1}{r.business_unit_name}{r.branch_code_name}{r.rm_name}"
            r.lookup2 = f"{r.assets_liabs}{r.minor_account}{r.major_account}{r.sub_cat}"
            r.input_refdata_lookup = f"{r.lookup1}{r.currency_type}"

            # Persist BSISLOOKUP in payload for downstream commands
            payload = dict(r.payload or {})
            payload["BSISLOOKUP"] = r.bsislookup
            r.payload = payload

            # Lookups into input_refdata (first match wins)
            ref = ref_by_helper.get(r.input_refdata_lookup)
            if ref:
                r.reporting_group = ref[0]
                r.tenor_days = ref[1]
                r.target_rate = ref[2]
                r.ftp_rate = ref[3]
            else:
                r.reporting_group = ""
                r.tenor_days = 0
                r.target_rate = Decimal("0")
                r.ftp_rate = Decimal("0")

            # AverageBalance: no FTP BS Line gate (ignored)
            avg = _to_decimal(r.value_raw)
            r.average_balance = avg

            # Gross_Int / FTP_Int: no gate
            r.gross_int = (Decimal("-1") * avg * (r.target_rate or Decimal("0"))) / Decimal("12")
            r.ftp_int = (Decimal("-1") * avg * (r.ftp_rate or Decimal("0"))) / Decimal("12")

            # P&L item + P&L Interest: lookup using BSISLOOKUP in BS<->IS
            mapping = mapping_by_bsislookup.get(r.bsislookup)
            if mapping:
                r.pnl_item = mapping[0]
                r.pnl_interest = mapping[1]
            else:
                r.pnl_item = ""
                r.pnl_interest = Decimal("0")

            # Actual Rate (no gate)
            if avg == 0:
                r.actual_rate = Decimal("0")
            else:
                r.actual_rate = (Decimal("-1") * (r.pnl_interest / avg)) * Decimal("12")

            batch.append(r)
            if len(batch) >= batch_size:
                ConsolidatedDataRow.objects.bulk_update(
                    batch,
                    [
                        "sub_sub_cat",
                        "acct_num",
                        "lookup1",
                        "bsislookup",
                        "lookup2",
                        "input_refdata_lookup",
                        "payload",
                        "reporting_group",
                        "tenor_days",
                        "average_balance",
                        "target_rate",
                        "gross_int",
                        "ftp_rate",
                        "ftp_int",
                        "pnl_item",
                        "pnl_interest",
                        "actual_rate",
                    ],
                    batch_size=batch_size,
                )
                updated += len(batch)
                batch.clear()

        if batch:
            ConsolidatedDataRow.objects.bulk_update(
                batch,
                [
                    "sub_sub_cat",
                    "acct_num",
                    "lookup1",
                    "bsislookup",
                    "lookup2",
                    "input_refdata_lookup",
                    "payload",
                    "reporting_group",
                    "tenor_days",
                    "average_balance",
                    "target_rate",
                    "gross_int",
                    "ftp_rate",
                    "ftp_int",
                    "pnl_item",
                    "pnl_interest",
                    "actual_rate",
                ],
                batch_size=batch_size,
            )
            updated += len(batch)

        self.stdout.write(
            self.style.SUCCESS(
                "Consolidated data recalculation complete\n"
                f"- rows updated: {updated}\n"
                f"- input_refdata helper keys: {len(ref_by_helper)}\n"
                f"- bs<->is keys: {len(mapping_by_bsislookup)}"
            )
        )

