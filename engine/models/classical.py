"""Modelos clásicos: deriva, tendencia lineal, Holt y ARIMA (opcional)."""

from __future__ import annotations

import warnings

import numpy as np

from engine.models.base import ForecastModel


class DriftModel(ForecastModel):
    """Random walk con deriva: extrapola la deriva media de los log-retornos."""

    name = "drift"

    def forecast(self, prices: np.ndarray, horizon: int) -> float:
        log_ret = np.diff(np.log(prices))
        mu = float(np.mean(log_ret))
        return float(prices[-1] * np.exp(mu * horizon))


class LinearTrendModel(ForecastModel):
    """Regresión lineal del log-precio sobre el tiempo (tendencia)."""

    name = "linear"

    def __init__(self, lookback: int = 120):
        self.lookback = lookback

    def forecast(self, prices: np.ndarray, horizon: int) -> float:
        lb = min(self.lookback, len(prices))
        y = np.log(prices[-lb:])
        x = np.arange(lb, dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        return float(np.exp(intercept + slope * (lb - 1 + horizon)))


class HoltLinearModel(ForecastModel):
    """Suavizado exponencial doble (Holt) sobre el log-precio.

    Ajusta nivel y tendencia; los parámetros alpha/beta se eligen por búsqueda
    en rejilla minimizando el error de un paso.
    """

    name = "holt"

    _ALPHAS = (0.1, 0.3, 0.5, 0.7, 0.9)
    _BETAS = (0.05, 0.1, 0.3, 0.5)

    @staticmethod
    def _smooth(y: np.ndarray, alpha: float, beta: float) -> tuple[float, float, float]:
        level = float(y[0])
        trend = float(y[1] - y[0])
        sse = 0.0
        for t in range(1, len(y)):
            forecast = level + trend
            sse += (y[t] - forecast) ** 2
            prev_level = level
            level = alpha * y[t] + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
        return level, trend, sse

    def forecast(self, prices: np.ndarray, horizon: int) -> float:
        y = np.log(prices)
        best: tuple[float, float, float] | None = None
        for alpha in self._ALPHAS:
            for beta in self._BETAS:
                level, trend, sse = self._smooth(y, alpha, beta)
                if best is None or sse < best[0]:
                    best = (sse, level, trend)
        assert best is not None
        _, level, trend = best
        return float(np.exp(level + trend * horizon))


class ArimaModel(ForecastModel):
    """ARIMA sobre el log-precio (requiere statsmodels)."""

    name = "arima"
    requires = ("statsmodels",)

    def __init__(self, order: tuple[int, int, int] = (2, 1, 1)):
        self.order = order

    def forecast(self, prices: np.ndarray, horizon: int) -> float:
        from statsmodels.tsa.arima.model import ARIMA

        y = np.log(prices)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                result = ARIMA(y, order=self.order).fit()
                fc = np.asarray(result.forecast(steps=horizon))
            except Exception:  # noqa: BLE001 - modelo no convergió: cae a naive
                return float(prices[-1])
        return float(np.exp(fc[-1]))
