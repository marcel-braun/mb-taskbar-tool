import pytest

from mbtaskbar.core.feature import Feature, Metric
from mbtaskbar.core.registry import available_features, create_feature, register_feature
import mbtaskbar.features  # noqa: F401


def test_builtin_features_registered() -> None:
    assert {"calendar_week", "cpu", "ram", "disk"} <= set(available_features())


def test_create_feature() -> None:
    assert create_feature("ram").id == "ram"


def test_duplicate_id_rejected() -> None:
    with pytest.raises(ValueError):
        @register_feature
        class Dup(Feature):
            id = "cpu"

            def update(self) -> list[Metric]:
                return []

            def icon_text(self, metrics: list[Metric]) -> str:
                return ""


def test_configure_merges_defaults() -> None:
    disk = create_feature("disk")
    disk.configure({"other": 1})
    assert disk.settings == {"drives": [], "other": 1}
