"""Agente pronosticador: proyecta el precio en el horizonte configurado.

Combina dos modelos simples y robustos (sin dependencias de ML pesadas):

* **Drift** sobre log-retornos (deriva media histórica).
* **Tendencia lineal** (regresión por mínimos cuadrados sobre el tiempo).

El pronóstico final es el promedio de ambos. Se reporta un intervalo de
confianza aproximado a partir de la volatilidad de los retornos.
"""

from __future__ import annotations

import numpy as np

from engine.core.agent import BaseAgent
from engine.core.context import MarketContext


class ForecastAgent(BaseAgent):
    name = "ForecastAgent"

    def run(self, context: MarketContext) -> MarketContext:
        df = context.require_prices()
        horizon = context.config.forecast_horizon
        close = df["close"].to_numpy(dtype=float)
        last_price = float(close[-1])

        log_close = np.log(close)
        log_ret = np.diff(log_close)
        mu = float(np.mean(log_ret))
        sigma = float(np.std(log_ret, ddof=1))

        drift_forecast = last_price * np.exp(mu * horizon)

        # Tendencia lineal sobre los últimos min(120, n) puntos.
        lookback = min(120, len(close))
        y = log_close[-lookback:]
        x = np.arange(lookback, dtype=float)
        slope, intercept = np.polyfit(x, y, 1)
        trend_forecast = float(np.exp(intercept + slope * (lookback - 1 + horizon)))

        point = 0.5 * (drift_forecast + trend_forecast)
        expected_return = point / last_price - 1.0

        # Banda ~95% asumiendo difusión de la volatilidad diaria.
        band = 1.96 * sigma * np.sqrt(horizon) * last_price

        context.forecast = {
            "horizon_days": horizon,
            "last_price": last_price,
            "point": float(point),
            "drift_model": float(drift_forecast),
            "trend_model": trend_forecast,
            "expected_return": float(expected_return),
            "lower_95": float(point - band),
            "upper_95": float(point + band),
            "daily_vol": sigma,
        }
        context.note(
            self.name,
            f"Pronóstico {horizon}d: {point:.2f} "
            f"({expected_return * 100:+.2f}%) "
            f"[{point - band:.2f}, {point + band:.2f}].",
        )
        return context
