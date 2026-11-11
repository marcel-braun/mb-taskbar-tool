from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QProgressBar, QVBoxLayout, QWidget

from mbtaskbar.core.feature import CRITICAL_PERCENT, Metric

STYLE = """
#card { background: #202020; border: 1px solid #3a3a3a; border-radius: 8px; }
QLabel { color: #e6e6e6; font: 9pt "Segoe UI"; }
QLabel[role="value"] { color: #ffffff; }
QProgressBar { background: #3a3a3a; border: none; border-radius: 2px; }
QProgressBar::chunk { background: #4cc2ff; border-radius: 2px; }
QProgressBar[level="warn"]::chunk { background: #ffb900; }
QProgressBar[level="crit"]::chunk { background: #ff4343; }
"""


def _level(percent: float, critical_percent: float = CRITICAL_PERCENT) -> str:
    if percent >= critical_percent:
        return "crit"
    if percent >= 75:
        return "warn"
    return "ok"


def popup_position(anchor: QRect, size: tuple[int, int], screen: QRect, margin: int = 8) -> QPoint:
    """Place the popup next to the tray icon, on the side facing the screen centre."""
    w, h = size
    x = anchor.center().x() - w // 2
    if anchor.center().y() > screen.center().y():
        y = min(anchor.top(), screen.bottom()) - h - margin
    else:
        y = max(anchor.bottom(), screen.top()) + margin
    x = max(screen.left() + margin, min(x, screen.right() - w - margin))
    y = max(screen.top() + margin, min(y, screen.bottom() - h - margin))
    return QPoint(x, y)


class HoverPopup(QWidget):
    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(STYLE)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame(objectName="card")
        outer.addWidget(card)
        self._grid = QGridLayout(card)
        self._grid.setContentsMargins(12, 10, 12, 10)
        self._grid.setHorizontalSpacing(10)
        self._grid.setVerticalSpacing(6)

        self._layout_key: tuple[str, ...] = ()
        self._rows: list[tuple[QLabel, QProgressBar, QLabel]] = []

    def set_metrics(self, metrics: list[Metric]) -> None:
        key = tuple(m.label for m in metrics)
        if key != self._layout_key:
            self._rebuild(metrics)
            self._layout_key = key
        for (label, bar, value), metric in zip(self._rows, metrics):
            label.setText(metric.label)
            value.setText(metric.value_text)
            if metric.percent is None:
                bar.hide()
            else:
                bar.show()
                bar.setValue(round(metric.percent))
                level = _level(metric.percent, metric.critical_percent)
                if bar.property("level") != level:
                    bar.setProperty("level", level)
                    bar.style().unpolish(bar)
                    bar.style().polish(bar)

    def _rebuild(self, metrics: list[Metric]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._rows.clear()
        for row, _ in enumerate(metrics):
            label = QLabel()
            bar = QProgressBar(textVisible=False, maximum=100)
            bar.setFixedSize(90, 6)
            value = QLabel()
            value.setProperty("role", "value")
            value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._grid.addWidget(label, row, 0)
            self._grid.addWidget(bar, row, 1)
            self._grid.addWidget(value, row, 2)
            self._rows.append((label, bar, value))
        self.adjustSize()

    def show_at(self, anchor: QRect) -> None:
        self.adjustSize()
        screen = QGuiApplication.screenAt(anchor.center()) or QGuiApplication.primaryScreen()
        self.move(popup_position(anchor, (self.width(), self.height()), screen.availableGeometry()))
        self.show()
        self.raise_()
