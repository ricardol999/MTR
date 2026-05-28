"""Orquestador que ejecuta la tubería de agentes en orden."""

from __future__ import annotations

from collections.abc import Iterable

from engine.config import EngineConfig
from engine.core.agent import BaseAgent
from engine.core.context import MarketContext


class Engine:
    """Coordina la ejecución secuencial de los agentes.

    El orden importa: cada agente depende de lo que dejaron los anteriores
    (datos -> indicadores -> pronóstico -> riesgo -> señal -> backtest).
    """

    def __init__(self, config: EngineConfig, agents: Iterable[BaseAgent]):
        self.config = config
        self.agents = list(agents)

    def run(self) -> MarketContext:
        context = MarketContext(config=self.config)
        for agent in self.agents:
            try:
                context = agent.run(context)
            except Exception as exc:  # noqa: BLE001 - se registra y se propaga
                context.note(agent.name, f"ERROR: {exc}")
                raise
        return context
