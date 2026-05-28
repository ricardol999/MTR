"""Caché de precios OHLCV en SQLite.

Evita re-descargar datos (sobre todo de yfinance) entre corridas. Guarda las
velas por (símbolo, origen, fecha) y permite recuperar el histórico cacheado.
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

import pandas as pd

from engine.data.providers import OHLCV_COLUMNS


class PriceCache:
    def __init__(self, path: str):
        self.path = path
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS prices (
                    symbol TEXT NOT NULL,
                    source TEXT NOT NULL,
                    date   TEXT NOT NULL,
                    open   REAL, high REAL, low REAL, close REAL, volume REAL,
                    fetched_at TEXT NOT NULL,
                    PRIMARY KEY (symbol, source, date)
                )
                """
            )

    def get(
        self, symbol: str, source: str, period_days: int, max_age_days: int
    ) -> pd.DataFrame | None:
        """Devuelve el histórico cacheado si es suficiente y está fresco."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT date, open, high, low, close, volume
                FROM prices WHERE symbol = ? AND source = ?
                ORDER BY date ASC
                """,
                (symbol, source),
            ).fetchall()

        if len(rows) < period_days:
            return None

        df = pd.DataFrame(
            rows, columns=["date", *OHLCV_COLUMNS]
        )
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        df.index.name = "date"

        # Frescura: la última fecha no debe quedar más vieja que max_age_days
        # días de mercado respecto a hoy.
        last_date = df.index[-1]
        stale_after = pd.Timestamp.today().normalize() - pd.tseries.offsets.BDay(
            max_age_days
        )
        if last_date < stale_after:
            return None

        return df.tail(period_days)

    def put(self, symbol: str, source: str, df: pd.DataFrame) -> None:
        now = datetime.now(timezone.utc).isoformat()
        records = [
            (
                symbol,
                source,
                idx.strftime("%Y-%m-%d"),
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                float(row["volume"]),
                now,
            )
            for idx, row in df.iterrows()
        ]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO prices
                    (symbol, source, date, open, high, low, close, volume, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, source, date) DO UPDATE SET
                    open=excluded.open, high=excluded.high, low=excluded.low,
                    close=excluded.close, volume=excluded.volume,
                    fetched_at=excluded.fetched_at
                """,
                records,
            )
