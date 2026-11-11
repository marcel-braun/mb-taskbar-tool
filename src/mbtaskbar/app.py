from __future__ import annotations

import argparse
import getpass
import logging
import sys
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon

import mbtaskbar.features  # noqa: F401  (registers features)
from mbtaskbar import APP_NAME
from mbtaskbar.core.config import (
    AppConfig,
    default_config_path,
    legacy_config_path,
    load_config,
    save_config,
)
from mbtaskbar.core.feature import Feature, Metric
from mbtaskbar.core.registry import available_features, create_feature
from mbtaskbar.core.scheduler import Scheduler
from mbtaskbar.platform import autostart
from mbtaskbar.ui.settings_dialog import SettingsDialog
from mbtaskbar.ui.tray import TrayController

log = logging.getLogger(__name__)


def _application_icon() -> QIcon:
    bundle_dir = getattr(sys, "_MEIPASS", None)
    base = Path(bundle_dir) if bundle_dir else Path(__file__).resolve().parents[2]
    return QIcon(str(base / "assets" / "app.ico"))


class TaskbarApp(QObject):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config
        self._features: dict[str, Feature] = {fid: create_feature(fid) for fid in available_features()}
        self._scheduler = Scheduler(self)
        self._tray = TrayController(self)
        self._dialog: SettingsDialog | None = None

        self._scheduler.updated.connect(self._on_updated)
        self._tray.settings_requested.connect(self.open_settings)
        self._tray.about_requested.connect(self.show_about)
        self._tray.quit_requested.connect(QApplication.quit)

    def start(self, first_run: bool) -> None:
        self._apply_config()
        self._tray.show()
        if first_run:
            self._tray.show_message(
                APP_NAME,
                "Tipp: Symbol über Einstellungen → Personalisierung → Taskleiste → "
                "Andere Symbole der Taskleiste dauerhaft einblenden.",
            )

    def _icon_feature_id(self) -> str:
        fid = self._config.icon_feature_id
        return fid if fid in self._features else next(iter(self._features))

    def _apply_config(self) -> None:
        for fid, feature in self._features.items():
            feature.configure(self._config.feature_settings.get(fid, {}))

        active = [fid for fid in self._config.enabled_features if fid in self._features]
        icon_fid = self._icon_feature_id()
        if icon_fid not in active:
            active.append(icon_fid)

        self._scheduler.stop()
        self._scheduler.set_features([self._features[fid] for fid in active])
        self._scheduler.start(self._config.update_interval_ms)

    def _on_updated(self, results: dict[str, list[Metric]]) -> None:
        icon_fid = self._icon_feature_id()
        active = set(self._config.enabled_features) | {icon_fid}
        critical = [
            (metric.percent, fid)
            for fid, metrics in results.items()
            if fid in active and fid in self._features
            if self._features[fid].supports_threshold
            for metric in metrics
            if metric.percent is not None and metric.percent >= self._features[fid].alert_threshold
        ]
        if critical:
            _, icon_fid = max(critical, key=lambda item: item[0])
        icon_text = self._features[icon_fid].icon_text(results.get(icon_fid, []))
        popup_metrics = [
            replace(metric, critical_percent=self._features[fid].alert_threshold)
            for fid in self._config.enabled_features
            if fid in self._features
            for metric in results.get(fid, [])
        ]
        self._tray.update(icon_text, popup_metrics, alert=bool(critical))

    def open_settings(self) -> None:
        if self._dialog is not None:
            self._dialog.raise_()
            self._dialog.activateWindow()
            return
        self._dialog = SettingsDialog(self._config, self._features)
        self._dialog.applied.connect(self._on_settings_applied)
        self._dialog.finished.connect(self._on_dialog_closed)
        self._dialog.show()
        self._dialog.activateWindow()

    def show_about(self) -> None:
        QMessageBox.about(
            None,
            f"Über {APP_NAME}",
            f"{APP_NAME}\n\nMarcel Braun\nmail@marcelbraun.de",
        )

    def _on_dialog_closed(self) -> None:
        if self._dialog is not None:
            self._dialog.deleteLater()
        self._dialog = None

    def _on_settings_applied(self, config: AppConfig) -> None:
        if config.autostart != self._config.autostart:
            try:
                autostart.set_enabled(config.autostart)
            except OSError as exc:
                log.exception("Autostart konnte nicht gesetzt werden")
                QMessageBox.warning(None, APP_NAME, f"Autostart konnte nicht gesetzt werden:\n{exc}")
                config.autostart = autostart.is_enabled()
        self._config = config
        try:
            save_config(config)
        except OSError as exc:
            log.exception("Konfiguration konnte nicht gespeichert werden")
            QMessageBox.warning(None, APP_NAME, f"Konfiguration konnte nicht gespeichert werden:\n{exc}")
        self._apply_config()


def _acquire_single_instance(app: QApplication) -> QLocalServer | None:
    name = f"{APP_NAME}-{getpass.getuser()}"
    probe = QLocalSocket()
    probe.connectToServer(name)
    if probe.waitForConnected(200):
        return None
    QLocalServer.removeServer(name)
    server = QLocalServer(app)
    server.listen(name)
    return server


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--show-settings", action="store_true")
    args = parser.parse_args()

    app = QApplication([sys.argv[0]])
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(_application_icon())
    app.setQuitOnLastWindowClosed(False)

    server = _acquire_single_instance(app)
    if server is None:
        log.info("%s läuft bereits.", APP_NAME)
        return 0

    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, APP_NAME, "Kein Infobereich (System Tray) verfügbar.")
        return 1

    config_path = default_config_path()
    first_run = not config_path.exists() and not legacy_config_path().exists()
    config = load_config()
    if not config_path.exists():
        save_config(config, config_path)

    taskbar_app = TaskbarApp(config)
    taskbar_app.start(first_run)
    if args.show_settings:
        taskbar_app.open_settings()
    return app.exec()
