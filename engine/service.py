"""Fachada de alto nivel del motor.

Centraliza la ejecución y la serialización para que CLI, API y scheduler
compartan exactamente la misma lógica y formato de salida.
"""

from __future__ import annotations

from typing import Any

from engine.config import EngineConfig
from engine.core.context import MarketContext
from engine.factory import build_engine


def context_to_dict(ctx: MarketContext) -> dict[str, Any]:
    """Serializa el contexto a un dict JSON-friendly."""
    return {
        "symbol": ctx.symbol,
        "indicators": ctx.indicators,
        "fundamentals": ctx.fundamentals,
        "forecast": ctx.forecast,
        "risk": ctx.risk,
        "signal": ctx.signal,
        "backtest": ctx.backtest,
        "log": ctx.log,
    }


def run_analysis(config: EngineConfig) -> dict[str, Any]:
    """Ejecuta el pipeline completo y devuelve el resultado serializado."""
    ctx = build_engine(config).run()
    return context_to_dict(ctx)


def signal_summary(config: EngineConfig) -> dict[str, Any]:
    """Versión compacta: solo señal + pronóstico (para alertas y listas)."""
    result = run_analysis(config)
    fc = result["forecast"]
    return {
        "symbol": result["symbol"],
        "action": result["signal"]["action"],
        "score": result["signal"]["score"],
        "confidence": result["signal"]["confidence"],
        "last_price": fc["last_price"],
        "forecast": fc["point"],
        "expected_return": fc["expected_return"],
        "best_model": fc["best_model"],
        "horizon_days": fc["horizon_days"],
    }
