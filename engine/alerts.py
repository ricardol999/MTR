"""Alertas de señales y sus destinos (sinks).

Una ``Alert`` describe un cambio accionable en la señal de un símbolo. Los
sinks deciden a dónde va: consola, archivo JSONL o webhook HTTP. Ningún sink
ejecuta órdenes; solo notifican.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class Alert:
    symbol: str
    action: str
    previous_action: str | None
    score: float
    expected_return: float
    last_price: float
    forecast: float
    timestamp: str

    @classmethod
    def from_summary(
        cls, summary: dict, previous_action: str | None
    ) -> "Alert":
        return cls(
            symbol=summary["symbol"],
            action=summary["action"],
            previous_action=previous_action,
            score=summary["score"],
            expected_return=summary["expected_return"],
            last_price=summary["last_price"],
            forecast=summary["forecast"],
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def message(self) -> str:
        change = (
            f"{self.previous_action} -> {self.action}"
            if self.previous_action
            else f"NUEVA {self.action}"
        )
        return (
            f"[{self.symbol}] {change} | precio {self.last_price:.2f} "
            f"pronóstico {self.forecast:.2f} ({self.expected_return * 100:+.1f}%) "
            f"score {self.score:+.2f}"
        )


class AlertSink(ABC):
    @abstractmethod
    def emit(self, alert: Alert) -> None:
        raise NotImplementedError


class ConsoleAlertSink(AlertSink):
    def emit(self, alert: Alert) -> None:
        print(alert.message())


class FileAlertSink(AlertSink):
    """Agrega cada alerta como una línea JSON (JSONL)."""

    def __init__(self, path: str):
        self.path = path
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def emit(self, alert: Alert) -> None:
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(alert), ensure_ascii=False) + "\n")


class WebhookAlertSink(AlertSink):
    """Envía la alerta como POST JSON (best-effort; requiere red)."""

    def __init__(self, url: str, timeout: float = 5.0):
        self.url = url
        self.timeout = timeout

    def emit(self, alert: Alert) -> None:
        import urllib.request

        data = json.dumps(asdict(alert)).encode("utf-8")
        req = urllib.request.Request(
            self.url, data=data, headers={"Content-Type": "application/json"}
        )
        try:
            urllib.request.urlopen(req, timeout=self.timeout).close()
        except Exception as exc:  # noqa: BLE001 - no abortar por fallo de red
            print(f"WebhookAlertSink: fallo al enviar ({exc})")
