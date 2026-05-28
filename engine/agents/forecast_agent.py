"""Agente pronosticador multi-modelo con selección por walk-forward.

Ejecuta varios modelos (deriva, tendencia lineal, Holt, autorregresivo y, si
están instalados, ARIMA y gradient boosting), los evalúa con validación
walk-forward y elige el de menor RMSE como pronóstico principal. También
calcula un ensamble ponderado por el inverso del error.
"""

from __future__ import annotations

import numpy as np

from engine.core.agent import BaseAgent
from engine.core.context import MarketContext
from engine.models import build_models, walk_forward


class ForecastAgent(BaseAgent):
    name = "ForecastAgent"

    def run(self, context: MarketContext) -> MarketContext:
        cfg = context.config
        df = context.require_prices()
        horizon = cfg.forecast_horizon
        close = df["close"].to_numpy(dtype=float)
        last_price = float(close[-1])

        sigma = float(np.std(np.diff(np.log(close)), ddof=1))

        models = build_models(cfg.forecast_models)
        results: dict[str, dict] = {}
        for model in models:
            metrics = walk_forward(
                model,
                close,
                horizon,
                cfg.walk_forward_splits,
                cfg.walk_forward_min_train,
            )
            point = model.forecast(close, horizon)
            results[model.name] = {"forecast": float(point), **metrics}

        scored = [(r["rmse"], n) for n, r in results.items() if r["rmse"] is not None]
        best_name = min(scored)[1] if scored else next(iter(results))
        point = results[best_name]["forecast"]

        ensemble = self._ensemble(results)
        expected_return = point / last_price - 1.0
        band = 1.96 * sigma * np.sqrt(horizon) * last_price

        context.forecast = {
            "horizon_days": horizon,
            "last_price": last_price,
            "point": float(point),
            "best_model": best_name,
            "ensemble": ensemble,
            "expected_return": float(expected_return),
            "lower_95": float(point - band),
            "upper_95": float(point + band),
            "daily_vol": sigma,
            "models": results,
        }
        wf = results[best_name]
        rmse_txt = f"{wf['rmse']:.2f}" if wf["rmse"] is not None else "n/a"
        context.note(
            self.name,
            f"Mejor modelo={best_name} (RMSE {rmse_txt}) "
            f"pronóstico {horizon}d={point:.2f} ({expected_return * 100:+.2f}%).",
        )
        return context

    @staticmethod
    def _ensemble(results: dict[str, dict]) -> float | None:
        weighted, total = 0.0, 0.0
        for r in results.values():
            rmse = r["rmse"]
            if rmse is not None and rmse > 0:
                w = 1.0 / rmse
                weighted += w * r["forecast"]
                total += w
        if total > 0:
            return float(weighted / total)
        forecasts = [r["forecast"] for r in results.values()]
        return float(np.mean(forecasts)) if forecasts else None
