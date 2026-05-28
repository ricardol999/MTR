"""CLI del scheduler de alertas.

Ejemplos:
    python -m engine.scheduler --symbols AAPL,MSFT,NVDA --once
    python -m engine.scheduler --symbols AAPL,MSFT --interval 3600 --alerts-file alerts.jsonl
"""

from __future__ import annotations

import argparse

from engine.alerts import ConsoleAlertSink, FileAlertSink, WebhookAlertSink
from engine.config import EngineConfig
from engine.scheduler.runner import loop, run_once
from engine.scheduler.state import SignalState


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="engine.scheduler", description="Scheduler de alertas.")
    p.add_argument("--symbols", required=True, help="Símbolos separados por coma.")
    p.add_argument("--source", default="synthetic", choices=["synthetic", "csv", "yfinance"])
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--once", action="store_true", help="Una sola pasada y termina.")
    p.add_argument("--interval", type=int, default=3600, help="Segundos entre pasadas.")
    p.add_argument("--state-path", default=".cache/signal_state.db")
    p.add_argument("--alerts-file", default=None, help="Ruta JSONL para registrar alertas.")
    p.add_argument("--webhook", default=None, help="URL para POST de cada alerta.")
    args = p.parse_args(argv)

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    config = EngineConfig(source=args.source, forecast_horizon=args.horizon)
    state = SignalState(args.state_path)

    sinks = [ConsoleAlertSink()]
    if args.alerts_file:
        sinks.append(FileAlertSink(args.alerts_file))
    if args.webhook:
        sinks.append(WebhookAlertSink(args.webhook))

    if args.once:
        alerts = run_once(symbols, config, sinks, state)
        print(f"-- {len(alerts)} alerta(s) en esta pasada --")
    else:
        print(f"Vigilando {len(symbols)} símbolos cada {args.interval}s (Ctrl+C para salir).")
        try:
            loop(symbols, config, sinks, state, args.interval)
        except KeyboardInterrupt:
            print("\nDetenido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
