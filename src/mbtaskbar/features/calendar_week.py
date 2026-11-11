from __future__ import annotations

from collections.abc import Callable
from datetime import date

from mbtaskbar.core.feature import Feature, Metric
from mbtaskbar.core.registry import register_feature


@register_feature
class CalendarWeekFeature(Feature):
    id = "calendar_week"
    display_name = "Kalenderwoche"

    def __init__(self, today: Callable[[], date] = date.today) -> None:
        super().__init__()
        self._today = today

    def update(self) -> list[Metric]:
        d = self._today()
        week = d.isocalendar().week
        return [Metric("KW", f"{week}  ({d:%d.%m.%Y})")]

    def icon_text(self, metrics: list[Metric]) -> str:
        return str(self._today().isocalendar().week)
