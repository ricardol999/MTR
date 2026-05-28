"""Ensambla el motor con la tubería estándar de agentes."""

from __future__ import annotations

from engine.agents import (
    BacktestAgent,
    DataAgent,
    ForecastAgent,
    RiskAgent,
    SignalAgent,
    TechnicalAgent,
)
from engine.config import EngineConfig
from engine.core.orchestrator import Engine


def build_engine(config: EngineConfig) -> Engine:
    """Crea el motor con los agentes en el orden de dependencia correcto."""
    return Engine(
        config,
        agents=[
            DataAgent(),
            TechnicalAgent(),
            ForecastAgent(),
            RiskAgent(),
            SignalAgent(),
            BacktestAgent(),
        ],
    )
