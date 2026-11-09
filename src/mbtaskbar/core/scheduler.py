from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal

from mbtaskbar.core.feature import Feature, Metric

log = logging.getLogger(__name__)


class Scheduler(QObject):
    updated = Signal(dict)  # dict[str, list[Metric]]

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._features: list[Feature] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.tick)

    def set_features(self, features: list[Feature]) -> None:
        self._features = list(features)

    def start(self, interval_ms: int) -> None:
        self._timer.start(interval_ms)
        self.tick()

    def stop(self) -> None:
        self._timer.stop()

    def tick(self) -> None:
        results: dict[str, list[Metric]] = {}
        for feature in self._features:
            try:
                results[feature.id] = feature.update()
            except Exception:
                log.exception("Update von %s fehlgeschlagen", feature.id)
                results[feature.id] = [Metric(feature.display_name, "Fehler")]
        self.updated.emit(results)
