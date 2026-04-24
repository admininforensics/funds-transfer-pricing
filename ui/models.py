from django.db import models
from django.utils import timezone

class ReportingGroup(models.Model):
    group_type = models.CharField(max_length=64)
    account = models.CharField(max_length=255)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["group_type", "account"],
                name="uq_reporting_group_type_account",
            )
        ]

    def __str__(self) -> str:
        return f"{self.group_type} · {self.account}"


class InputRefDataRow(models.Model):
    lookup = models.CharField(max_length=1024, blank=True, default="")
    assets_liabs = models.CharField(max_length=32)
    num_and_name = models.CharField(max_length=255)
    minor_account = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255)
    sub_cat = models.CharField(max_length=255, blank=True)
    sub_sub_cat = models.CharField(max_length=255, blank=True)
    currency_scope = models.CharField(max_length=16)
    calc_key_1 = models.CharField(max_length=1024, db_index=True, default="")
    helper = models.CharField(max_length=1050, db_index=True, default="")
    reporting_group_imported = models.CharField(max_length=255, blank=True, default="")
    target_rate = models.CharField(max_length=64, blank=True, default="")
    tenor_number = models.CharField(max_length=32, blank=True, default="")
    tenor_units = models.CharField(max_length=32, blank=True, default="")
    tenor_days = models.IntegerField(blank=True, default=0, db_index=True)
    ftp_rate = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "assets_liabs",
                    "num_and_name",
                    "minor_account",
                    "account_name",
                    "sub_cat",
                    "sub_sub_cat",
                    "currency_scope",
                ],
                name="uq_input_refdata_row_identity",
            )
        ]

    def __str__(self) -> str:
        return f"{self.minor_account} · {self.account_name} ({self.currency_scope})"

    def recalc(self) -> None:
        # Use the explicit LOOKUP from the extract as the primary key component.
        # If LOOKUP is missing (manually added row), fall back to a deterministic concat.
        if self.lookup:
            self.calc_key_1 = self.lookup
        else:
            self.calc_key_1 = f"{self.assets_liabs}{self.minor_account}{self.account_name}{self.sub_sub_cat}"
            self.lookup = self.calc_key_1

        self.helper = f"{self.lookup}{self.currency_scope}"
        self.tenor_days = _tenor_days(self.tenor_number, self.tenor_units)


def _tenor_days(tenor_number: str, tenor_units: str) -> int:
    try:
        n = float((tenor_number or "").strip())
    except ValueError:
        return 0
    u = (tenor_units or "").strip().lower()

    if u.startswith("day"):
        return int(round(n))
    if u.startswith("month"):
        return int(round(n * 30))
    if u.startswith("year"):
        return int(round(n * 365))
    return 0


class BsIsMapping(models.Model):
    balance_sheet = models.TextField()
    prof_and_loss = models.TextField()
    asset_liab_value = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    pnl_value = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    proportion = models.DecimalField(max_digits=18, decimal_places=12, default=0)
    pnl_attributed = models.DecimalField(max_digits=24, decimal_places=6, default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["balance_sheet", "prof_and_loss"],
                name="uq_bs_is_mapping_pair",
            )
        ]

    def __str__(self) -> str:
        return f"BS→IS: {self.balance_sheet[:40]}…"


class ConsolidatedDataRow(models.Model):
    row_number = models.IntegerField(db_index=True)

    month_english_name = models.CharField(max_length=32, blank=True, default="")
    line_code = models.CharField(max_length=64, blank=True, default="")
    trial_balance_name = models.CharField(max_length=255, blank=True, default="")
    tb_name2 = models.CharField(max_length=255, blank=True, default="")
    business_unit_name = models.CharField(max_length=128, blank=True, default="")
    branch_code_name = models.CharField(max_length=128, blank=True, default="")
    rm_name = models.CharField(max_length=128, blank=True, default="")
    assets_liabs = models.CharField(max_length=32, blank=True, default="")
    num_and_name = models.CharField(max_length=255, blank=True, default="")
    minor_account = models.CharField(max_length=255, blank=True, default="")
    major_account = models.CharField(max_length=255, blank=True, default="")
    currency_type = models.CharField(max_length=16, blank=True, default="")
    value_raw = models.CharField(max_length=64, blank=True, default="")
    tenor = models.CharField(max_length=64, blank=True, default="")
    sub_cat = models.CharField(max_length=255, blank=True, default="")

    # Calculated columns (from temp_calculatedcolumns_consoldata.csv)
    sub_sub_cat = models.CharField(max_length=255, blank=True, default="")
    acct_num = models.CharField(max_length=64, blank=True, default="")
    lookup1 = models.CharField(max_length=2048, blank=True, default="", db_index=True)
    bsislookup = models.CharField(max_length=3072, blank=True, default="", db_index=True)
    lookup2 = models.CharField(max_length=1024, blank=True, default="", db_index=True)
    input_refdata_lookup = models.CharField(max_length=3072, blank=True, default="", db_index=True)

    reporting_group = models.CharField(max_length=255, blank=True, default="", db_index=True)
    tenor_days = models.IntegerField(blank=True, default=0, db_index=True)
    average_balance = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    target_rate = models.DecimalField(max_digits=18, decimal_places=12, default=0)
    gross_int = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    ftp_rate = models.DecimalField(max_digits=18, decimal_places=12, default=0)
    ftp_int = models.DecimalField(max_digits=24, decimal_places=6, default=0)

    pnl_item = models.TextField(blank=True, default="")
    pnl_interest = models.DecimalField(max_digits=24, decimal_places=6, default=0)
    actual_rate = models.DecimalField(max_digits=18, decimal_places=12, default=0)

    payload = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["row_number"], name="uq_consolidated_row_number"),
        ]

    def __str__(self) -> str:
        return f"Row {self.row_number} · {self.minor_account} · {self.currency_type}"


class CurvePoint(models.Model):
    class Currency(models.TextChoices):
        LCY = "LCY", "LCY"
        FCY = "FCY", "FCY"

    class Component(models.TextChoices):
        BASE = "BASE", "Base curve"
        SPREAD = "SPREAD", "Liquidity spread"

    currency = models.CharField(max_length=3, choices=Currency.choices)
    component = models.CharField(max_length=10, choices=Component.choices)
    tenor_days = models.IntegerField(db_index=True)
    rate = models.DecimalField(max_digits=18, decimal_places=12)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["currency", "component", "tenor_days"],
                name="uq_curve_point_currency_component_tenor",
            )
        ]
        indexes = [
            models.Index(fields=["currency", "component", "tenor_days"], name="idx_curve_point_lookup"),
        ]

    def __str__(self) -> str:
        return f"{self.currency} {self.component} {self.tenor_days}d"


class DataEvent(models.Model):
    table_key = models.CharField(max_length=64, db_index=True)
    action = models.CharField(max_length=64)
    row_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["table_key", "-created_at"], name="idx_dataevent_latest"),
        ]

    def __str__(self) -> str:
        return f"{self.table_key} · {self.action} · {self.created_at.isoformat()}"
