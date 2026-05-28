"""Ejecuta el motor sobre una watchlist y emite alertas ante cambios de señal."""

from __future__ import annotations

import dataclasses
import time
from collections.abc import Iterable, Sequence

from engine.alerts import Alert, AlertSink
from engine.config import EngineConfig
from engine.scheduler.state import SignalState
from engine.service import signal_summary


def should_alert(previous: str | None, current: str) -> bool:
    """Alerta si la señal cambió, o si es nueva y accionable (no HOLD)."""
    if previous is None:
        return current != "HOLD"
    return current != previous


def run_once(
    symbols: Iterable[str],
    base_config: EngineConfig,
    sinks: Sequence[AlertSink],
    state: SignalState,
) -> list[Alert]:
    """Evalúa cada símbolo una vez y emite alertas por cambios. Devuelve alertas."""
    alerts: list[Alert] = []
    for symbol in symbols:
        symbol = symbol.upper()
        config = dataclasses.replace(base_config, symbol=symbol)
        summary = signal_summary(config)
        previous = state.last_action(symbol)
        current = summary["action"]

        if should_alert(previous, current):
            alert = Alert.from_summary(summary, previous)
            for sink in sinks:
                sink.emit(alert)
            alerts.append(alert)

        state.update(symbol, current, summary["score"])
    return alerts


def loop(
    symbols: Iterable[str],
    base_config: EngineConfig,
    sinks: Sequence[AlertSink],
    state: SignalState,
    interval_seconds: int,
    max_iterations: int | None = None,
) -> None:
    """Repite run_once cada ``interval_seconds`` (cron en proceso)."""
    symbols = list(symbols)
    iteration = 0
    while max_iterations is None or iteration < max_iterations:
        run_once(symbols, base_config, sinks, state)
        iteration += 1
        if max_iterations is not None and iteration >= max_iterations:
            break
        time.sleep(interval_seconds)
