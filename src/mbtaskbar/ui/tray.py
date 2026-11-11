from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from mbtaskbar.core.feature import Metric
from mbtaskbar.ui.hover_popup import HoverPopup
from mbtaskbar.ui.hover_watcher import HoverWatcher
from mbtaskbar.ui.icon_renderer import render_text_icon, taskbar_is_light


class TrayController(QObject):
    settings_requested = Signal()
    about_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(render_text_icon("…"))
        self._popup = HoverPopup()
        self._watcher = HoverWatcher(self._tray, self._popup, self)
        self._last_icon_key: tuple[str, bool, bool] | None = None

        menu = QMenu()
        settings_action = QAction("Einstellungen…", menu)
        settings_action.triggered.connect(self.settings_requested)
        about_action = QAction("Über…", menu)
        about_action.triggered.connect(self.about_requested)
        quit_action = QAction("Beenden", menu)
        quit_action.triggered.connect(self.quit_requested)
        menu.addAction(settings_action)
        menu.addAction(about_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self._menu = menu
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_activated)

    def show(self) -> None:
        self._tray.show()
        self._watcher.start()

    def hide(self) -> None:
        self._watcher.stop()
        self._popup.hide()
        self._tray.hide()

    def show_message(self, title: str, text: str) -> None:
        self._tray.showMessage(title, text, QSystemTrayIcon.MessageIcon.Information, 8000)

    def update(self, icon_text: str, metrics: list[Metric], *, alert: bool = False) -> None:
        key = (icon_text, taskbar_is_light(), alert)
        if key != self._last_icon_key:
            self._tray.setIcon(render_text_icon(icon_text, key[1], alert=alert))
            self._last_icon_key = key
        self._popup.set_metrics(metrics)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        # Click toggles the popup as fallback when the icon sits in the overflow area
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self._popup.isVisible():
                self._popup.hide()
            else:
                self._popup.show_at(self._tray.geometry())
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.settings_requested.emit()
