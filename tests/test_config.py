from pathlib import Path

from mbtaskbar.core import config as config_module
from mbtaskbar.core.config import (
    MAX_INTERVAL_MS,
    MIN_INTERVAL_MS,
    AppConfig,
    default_config_path,
    load_config,
    save_config,
)


def test_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "sub" / "config.json"
    cfg = AppConfig(icon_feature_id="cpu", enabled_features=["ram"], update_interval_ms=5000,
                    autostart=True, feature_settings={"disk": {"drives": ["C:\\"]}})
    save_config(cfg, path)
    assert load_config(path) == cfg


def test_missing_file_gives_defaults(tmp_path: Path) -> None:
    assert load_config(tmp_path / "nope.json") == AppConfig()


def test_corrupt_file_gives_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{ not json", encoding="utf-8")
    assert load_config(path) == AppConfig()


def test_non_object_root_gives_defaults(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    path.write_text("[1, 2]", encoding="utf-8")
    assert load_config(path) == AppConfig()


def test_unknown_keys_ignored() -> None:
    cfg = AppConfig.from_dict({"icon_feature_id": "ram", "foo": 1})
    assert cfg.icon_feature_id == "ram"


def test_interval_clamped() -> None:
    assert AppConfig(update_interval_ms=1).update_interval_ms == MIN_INTERVAL_MS
    assert AppConfig(update_interval_ms=10**9).update_interval_ms == MAX_INTERVAL_MS


def test_frozen_config_is_stored_beside_executable(tmp_path: Path, monkeypatch) -> None:
    executable = tmp_path / "MbTaskbarTool.exe"
    monkeypatch.setattr(config_module.sys, "frozen", True, raising=False)
    monkeypatch.setattr(config_module.sys, "executable", str(executable))

    assert default_config_path() == tmp_path / "config.json"


def test_load_config_falls_back_to_legacy_path(tmp_path: Path, monkeypatch) -> None:
    local_path = tmp_path / "program" / "config.json"
    legacy_path = tmp_path / "appdata" / "config.json"
    save_config(AppConfig(icon_feature_id="cpu"), legacy_path)
    monkeypatch.setattr(config_module, "default_config_path", lambda: local_path)
    monkeypatch.setattr(config_module, "legacy_config_path", lambda: legacy_path)

    assert load_config().icon_feature_id == "cpu"
