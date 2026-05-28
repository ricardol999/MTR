"""Modelos de aprendizaje sobre log-retornos rezagados.

Ambos predicen el siguiente log-retorno a partir de ``lags`` retornos previos y
luego iteran ``horizon`` pasos para componer el precio. ``ARRidgeModel`` usa
numpy puro; ``GradientBoostingModel`` requiere scikit-learn.
"""

from __future__ import annotations

import numpy as np

from engine.models.base import ForecastModel


def _lag_matrix(returns: np.ndarray, lags: int) -> tuple[np.ndarray, np.ndarray]:
    rows_x, rows_y = [], []
    for t in range(lags, len(returns)):
        rows_x.append(returns[t - lags : t][::-1])  # [r_{t-1}, ..., r_{t-lags}]
        rows_y.append(returns[t])
    return np.asarray(rows_x), np.asarray(rows_y)


def _compose(log_last: float, recent: list[float], lags: int, horizon: int, step) -> float:
    history = list(recent)
    log_price = log_last
    for _ in range(horizon):
        feat = np.asarray(history[-lags:][::-1])
        pred = step(feat)
        log_price += pred
        history.append(pred)
    return float(np.exp(log_price))


class ARRidgeModel(ForecastModel):
    """Autorregresivo lineal con regularización ridge (numpy puro)."""

    name = "ar"

    def __init__(self, lags: int = 5, l2: float = 1e-3):
        self.lags = lags
        self.l2 = l2

    def forecast(self, prices: np.ndarray, horizon: int) -> float:
        log_price = np.log(prices)
        returns = np.diff(log_price)
        if len(returns) <= self.lags + 2:
            return float(prices[-1])

        x, y = _lag_matrix(returns, self.lags)
        xb = np.column_stack([np.ones(len(x)), x])
        gram = xb.T @ xb + self.l2 * np.eye(xb.shape[1])
        coef = np.linalg.solve(gram, xb.T @ y)

        def step(feat: np.ndarray) -> float:
            return float(np.concatenate([[1.0], feat]) @ coef)

        return _compose(
            float(log_price[-1]), list(returns[-self.lags :]), self.lags, horizon, step
        )


class GradientBoostingModel(ForecastModel):
    """Gradient boosting sobre retornos rezagados (requiere scikit-learn)."""

    name = "gbr"
    requires = ("sklearn",)

    def __init__(self, lags: int = 5):
        self.lags = lags

    def forecast(self, prices: np.ndarray, horizon: int) -> float:
        from sklearn.ensemble import GradientBoostingRegressor

        log_price = np.log(prices)
        returns = np.diff(log_price)
        if len(returns) <= self.lags + 10:
            return float(prices[-1])

        x, y = _lag_matrix(returns, self.lags)
        model = GradientBoostingRegressor(
            n_estimators=100, max_depth=3, learning_rate=0.05, random_state=0
        )
        model.fit(x, y)

        def step(feat: np.ndarray) -> float:
            return float(model.predict(feat.reshape(1, -1))[0])

        return _compose(
            float(log_price[-1]), list(returns[-self.lags :]), self.lags, horizon, step
        )
