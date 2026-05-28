"""Agente de backtesting: valida la estrategia sobre el histórico.

Estrategia evaluada: estar largo cuando la SMA rápida cruza por encima de la
SMA lenta (cruce dorado) y en efectivo en caso contrario. Es deliberadamente
simple para servir de línea base reproducible.
"""

from __future__ import annotations

import numpy as np

from engine.core.agent import BaseAgent
from engine.core.context import MarketContext


class BacktestAgent(BaseAgent):
    name = "BacktestAgent"

    def run(self, context: MarketContext) -> MarketContext:
        cfg = context.config
        df = context.require_prices()

        if "sma_fast" not in df or "sma_slow" not in df:
            raise ValueError("BacktestAgent requiere indicadores (ejecuta TechnicalAgent).")

        data = df.dropna(subset=["sma_fast", "sma_slow"]).copy()
        # Posición del día siguiente para evitar mirar al futuro (sin look-ahead).
        position = (data["sma_fast"] > data["sma_slow"]).astype(float).shift(1).fillna(0.0)
        market_ret = data["close"].pct_change().fillna(0.0)
        strat_ret = position * market_ret

        equity = (1.0 + strat_ret).cumprod() * cfg.initial_capital
        buy_hold = (1.0 + market_ret).cumprod() * cfg.initial_capital

        total_return = float(equity.iloc[-1] / cfg.initial_capital - 1.0)
        bh_return = float(buy_hold.iloc[-1] / cfg.initial_capital - 1.0)

        ann = cfg.trading_days_per_year
        mean, std = strat_ret.mean(), strat_ret.std(ddof=1)
        sharpe = (
            float((mean - cfg.risk_free_rate / ann) / std * np.sqrt(ann))
            if std > 0
            else 0.0
        )

        eq = equity.to_numpy()
        max_dd = float((eq / np.maximum.accumulate(eq) - 1.0).min())

        trades = int((position.diff().abs() > 0).sum())
        wins = float((strat_ret[strat_ret != 0] > 0).mean()) if (strat_ret != 0).any() else 0.0

        context.backtest = {
            "strategy": "SMA crossover (golden cross)",
            "final_equity": float(equity.iloc[-1]),
            "total_return": total_return,
            "buy_hold_return": bh_return,
            "excess_return": total_return - bh_return,
            "sharpe": sharpe,
            "max_drawdown": max_dd,
            "trades": trades,
            "win_rate": wins,
            "bars": int(len(data)),
        }
        context.note(
            self.name,
            f"Retorno={total_return * 100:+.1f}% (B&H {bh_return * 100:+.1f}%) "
            f"Sharpe={sharpe:.2f} maxDD={max_dd * 100:.1f}% trades={trades}.",
        )
        return context
