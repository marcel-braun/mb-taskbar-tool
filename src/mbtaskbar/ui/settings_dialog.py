from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from mbtaskbar.core.config import MAX_INTERVAL_MS, MIN_INTERVAL_MS, AppConfig
from mbtaskbar.core.feature import Feature


class SettingsDialog(QDialog):
    applied = Signal(object)  # AppConfig

    def __init__(self, config: AppConfig, features: dict[str, Feature], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("MbTaskbarTool – Einstellungen")
        self.setMinimumWidth(420)
        self._config = config
        self._features = features
        self._feature_pages: dict[str, QWidget] = {}
        self._threshold_inputs: dict[str, QDoubleSpinBox] = {}

        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), "Allgemein")
        tabs.addTab(self._build_features_tab(), "Features")
        tabs.addTab(self._build_thresholds_tab(), "Schwellenwerte")
        for fid, feature in features.items():
            page = feature.create_settings_widget()
            if page is not None:
                self._feature_pages[fid] = page
                tabs.addTab(page, feature.display_name)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

    def _build_general_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)

        self._icon_combo = QComboBox()
        for fid, feature in self._features.items():
            self._icon_combo.addItem(feature.display_name, fid)
        idx = self._icon_combo.findData(self._config.icon_feature_id)
        self._icon_combo.setCurrentIndex(max(idx, 0))
        form.addRow("Symbol in der Taskleiste:", self._icon_combo)

        self._interval = QDoubleSpinBox(suffix=" s", decimals=1, singleStep=0.5)
        self._interval.setRange(MIN_INTERVAL_MS / 1000, MAX_INTERVAL_MS / 1000)
        self._interval.setValue(self._config.update_interval_ms / 1000)
        form.addRow("Aktualisierungsintervall:", self._interval)

        self._autostart = QCheckBox("Mit Windows starten")
        self._autostart.setChecked(self._config.autostart)
        form.addRow("", self._autostart)
        return page

    def _build_features_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Im Hover-Fenster anzeigen (Reihenfolge per Drag && Drop):"))
        self._feature_list = QListWidget()
        self._feature_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        enabled = [fid for fid in self._config.enabled_features if fid in self._features]
        ordered = enabled + [fid for fid in self._features if fid not in enabled]
        for fid in ordered:
            item = QListWidgetItem(self._features[fid].display_name)
            item.setData(Qt.ItemDataRole.UserRole, fid)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if fid in enabled else Qt.CheckState.Unchecked)
            self._feature_list.addItem(item)
        layout.addWidget(self._feature_list)
        return page

    def _build_thresholds_tab(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        for fid, feature in self._features.items():
            if not feature.supports_threshold:
                continue
            threshold = QDoubleSpinBox(suffix=" %", decimals=1, singleStep=1.0)
            threshold.setObjectName(f"threshold_{fid}")
            threshold.setRange(0, 100)
            threshold.setValue(feature.alert_threshold)
            self._threshold_inputs[fid] = threshold
            form.addRow(f"{feature.display_name}:", threshold)
        return page

    def _collect(self) -> AppConfig:
        enabled = []
        for i in range(self._feature_list.count()):
            item = self._feature_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                enabled.append(item.data(Qt.ItemDataRole.UserRole))

        feature_settings = {
            fid: dict(settings) for fid, settings in self._config.feature_settings.items()
        }
        for fid, page in self._feature_pages.items():
            feature_settings.setdefault(fid, {}).update(self._features[fid].read_settings_widget(page))
        for fid, threshold in self._threshold_inputs.items():
            feature_settings.setdefault(fid, {})["alert_threshold"] = threshold.value()

        return replace(
            self._config,
            icon_feature_id=self._icon_combo.currentData(),
            enabled_features=enabled,
            update_interval_ms=round(self._interval.value() * 1000),
            autostart=self._autostart.isChecked(),
            feature_settings=feature_settings,
        )

    def _apply(self) -> None:
        self._config = self._collect()
        self.applied.emit(self._config)

    def _on_ok(self) -> None:
        self._apply()
        self.accept()
