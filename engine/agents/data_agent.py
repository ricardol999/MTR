"""Agente recolector: carga el histórico OHLCV en el contexto."""

from __future__ import annotations

from engine.core.agent import BaseAgent
from engine.core.context import MarketContext
from engine.data.cache import PriceCache
from engine.data.providers import get_provider


class DataAgent(BaseAgent):
    name = "DataAgent"

    def run(self, context: MarketContext) -> MarketContext:
        cfg = context.config
        cache = PriceCache(cfg.cache_path) if cfg.use_cache else None

        prices = None
        from_cache = False
        if cache is not None:
            prices = cache.get(
                cfg.symbol, cfg.source, cfg.period_days, cfg.cache_max_age_days
            )
            from_cache = prices is not None

        if prices is None:
            provider = get_provider(cfg.source, cfg.csv_path)
            prices = provider.get_history(cfg.symbol, cfg.period_days)
            if cache is not None:
                cache.put(cfg.symbol, cfg.source, prices)

        context.prices = prices
        origin = "caché" if from_cache else cfg.source
        context.note(
            self.name,
            f"{len(prices)} velas cargadas para {cfg.symbol} "
            f"({prices.index[0].date()} -> {prices.index[-1].date()}) "
            f"vía {origin}.",
        )
        return context
