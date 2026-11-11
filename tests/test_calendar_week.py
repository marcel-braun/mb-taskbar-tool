from datetime import date

import pytest

from mbtaskbar.features.calendar_week import CalendarWeekFeature


@pytest.mark.parametrize(
    ("day", "week"),
    [
        (date(2026, 11, 9), 46),
        (date(2026, 12, 31), 53),
        (date(2027, 1, 1), 53),
        (date(2027, 1, 3), 53),
        (date(2027, 1, 4), 1),
        (date(2024, 12, 30), 1),
    ],
)
def test_iso_week(day: date, week: int) -> None:
    feature = CalendarWeekFeature(today=lambda: day)
    metrics = feature.update()
    assert feature.icon_text(metrics) == str(week)
    assert metrics[0].value_text.startswith(f"{week} ")
