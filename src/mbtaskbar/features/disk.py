from __future__ import annotations

from typing import Any, TYPE_CHECKING

import psutil

from mbtaskbar.core.feature import Feature, Metric
from mbtaskbar.core.registry import register_feature

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

GB = 1024**3


def local_drives() -> list[str]:
    drives = []
    for part in psutil.disk_partitions(all=False):
        if "cdrom" in part.opts or not part.fstype:
            continue
        drives.append(part.mountpoint)
    return drives


@register_feature
class DiskFeature(Feature):
    id = "disk"
    display_name = "Laufwerke"
    supports_threshold = True

    def default_settings(self) -> dict[str, Any]:
        # Empty list = all local drives
        return {"drives": []}

    def _selected_drives(self) -> list[str]:
        return self.settings.get("drives") or local_drives()

    def update(self) -> list[Metric]:
        metrics = []
        for drive in self._selected_drives():
            try:
                usage = psutil.disk_usage(drive)
            except OSError:
                continue
            metrics.append(
                Metric(
                    drive.rstrip("\\"),
                    f"{usage.used / GB:.0f} / {usage.total / GB:.0f} GB",
                    usage.percent,
                )
            )
        return metrics

    def icon_text(self, metrics: list[Metric]) -> str:
        values = [m.percent for m in metrics if m.percent is not None]
        return f"{max(values):.0f}" if values else "-"

    def create_settings_widget(self) -> QWidget:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("Anzuzeigende Laufwerke (keine Auswahl = alle):"))
        lst = QListWidget()
        lst.setObjectName("drives")
        selected = set(self.settings.get("drives") or [])
        for drive in local_drives():
            item = QListWidgetItem(drive)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if drive in selected else Qt.CheckState.Unchecked)
            lst.addItem(item)
        layout.addWidget(lst)
        return widget

    def read_settings_widget(self, widget: QWidget) -> dict[str, Any]:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QListWidget

        lst = widget.findChild(QListWidget, "drives")
        drives = [
            lst.item(i).text()
            for i in range(lst.count())
            if lst.item(i).checkState() == Qt.CheckState.Checked
        ]
        return {"drives": drives}
