"""Proveedores de datos históricos OHLCV.

Cada proveedor devuelve un ``DataFrame`` indexado por fecha con columnas
``open, high, low, close, volume``. Esto desacopla el origen de los datos del
resto del motor: el mismo pipeline funciona con datos sintéticos (offline),
CSV o yfinance.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


def stable_seed(text: str) -> int:
    """Semilla determinista entre procesos (hash() de Python está salado)."""
    return int.from_bytes(hashlib.md5(text.encode("utf-8")).digest()[:4], "big")


class DataProvider(ABC):
    @abstractmethod
    def get_history(self, symbol: str, period_days: int) -> pd.DataFrame:
        """Devuelve OHLCV de los últimos ``period_days`` días de mercado."""
        raise NotImplementedError


def _validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in OHLCV_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas OHLCV: {missing}")
    df = df[OHLCV_COLUMNS].copy()
    df = df.dropna(subset=["close"])
    if df.empty:
        raise ValueError("El proveedor devolvió un dataset vacío.")
    return df


class SyntheticDataProvider(DataProvider):
    """Genera una serie OHLCV realista con un random walk geométrico.

    Útil para demos, pruebas y entornos sin acceso a internet. Es determinista
    por símbolo (la semilla deriva del nombre) para resultados reproducibles.
    """

    def __init__(self, annual_drift: float = 0.08, annual_vol: float = 0.25):
        self.annual_drift = annual_drift
        self.annual_vol = annual_vol

    def get_history(self, symbol: str, period_days: int) -> pd.DataFrame:
        rng = np.random.default_rng(stable_seed(symbol))

        dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=period_days)
        n = len(dates)

        dt = 1.0 / 252.0
        mu, sigma = self.annual_drift, self.annual_vol
        shocks = rng.normal(
            (mu - 0.5 * sigma**2) * dt, sigma * np.sqrt(dt), size=n
        )
        close = 100.0 * np.exp(np.cumsum(shocks))

        intraday = np.abs(rng.normal(0, sigma * np.sqrt(dt), size=n)) * close
        open_ = close * (1 + rng.normal(0, 0.002, size=n))
        high = np.maximum(open_, close) + intraday
        low = np.minimum(open_, close) - intraday
        volume = rng.integers(1_000_000, 5_000_000, size=n).astype(float)

        df = pd.DataFrame(
            {
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            },
            index=dates,
        )
        df.index.name = "date"
        return _validate_ohlcv(df)


class CsvDataProvider(DataProvider):
    """Carga OHLCV desde un CSV con una columna de fecha y columnas OHLCV.

    Acepta encabezados comunes (Open/High/Low/Close/Adj Close/Volume) y los
    normaliza a minúsculas.
    """

    def __init__(self, path: str):
        self.path = path

    def get_history(self, symbol: str, period_days: int) -> pd.DataFrame:
        df = pd.read_csv(self.path)
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        date_col = next(
            (c for c in ("date", "datetime", "timestamp") if c in df.columns), None
        )
        if date_col is None:
            raise ValueError("El CSV debe incluir una columna de fecha (date/datetime).")
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col).sort_index()
        df.index.name = "date"

        if "close" not in df.columns and "adj_close" in df.columns:
            df["close"] = df["adj_close"]

        df = _validate_ohlcv(df)
        return df.tail(period_days)


class YFinanceDataProvider(DataProvider):
    """Descarga datos reales con yfinance (requiere acceso a internet).

    En entornos sin red externa fallará; usa SyntheticDataProvider o CSV.
    """

    def get_history(self, symbol: str, period_days: int) -> pd.DataFrame:
        try:
            import yfinance as yf
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "yfinance no está instalado. Ejecuta: pip install yfinance"
            ) from exc

        # Margen extra de días calendario para cubrir fines de semana/feriados.
        period = f"{int(period_days * 1.5) + 10}d"
        raw = yf.download(symbol, period=period, progress=False, auto_adjust=True)
        if raw is None or raw.empty:
            raise RuntimeError(
                f"yfinance no devolvió datos para '{symbol}'. "
                "Verifica el símbolo y el acceso a internet."
            )
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        raw.columns = [str(c).strip().lower() for c in raw.columns]
        raw.index.name = "date"
        df = _validate_ohlcv(raw)
        return df.tail(period_days)


def get_provider(source: str, csv_path: str | None = None) -> DataProvider:
    source = source.lower()
    if source == "synthetic":
        return SyntheticDataProvider()
    if source == "csv":
        if not csv_path:
            raise ValueError("source='csv' requiere config.csv_path.")
        return CsvDataProvider(csv_path)
    if source == "yfinance":
        return YFinanceDataProvider()
    raise ValueError(f"Origen de datos desconocido: {source!r}")
