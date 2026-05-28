"""Agente recolector: carga el histórico OHLCV en el contexto."""

from __future__ import annotations

from engine.core.agent import BaseAgent
from engine.core.context import MarketContext
from engine.data.providers import get_provider


class DataAgent(BaseAgent):
    name = "DataAgent"

    def run(self, context: MarketContext) -> MarketContext:
        cfg = context.config
        provider = get_provider(cfg.source, cfg.csv_path)
        prices = provider.get_history(cfg.symbol, cfg.period_days)
        context.prices = prices
        context.note(
            self.name,
            f"{len(prices)} velas cargadas para {cfg.symbol} "
            f"({prices.index[0].date()} -> {prices.index[-1].date()}) "
            f"vía {cfg.source}.",
        )
        return context
