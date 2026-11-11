from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from mbtaskbar import APP_NAME

log = logging.getLogger(__name__)

MIN_INTERVAL_MS = 500
MAX_INTERVAL_MS = 60_000


def default_config_path() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parents[3]
    return base / "config.json"


def legacy_config_path() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / APP_NAME / "config.json"


@dataclass
class AppConfig:
    icon_feature_id: str = "calendar_week"
    enabled_features: list[str] = field(
        default_factory=lambda: ["calendar_week", "cpu", "ram", "disk"]
    )
    update_interval_ms: int = 2000
    autostart: bool = False
    feature_settings: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.update_interval_ms = max(MIN_INTERVAL_MS, min(MAX_INTERVAL_MS, int(self.update_interval_ms)))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_config(path: Path | None = None) -> AppConfig:
    if path is None:
        path = default_config_path()
        if not path.exists():
            legacy_path = legacy_config_path()
            if legacy_path.exists():
                path = legacy_path
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("config root is not an object")
        return AppConfig.from_dict(data)
    except FileNotFoundError:
        return AppConfig()
    except (OSError, ValueError, TypeError) as exc:
        log.warning("Konfiguration %s ungültig, verwende Standardwerte: %s", path, exc)
        return AppConfig()


def save_config(config: AppConfig, path: Path | None = None) -> None:
    path = path or default_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)
