"""Proveedores de datos fundamentales por símbolo.

Devuelven un diccionario de métricas normalizadas:
    pe, pb, ps, roe, debt_to_equity, profit_margin, revenue_growth,
    dividend_yield, market_cap

Valores ``None`` significan "no disponible".
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from engine.data.providers import stable_seed

FUNDAMENTAL_FIELDS = [
    "pe",
    "pb",
    "ps",
    "roe",
    "debt_to_equity",
    "profit_margin",
    "revenue_growth",
    "dividend_yield",
    "market_cap",
]


class FundamentalsProvider(ABC):
    @abstractmethod
    def get_fundamentals(self, symbol: str) -> dict[str, float | None]:
        raise NotImplementedError


class SyntheticFundamentalsProvider(FundamentalsProvider):
    """Genera fundamentales plausibles y deterministas por símbolo (offline)."""

    def get_fundamentals(self, symbol: str) -> dict[str, float | None]:
        rng = np.random.default_rng(stable_seed(f"fund:{symbol}"))
        return {
            "pe": round(float(rng.uniform(8, 40)), 2),
            "pb": round(float(rng.uniform(0.8, 12)), 2),
            "ps": round(float(rng.uniform(0.5, 15)), 2),
            "roe": round(float(rng.uniform(-0.05, 0.4)), 4),
            "debt_to_equity": round(float(rng.uniform(0.0, 2.5)), 2),
            "profit_margin": round(float(rng.uniform(-0.1, 0.35)), 4),
            "revenue_growth": round(float(rng.uniform(-0.15, 0.4)), 4),
            "dividend_yield": round(float(rng.uniform(0.0, 0.05)), 4),
            "market_cap": float(rng.integers(1, 2500) * 1_000_000_000),
        }


class YFinanceFundamentalsProvider(FundamentalsProvider):
    """Obtiene fundamentales reales con yfinance (requiere internet)."""

    def get_fundamentals(self, symbol: str) -> dict[str, float | None]:
        try:
            import yfinance as yf
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "yfinance no está instalado. Ejecuta: pip install yfinance"
            ) from exc

        # .info es propenso a fallos/datos parciales; nunca debe tumbar el análisis.
        try:
            info = yf.Ticker(symbol).info or {}
        except Exception:  # noqa: BLE001
            info = {}

        # debtToEquity de yfinance viene en porcentaje (p. ej. 150 = 1.5x).
        raw_de = info.get("debtToEquity")
        debt_to_equity = (
            float(raw_de) / 100.0 if isinstance(raw_de, (int, float)) else None
        )

        def g(key: str) -> float | None:
            value = info.get(key)
            return float(value) if isinstance(value, (int, float)) else None

        return {
            "pe": g("trailingPE"),
            "pb": g("priceToBook"),
            "ps": g("priceToSalesTrailing12Months"),
            "roe": g("returnOnEquity"),
            "debt_to_equity": debt_to_equity,
            "profit_margin": g("profitMargins"),
            "revenue_growth": g("revenueGrowth"),
            "dividend_yield": g("dividendYield"),
            "market_cap": g("marketCap"),
        }


def get_fundamentals_provider(source: str) -> FundamentalsProvider:
    source = source.lower()
    if source == "synthetic":
        return SyntheticFundamentalsProvider()
    if source == "yfinance":
        return YFinanceFundamentalsProvider()
    raise ValueError(f"Origen de fundamentales desconocido: {source!r}")
