from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from ui import mock_data
from ui.models import CurvePoint
from ui.management.commands._log import log_data_event


class Command(BaseCommand):
    help = "Seed CurvePoint rows from ui.mock_data.get_curves() if none exist."

    @transaction.atomic
    def handle(self, *args, **options):
        if CurvePoint.objects.exists():
            self.stdout.write(self.style.WARNING("CurvePoint already populated; skipping."))
            return

        curves = mock_data.get_curves()
        created = 0
        for currency in ["LCY", "FCY"]:
            curve = curves[currency]
            for p in curve["base_points"]:
                CurvePoint.objects.create(
                    currency=currency,
                    component="BASE",
                    tenor_days=int(p["tenor_days"]),
                    rate=Decimal(str(p["rate"]).replace("%", "")) / Decimal("100"),
                )
                created += 1
            for p in curve["spread_points"]:
                CurvePoint.objects.create(
                    currency=currency,
                    component="SPREAD",
                    tenor_days=int(p["tenor_days"]),
                    rate=Decimal(str(p["spread"]).replace("%", "")) / Decimal("100"),
                )
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded CurvePoint rows: {created}"))
        log_data_event(table_key="curves", action="seed", row_count=CurvePoint.objects.count())

