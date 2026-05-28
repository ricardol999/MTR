"""Registro de modelos y detección de dependencias opcionales."""

from __future__ import annotations

import importlib.util
from collections.abc import Iterable

from engine.models.base import ForecastModel
from engine.models.classical import (
    ArimaModel,
    DriftModel,
    HoltLinearModel,
    LinearTrendModel,
)
from engine.models.ml import ARRidgeModel, GradientBoostingModel

_MODEL_CLASSES: dict[str, type[ForecastModel]] = {
    cls.name: cls
    for cls in (
        DriftModel,
        LinearTrendModel,
        HoltLinearModel,
        ARRidgeModel,
        ArimaModel,
        GradientBoostingModel,
    )
}


def _deps_available(cls: type[ForecastModel]) -> bool:
    return all(importlib.util.find_spec(dep) is not None for dep in cls.requires)


def available_model_names() -> list[str]:
    """Modelos cuyas dependencias están instaladas, en orden de registro."""
    return [name for name, cls in _MODEL_CLASSES.items() if _deps_available(cls)]


def build_models(names: Iterable[str] | None = None) -> list[ForecastModel]:
    """Instancia los modelos pedidos (o todos los disponibles si ``names`` es None).

    Si se piden modelos explícitos, los que tengan dependencias ausentes se
    omiten silenciosamente; un nombre desconocido lanza error.
    """
    if names is None:
        return [_MODEL_CLASSES[name]() for name in available_model_names()]

    models: list[ForecastModel] = []
    for name in names:
        if name not in _MODEL_CLASSES:
            raise ValueError(f"Modelo desconocido: {name!r}")
        cls = _MODEL_CLASSES[name]
        if _deps_available(cls):
            models.append(cls())
    return models
