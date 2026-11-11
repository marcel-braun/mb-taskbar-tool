from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from math import isfinite
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


CRITICAL_PERCENT = 90


@dataclass(frozen=True)
class Metric:
    label: str
    value_text: str
    percent: float | None = None
    critical_percent: float = CRITICAL_PERCENT


class Feature(ABC):
    """Base class for all features. Subclasses register via @register_feature."""

    id: str = ""
    display_name: str = ""
    supports_threshold: bool = False

    def __init__(self) -> None:
        self.settings: dict[str, Any] = self.default_settings()

    def default_settings(self) -> dict[str, Any]:
        return {}

    def configure(self, settings: dict[str, Any]) -> None:
        self.settings = {**self.default_settings(), **settings}

    @property
    def alert_threshold(self) -> float:
        try:
            value = float(self.settings.get("alert_threshold", CRITICAL_PERCENT))
        except (TypeError, ValueError):
            return CRITICAL_PERCENT
        return max(0.0, min(100.0, value)) if isfinite(value) else CRITICAL_PERCENT

    @abstractmethod
    def update(self) -> list[Metric]:
        """Collect current values. Called periodically from the GUI thread, must be fast."""

    @abstractmethod
    def icon_text(self, metrics: list[Metric]) -> str:
        """Short text (max. ~3 chars) for the tray icon."""

    def create_settings_widget(self) -> QWidget | None:
        return None

    def read_settings_widget(self, widget: QWidget) -> dict[str, Any]:
        return {}
