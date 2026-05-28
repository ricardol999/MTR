"""Estado compartido entre agentes (patrón blackboard)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from engine.config import EngineConfig


@dataclass
class MarketContext:
    """Pizarra compartida que cada agente lee y enriquece en secuencia.

    Los agentes se comunican únicamente a través de este objeto: leen lo que
    necesitan y depositan sus resultados para los agentes posteriores.
    """

    config: EngineConfig

    # OHLCV histórico, indexado por fecha. Lo llena DataAgent.
    prices: pd.DataFrame | None = None

    # Resultados producidos por cada agente.
    indicators: dict[str, Any] = field(default_factory=dict)
    fundamentals: dict[str, Any] = field(default_factory=dict)
    forecast: dict[str, Any] = field(default_factory=dict)
    risk: dict[str, Any] = field(default_factory=dict)
    signal: dict[str, Any] = field(default_factory=dict)
    backtest: dict[str, Any] = field(default_factory=dict)

    # Bitácora de la corrida: cada agente añade una entrada.
    log: list[str] = field(default_factory=list)

    def note(self, agent: str, message: str) -> None:
        self.log.append(f"[{agent}] {message}")

    @property
    def symbol(self) -> str:
        return self.config.symbol

    def require_prices(self) -> pd.DataFrame:
        if self.prices is None or self.prices.empty:
            raise ValueError(
                "No hay datos de precios en el contexto. "
                "Asegúrate de que DataAgent se ejecute primero."
            )
        return self.prices
