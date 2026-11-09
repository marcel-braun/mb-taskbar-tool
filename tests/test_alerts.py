from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from mbtaskbar import app
from mbtaskbar.core.config import AppConfig
from mbtaskbar.core.config import load_config, save_config
from mbtaskbar.core.feature import Metric
from mbtaskbar.ui import tray
from mbtaskbar.ui.icon_renderer import ICON_SIZE, render_text_icon
from mbtaskbar.ui.hover_popup import HoverPopup
from mbtaskbar.ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qapp():
    instance = QApplication.instance() or QApplication([])
    yield instance


@pytest.fixture
def taskbar(qapp, monkeypatch):
    monkeypatch.setattr(app, "TrayController", Mock())
    return app.TaskbarApp(AppConfig())


@pytest.mark.parametrize("percent, alert", [(75, False), (89.9, False), (90, True), (100, True)])
def test_threshold_switches_icon(taskbar, percent, alert):
    results = {"cpu": [Metric("CPU", f"{percent} %", percent)]}
    taskbar._on_updated(results)
    icon_text = taskbar._features["cpu" if alert else "calendar_week"].icon_text(
        results.get("cpu" if alert else "calendar_week", [])
    )
    taskbar._tray.update.assert_called_once_with(icon_text, results["cpu"], alert=alert)


def test_highest_critical_feature_wins(taskbar):
    results = {
        "cpu": [Metric("CPU", "91 %", 91)],
        "ram": [Metric("RAM", "97 %", 97)],
        "disk": [Metric("C:", "20 %", 20), Metric("D:", "99 %", 99)],
    }
    taskbar._on_updated(results)
    assert taskbar._tray.update.call_args.args[0] == "99"
    assert taskbar._tray.update.call_args.kwargs == {"alert": True}


def test_alarm_clears_and_restores_configured_icon(taskbar):
    taskbar._config.icon_feature_id = "ram"
    taskbar._on_updated({"cpu": [Metric("CPU", "95 %", 95)]})
    taskbar._on_updated({"cpu": [Metric("CPU", "40 %", 40)], "ram": [Metric("RAM", "50 %", 50)]})
    assert taskbar._tray.update.call_args.args[0] == "50"
    assert taskbar._tray.update.call_args.kwargs == {"alert": False}


def test_disabled_and_unknown_features_do_not_trigger_alarm(taskbar):
    taskbar._config.enabled_features = ["calendar_week"]
    taskbar._on_updated({"cpu": [Metric("CPU", "99 %", 99)], "unknown": [Metric("?", "100 %", 100)]})
    taskbar._tray.update.assert_called_once_with(
        taskbar._features["calendar_week"].icon_text([]), [], alert=False
    )


def test_configured_icon_triggers_alarm_even_outside_popup(taskbar):
    taskbar._config.enabled_features = ["calendar_week"]
    taskbar._config.icon_feature_id = "cpu"
    taskbar._on_updated({"cpu": [Metric("CPU", "90 %", 90)]})
    taskbar._tray.update.assert_called_once_with("90", [], alert=True)


def test_missing_percent_does_not_trigger_alarm(taskbar):
    taskbar._on_updated({"ram": [Metric("RAM", "unavailable")]})
    assert taskbar._tray.update.call_args.kwargs == {"alert": False}


@pytest.mark.parametrize("fid", ["cpu", "ram", "disk"])
@pytest.mark.parametrize("percent, alert", [(64.9, False), (65, True), (89, True)])
def test_individual_feature_threshold(taskbar, fid, percent, alert):
    taskbar._features[fid].configure({"alert_threshold": 65})
    taskbar._on_updated({fid: [Metric(fid, str(percent), percent)]})
    assert taskbar._tray.update.call_args.kwargs == {"alert": alert}
    assert taskbar._tray.update.call_args.args[1][0].critical_percent == 65


def test_thresholds_are_independent(taskbar):
    taskbar._features["cpu"].configure({"alert_threshold": 60})
    taskbar._features["ram"].configure({"alert_threshold": 95})
    taskbar._on_updated({
        "cpu": [Metric("CPU", "70 %", 70)],
        "ram": [Metric("RAM", "94 %", 94)],
    })
    assert taskbar._tray.update.call_args.args[0] == "70"
    assert taskbar._tray.update.call_args.kwargs == {"alert": True}


