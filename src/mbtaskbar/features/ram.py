from __future__ import annotations

import psutil

from mbtaskbar.core.feature import Feature, Metric
from mbtaskbar.core.registry import register_feature

GB = 1024**3


@register_feature
class RamFeature(Feature):
    id = "ram"
    display_name = "Arbeitsspeicher"
    supports_threshold = True

    def update(self) -> list[Metric]:
        vm = psutil.virtual_memory()
        return [Metric("RAM", f"{vm.used / GB:.1f} / {vm.total / GB:.1f} GB", vm.percent)]

    def icon_text(self, metrics: list[Metric]) -> str:
        return f"{metrics[0].percent:.0f}" if metrics and metrics[0].percent is not None else "-"
