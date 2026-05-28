"""Configuración central del motor."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EngineConfig:
    """Parámetros que gobiernan una corrida del motor.

    Todo es backtesting/análisis sobre datos históricos: el motor no ejecuta
    órdenes ni opera dinero real.
    """

    symbol: str = "AAPL"
    source: str = "synthetic"  # synthetic | csv | yfinance
    csv_path: str | None = None
    period_days: int = 365

    # Horizonte de pronóstico en días de mercado.
    forecast_horizon: int = 5

    # Modelos de pronóstico a usar (None = todos los disponibles).
    # Opciones: drift, linear, holt, ar, arima, gbr.
    forecast_models: tuple[str, ...] | None = None
    # Validación walk-forward.
    walk_forward_splits: int = 30
    walk_forward_min_train: int = 60

    # Gestión de riesgo (fracción del capital arriesgado por operación).
    risk_per_trade: float = 0.02
    stop_loss_atr_mult: float = 2.0

    # Capital inicial para el backtest.
    initial_capital: float = 10_000.0

    # Días de mercado por año (para anualizar volatilidad/Sharpe).
    trading_days_per_year: int = 252

    # Tasa libre de riesgo anual (para el Sharpe).
    risk_free_rate: float = 0.0

    # Caché de precios en SQLite (evita re-descargar datos, p. ej. yfinance).
    use_cache: bool = True
    cache_path: str = ".cache/prices.db"
    # Antigüedad máxima (días de mercado) antes de considerar la caché obsoleta.
    cache_max_age_days: int = 1

    # Análisis fundamental.
    enable_fundamentals: bool = True
    fundamentals_source: str = "synthetic"  # synthetic | yfinance

    indicator_windows: dict[str, int] = field(
        default_factory=lambda: {
            "sma_fast": 20,
            "sma_slow": 50,
            "ema": 20,
            "rsi": 14,
            "atr": 14,
            "bollinger": 20,
        }
    )
