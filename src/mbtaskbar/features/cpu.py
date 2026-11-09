from __future__ import annotations

import psutil

from mbtaskbar.core.feature import Feature, Metric
from mbtaskbar.core.registry import register_feature


@register_feature
class CpuFeature(Feature):
    id = "cpu"
    display_name = "CPU"
    supports_threshold = True

    def __init__(self) -> None:
        super().__init__()
        # First non-blocking call only primes the counters and returns 0.0
        psutil.cpu_percent(interval=None)

    def update(self) -> list[Metric]:
        pct = psutil.cpu_percent(interval=None)
        return [Metric("CPU", f"{pct:.0f} %", pct)]

    def icon_text(self, metrics: list[Metric]) -> str:
        return f"{metrics[0].percent:.0f}" if metrics and metrics[0].percent is not None else "-"
