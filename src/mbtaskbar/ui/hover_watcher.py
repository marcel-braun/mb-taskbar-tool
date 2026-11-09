from __future__ import annotations

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QSystemTrayIcon

from mbtaskbar.ui.hover_popup import HoverPopup

POLL_MS = 120
SHOW_DELAY_MS = 250
HIDE_DELAY_MS = 350


class HoverWatcher(QObject):
    """QSystemTrayIcon has no hover signal, so the cursor is polled against the icon geometry."""

    def __init__(self, tray: QSystemTrayIcon, popup: HoverPopup, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tray = tray
        self._popup = popup
        self._hover_ms = 0
        self._away_ms = 0
        self._timer = QTimer(self, interval=POLL_MS)
        self._timer.timeout.connect(self._poll)

    def start(self) -> None:
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _poll(self) -> None:
        pos = QCursor.pos()
        icon_rect = self._tray.geometry()
        on_icon = icon_rect.isValid() and icon_rect.contains(pos)
        on_popup = self._popup.isVisible() and self._popup.frameGeometry().contains(pos)

        if on_icon or on_popup:
            self._away_ms = 0
            self._hover_ms += POLL_MS
            if on_icon and not self._popup.isVisible() and self._hover_ms >= SHOW_DELAY_MS:
                self._popup.show_at(icon_rect)
        else:
            self._hover_ms = 0
            if self._popup.isVisible():
                self._away_ms += POLL_MS
                if self._away_ms >= HIDE_DELAY_MS:
                    self._popup.hide()
