"""Clase base de los agentes del motor."""

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.core.context import MarketContext


class BaseAgent(ABC):
    """Un agente recibe el contexto, hace su trabajo y devuelve el contexto.

    Cada agente es responsable de una capacidad acotada (datos, técnico,
    pronóstico, riesgo, señal, backtest) y no conoce a los demás: solo lee y
    escribe en el ``MarketContext``.
    """

    #: Nombre legible usado en la bitácora.
    name: str = "agent"

    @abstractmethod
    def run(self, context: MarketContext) -> MarketContext:
        """Procesa el contexto y lo devuelve enriquecido."""
        raise NotImplementedError

    def __call__(self, context: MarketContext) -> MarketContext:
        return self.run(context)
