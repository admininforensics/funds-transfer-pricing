from __future__ import annotations

from django import forms

from .models import CurvePoint, InputRefDataRow, ReportingGroup


class InputRefDataRowForm(forms.ModelForm):
    reporting_group_imported = forms.ChoiceField(
        choices=[],
        required=False,
        label="Reporting group",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "—")]
        choices.extend(
            (rg.account, f"{rg.group_type} · {rg.account}") for rg in ReportingGroup.objects.order_by("group_type", "account")
        )
        self.fields["reporting_group_imported"].choices = choices

    class Meta:
        model = InputRefDataRow
        fields = [
            "reporting_group_imported",
            "target_rate",
            "tenor_number",
            "tenor_units",
            "ftp_rate",
            "assets_liabs",
            "num_and_name",
            "minor_account",
            "account_name",
            "sub_cat",
            "sub_sub_cat",
            "currency_scope",
        ]


class CurvePointForm(forms.ModelForm):
    class Meta:
        model = CurvePoint
        fields = ["tenor_days", "rate"]

