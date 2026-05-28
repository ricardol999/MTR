"""Persistencia del último estado de señal por símbolo (para detectar cambios)."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone


class SignalState:
    def __init__(self, path: str):
        self.path = path
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signal_state (
                    symbol TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    score REAL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def last_action(self, symbol: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT action FROM signal_state WHERE symbol = ?", (symbol,)
            ).fetchone()
        return row[0] if row else None

    def update(self, symbol: str, action: str, score: float) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO signal_state (symbol, action, score, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    action=excluded.action, score=excluded.score,
                    updated_at=excluded.updated_at
                """,
                (symbol, action, score, now),
            )
