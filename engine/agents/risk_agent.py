"""Agente de gestión de riesgo: volatilidad, drawdown y dimensionamiento."""

from __future__ import annotations

import numpy as np

from engine.core.agent import BaseAgent
from engine.core.context import MarketContext


def _max_drawdown(equity: np.ndarray) -> float:
    running_max = np.maximum.accumulate(equity)
    drawdowns = equity / running_max - 1.0
    return float(drawdowns.min())


class RiskAgent(BaseAgent):
    """Cuantifica el riesgo y propone tamaño de posición y stop-loss.

    Usa un esquema de fracción fija: arriesga ``risk_per_trade`` del capital,
    con el stop a ``stop_loss_atr_mult`` ATR por debajo del precio actual.
    """

    name = "RiskAgent"

    def run(self, context: MarketContext) -> MarketContext:
        cfg = context.config
        df = context.require_prices()
        close = df["close"].to_numpy(dtype=float)
        last_price = float(close[-1])

        log_ret = np.diff(np.log(close))
        daily_vol = float(np.std(log_ret, ddof=1))
        annual_vol = daily_vol * np.sqrt(cfg.trading_days_per_year)
        max_dd = _max_drawdown(close)

        atr = context.indicators.get("atr")
        stop_distance = (
            cfg.stop_loss_atr_mult * atr
            if atr
            else cfg.stop_loss_atr_mult * daily_vol * last_price
        )
        stop_price = last_price - stop_distance

        risk_capital = cfg.initial_capital * cfg.risk_per_trade
        shares = int(risk_capital / stop_distance) if stop_distance > 0 else 0
        position_value = shares * last_price

        context.risk = {
            "daily_vol": daily_vol,
            "annual_vol": annual_vol,
            "max_drawdown": max_dd,
            "atr": atr,
            "stop_price": stop_price,
            "stop_distance": float(stop_distance),
            "suggested_shares": shares,
            "position_value": float(position_value),
            "risk_capital": float(risk_capital),
        }
        context.note(
            self.name,
            f"Vol anual={annual_vol * 100:.1f}% maxDD={max_dd * 100:.1f}% "
            f"stop={stop_price:.2f} tamaño={shares} acc.",
        )
        return context
