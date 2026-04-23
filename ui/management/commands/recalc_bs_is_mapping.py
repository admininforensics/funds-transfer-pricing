from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction

from ui.models import BsIsMapping, ConsolidatedDataRow


def _to_decimal(s: str) -> Decimal:
    try:
        return Decimal((s or "").strip())
    except (InvalidOperation, ValueError):
        return Decimal("0")


class Command(BaseCommand):
    help = "Recalculate BsIsMapping numeric columns from ConsolidatedDataRow (requires BSISLOOKUP on consolidated rows)."

    @transaction.atomic
    def handle(self, *args, **options):
        # We will rely on ConsolidatedDataRow.payload["BSISLOOKUP"] once that calculated column is added.
        # For now, if it isn't present, nothing will be populated.
        sample = ConsolidatedDataRow.objects.first()
        if sample is None:
            self.stdout.write(self.style.WARNING("No consolidated data rows found; nothing to recalc."))
            return

        # Build "first match wins" values keyed by BSISLOOKUP (match Excel VLOOKUP behavior).
        first_value: dict[str, Decimal] = {}
        for r in ConsolidatedDataRow.objects.order_by("row_number").only("row_number", "value_raw", "payload").iterator(chunk_size=2000):
            key = (r.payload or {}).get("BSISLOOKUP") or ""
            if not key or key in first_value:
                continue
            first_value[key] = _to_decimal(r.value_raw)

        if not first_value:
            self.stdout.write(
                self.style.WARNING(
                    "No BSISLOOKUP keys found on consolidated data rows yet. "
                    "Add consolidated calculated columns first, then rerun."
                )
            )
            return

        # Populate Asset/Liab and P&L values by lookup.
        mappings = list(BsIsMapping.objects.all())
        for m in mappings:
            m.asset_liab_value = first_value.get(m.balance_sheet, Decimal("0"))
            m.pnl_value = first_value.get(m.prof_and_loss, Decimal("0"))

        # Group totals of Asset/Liab by Prof & Loss, then compute proportion and attributed.
        totals_by_pl: dict[str, Decimal] = {}
        for m in mappings:
            totals_by_pl[m.prof_and_loss] = totals_by_pl.get(m.prof_and_loss, Decimal("0")) + (m.asset_liab_value or Decimal("0"))

        for m in mappings:
            denom = totals_by_pl.get(m.prof_and_loss, Decimal("0"))
            if denom == 0:
                m.proportion = Decimal("0")
            else:
                m.proportion = (m.asset_liab_value or Decimal("0")) / denom
            m.pnl_attributed = (m.proportion or Decimal("0")) * (m.pnl_value or Decimal("0"))

        BsIsMapping.objects.bulk_update(
            mappings,
            ["asset_liab_value", "pnl_value", "proportion", "pnl_attributed"],
            batch_size=1000,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Recalc complete\n"
                f"- updated rows: {len(mappings)}\n"
                f"- consolidated keys available: {len(first_value)}"
            )
        )