@pytest.mark.parametrize("threshold, expected", [(None, 90), ("bad", 90), (float("nan"), 90), (-1, 0), (101, 100)])
def test_invalid_thresholds_are_safe(taskbar, threshold, expected):
    feature = taskbar._features["cpu"]
    feature.configure({"alert_threshold": threshold})
    assert feature.alert_threshold == expected


def test_threshold_settings_roundtrip(taskbar, tmp_path, monkeypatch):
    monkeypatch.setattr("mbtaskbar.features.disk.local_drives", lambda: ["C:\\"])
    config = AppConfig(feature_settings={
        "cpu": {"alert_threshold": 61.5},
        "ram": {"alert_threshold": 82},
        "disk": {"alert_threshold": 97, "drives": ["C:\\"], "custom": True},
    })
    for fid, feature in taskbar._features.items():
        feature.configure(config.feature_settings.get(fid, {}))
    dialog = SettingsDialog(config, taskbar._features)
    assert set(dialog._threshold_inputs) == {"cpu", "ram", "disk"}
    assert dialog._threshold_inputs["cpu"].value() == 61.5
    assert dialog._threshold_inputs["ram"].value() == 82
    assert dialog._threshold_inputs["disk"].value() == 97
    dialog._threshold_inputs["cpu"].setValue(55.5)
    collected = dialog._collect()
    assert config.feature_settings["cpu"]["alert_threshold"] == 61.5
    assert collected.feature_settings["disk"]["drives"] == ["C:\\"]
    assert collected.feature_settings["disk"]["custom"] is True
    path = tmp_path / "config.json"
    save_config(collected, path)
    restored = load_config(path)
    assert restored.feature_settings["cpu"]["alert_threshold"] == 55.5
    assert restored.feature_settings["ram"]["alert_threshold"] == 82
    assert restored.feature_settings["disk"]["alert_threshold"] == 97
    taskbar._config = restored
    taskbar._apply_config()
    taskbar._scheduler.stop()
    assert taskbar._features["cpu"].alert_threshold == 55.5
    reopened = SettingsDialog(restored, taskbar._features)
    assert reopened._threshold_inputs["cpu"].value() == 55.5
    dialog.close()
    reopened.close()


def test_popup_uses_feature_threshold(qapp):
    popup = HoverPopup()
    popup.set_metrics([Metric("CPU", "65 %", 65, critical_percent=65)])
    assert popup._rows[0][1].property("level") == "crit"
    popup.set_metrics([Metric("CPU", "65 %", 65, critical_percent=95)])
    assert popup._rows[0][1].property("level") == "ok"
    popup.close()


@pytest.mark.parametrize("light_taskbar", [False, True])
@pytest.mark.parametrize("alert", [False, True])
def test_icon_color(qapp, light_taskbar, alert):
    image = render_text_icon("90", light_taskbar, alert=alert).pixmap(ICON_SIZE, ICON_SIZE).toImage()
    colors = [
        image.pixelColor(column, row)
        for row in range(image.height())
        for column in range(image.width())
        if image.pixelColor(column, row).alpha() == 255
    ]
    assert colors
    expected = "#ff4343" if alert else "#000000" if light_taskbar else "#ffffff"
    assert all(color.name() == expected for color in colors)


def test_tray_redraws_when_only_alert_changes(qapp, monkeypatch):
    monkeypatch.setattr(tray, "QSystemTrayIcon", Mock())
    monkeypatch.setattr(tray, "HoverPopup", Mock())
    monkeypatch.setattr(tray, "HoverWatcher", Mock())
    monkeypatch.setattr(tray, "taskbar_is_light", lambda: False)
    renderer = Mock()
    monkeypatch.setattr(tray, "render_text_icon", renderer)
    controller = tray.TrayController()
    renderer.reset_mock()
    controller.update("90", [], alert=False)
    controller.update("90", [], alert=True)
    controller.update("90", [], alert=True)
    controller.update("90", [], alert=False)
    assert renderer.call_count == 3
    assert [call.kwargs["alert"] for call in renderer.call_args_list] == [False, True, False]