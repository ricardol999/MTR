"""Ensambla el motor con la tubería estándar de agentes."""

from __future__ import annotations

from engine.agents import (
    BacktestAgent,
    DataAgent,
    ForecastAgent,
    FundamentalAgent,
    RiskAgent,
    SignalAgent,
    TechnicalAgent,
)
from engine.config import EngineConfig
from engine.core.agent import BaseAgent
from engine.core.orchestrator import Engine


def build_engine(config: EngineConfig) -> Engine:
    """Crea el motor con los agentes en el orden de dependencia correcto."""
    agents: list[BaseAgent] = [DataAgent(), TechnicalAgent()]
    if config.enable_fundamentals:
        agents.append(FundamentalAgent())
    agents += [ForecastAgent(), RiskAgent(), SignalAgent(), BacktestAgent()]
    return Engine(config, agents=agents)
