"""Agente de análisis técnico: calcula indicadores sobre el histórico."""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.core.agent import BaseAgent
from engine.core.context import MarketContext


def _rsi(close: pd.Series, window: int) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def _atr(df: pd.DataFrame, window: int) -> pd.Series:
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.ewm(alpha=1 / window, min_periods=window).mean()


class TechnicalAgent(BaseAgent):
    """Calcula SMA/EMA, RSI, MACD, Bandas de Bollinger y ATR.

    Deja las series como columnas en ``context.prices`` y un resumen del último
    valor en ``context.indicators``.
    """

    name = "TechnicalAgent"

    def run(self, context: MarketContext) -> MarketContext:
        df = context.require_prices()
        w = context.config.indicator_windows
        close = df["close"]

        df["sma_fast"] = close.rolling(w["sma_fast"]).mean()
        df["sma_slow"] = close.rolling(w["sma_slow"]).mean()
        df["ema"] = close.ewm(span=w["ema"], adjust=False).mean()
        df["rsi"] = _rsi(close, w["rsi"])

        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        bb_mid = close.rolling(w["bollinger"]).mean()
        bb_std = close.rolling(w["bollinger"]).std()
        df["bb_mid"] = bb_mid
        df["bb_upper"] = bb_mid + 2 * bb_std
        df["bb_lower"] = bb_mid - 2 * bb_std

        df["atr"] = _atr(df, w["atr"])
        df["log_return"] = np.log(close / close.shift(1))

        last = df.iloc[-1]
        context.indicators = {
            "close": float(last["close"]),
            "sma_fast": _f(last["sma_fast"]),
            "sma_slow": _f(last["sma_slow"]),
            "ema": _f(last["ema"]),
            "rsi": _f(last["rsi"]),
            "macd": _f(last["macd"]),
            "macd_signal": _f(last["macd_signal"]),
            "macd_hist": _f(last["macd_hist"]),
            "bb_upper": _f(last["bb_upper"]),
            "bb_lower": _f(last["bb_lower"]),
            "atr": _f(last["atr"]),
            "trend_up": bool(last["sma_fast"] > last["sma_slow"]),
        }
        context.note(
            self.name,
            f"RSI={_fmt(last['rsi'])} MACD_hist={_fmt(last['macd_hist'])} "
            f"tendencia={'alcista' if context.indicators['trend_up'] else 'bajista'}.",
        )
        return context


def _f(value: object) -> float | None:
    f = float(value)  # type: ignore[arg-type]
    return None if np.isnan(f) else f


def _fmt(value: object) -> str:
    f = float(value)  # type: ignore[arg-type]
    return "n/a" if np.isnan(f) else f"{f:.2f}"
