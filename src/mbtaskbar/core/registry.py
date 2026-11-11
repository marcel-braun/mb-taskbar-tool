from __future__ import annotations

from typing import TypeVar

from mbtaskbar.core.feature import Feature

F = TypeVar("F", bound=type[Feature])

_registry: dict[str, type[Feature]] = {}


def register_feature(cls: F) -> F:
    if not cls.id:
        raise ValueError(f"{cls.__name__} has no id")
    if cls.id in _registry and _registry[cls.id] is not cls:
        raise ValueError(f"Duplicate feature id: {cls.id}")
    _registry[cls.id] = cls
    return cls


def available_features() -> dict[str, type[Feature]]:
    return dict(_registry)


def create_feature(feature_id: str) -> Feature:
    return _registry[feature_id]()
