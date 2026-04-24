from __future__ import annotations

from ui.models import DataEvent


def log_data_event(*, table_key: str, action: str, row_count: int, notes: str = "") -> None:
    DataEvent.objects.create(
        table_key=table_key,
        action=action,
        row_count=row_count,
        notes=notes,
    )

