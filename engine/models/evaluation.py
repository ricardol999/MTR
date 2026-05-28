"""Validación walk-forward y métricas de error de pronóstico."""

from __future__ import annotations

import numpy as np

from engine.models.base import ForecastModel


def walk_forward(
    model: ForecastModel,
    prices: np.ndarray,
    horizon: int,
    n_splits: int,
    min_train: int,
) -> dict[str, float | int | None]:
    """Evalúa el modelo reentrenando en orígenes crecientes (sin look-ahead).

    En cada origen ``i`` se entrena con ``prices[:i]`` y se pronostica el precio
    en ``i-1+horizon``, comparándolo con el real. Devuelve MAE, RMSE, MAPE y
    precisión direccional.
    """
    last_origin = len(prices) - horizon
    if last_origin <= min_train:
        return {"mae": None, "rmse": None, "mape": None, "dir_acc": None, "n": 0}

    origins = list(range(min_train, last_origin + 1))
    if len(origins) > n_splits:
        idx = np.linspace(0, len(origins) - 1, n_splits).round().astype(int)
        origins = [origins[i] for i in dict.fromkeys(idx)]

    preds, actuals, bases = [], [], []
    for i in origins:
        train = prices[:i]
        try:
            pred = model.forecast(train, horizon)
        except Exception:  # noqa: BLE001 - un origen problemático no aborta todo
            continue
        if not np.isfinite(pred):
            continue
        preds.append(pred)
        actuals.append(float(prices[i - 1 + horizon]))
        bases.append(float(train[-1]))

    if not preds:
        return {"mae": None, "rmse": None, "mape": None, "dir_acc": None, "n": 0}

    preds_a = np.asarray(preds)
    actuals_a = np.asarray(actuals)
    bases_a = np.asarray(bases)
    err = preds_a - actuals_a

    mae = float(np.mean(np.abs(err)))
    rmse = float(np.sqrt(np.mean(err**2)))
    mape = float(np.mean(np.abs(err / actuals_a)))

    pred_dir = np.sign(preds_a - bases_a)
    actual_dir = np.sign(actuals_a - bases_a)
    mask = pred_dir != 0
    dir_acc = float(np.mean(pred_dir[mask] == actual_dir[mask])) if mask.any() else None

    return {
        "mae": mae,
        "rmse": rmse,
        "mape": mape,
        "dir_acc": dir_acc,
        "n": len(preds),
    }
