"""Interfaz de línea de comandos del motor.

Ejemplos:
    python -m engine.cli --symbol AAPL --source synthetic
    python -m engine.cli --symbol MSFT --source csv --csv-path data/msft.csv
    python -m engine.cli --symbol AAPL --source yfinance --horizon 10
"""

from __future__ import annotations

import argparse
import json
import sys

from engine.config import EngineConfig
from engine.core.context import MarketContext
from engine.factory import build_engine


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="engine",
        description="Motor multi-agente de análisis y pronóstico bursátil (backtesting).",
    )
    p.add_argument("--symbol", default="AAPL", help="Símbolo a analizar (def: AAPL).")
    p.add_argument(
        "--source",
        default="synthetic",
        choices=["synthetic", "csv", "yfinance"],
        help="Origen de datos (def: synthetic).",
    )
    p.add_argument("--csv-path", default=None, help="Ruta del CSV si source=csv.")
    p.add_argument("--period-days", type=int, default=365, help="Días de histórico.")
    p.add_argument("--horizon", type=int, default=5, help="Horizonte de pronóstico (días).")
    p.add_argument("--capital", type=float, default=10_000.0, help="Capital inicial.")
    p.add_argument("--no-cache", action="store_true", help="Desactiva la caché de precios.")
    p.add_argument(
        "--no-fundamentals", action="store_true", help="Omite el análisis fundamental."
    )
    p.add_argument(
        "--fundamentals-source",
        default="synthetic",
        choices=["synthetic", "yfinance"],
        help="Origen de fundamentales (def: synthetic).",
    )
    p.add_argument("--json", action="store_true", help="Salida en JSON.")
    return p.parse_args(argv)


def _report(ctx: MarketContext) -> str:
    s, fc, risk, bt = ctx.signal, ctx.forecast, ctx.risk, ctx.backtest
    lines = [
        f"=== Reporte: {ctx.symbol} ===",
        "",
        "-- Bitácora de agentes --",
        *ctx.log,
    ]
    if ctx.fundamentals:
        m = ctx.fundamentals["metrics"]
        lines += [
            "",
            "-- Fundamental --",
            f"Score:             {ctx.fundamentals['score']:+.2f}",
            f"PE={_fmt(m.get('pe'))} PB={_fmt(m.get('pb'))} "
            f"ROE={_fmt(m.get('roe'))} D/E={_fmt(m.get('debt_to_equity'))} "
            f"Margen={_fmt(m.get('profit_margin'))}",
        ]
    lines += [
        "",
        "-- Pronóstico --",
        f"Precio actual:     {fc['last_price']:.2f}",
        f"Pronóstico {fc['horizon_days']}d:    {fc['point']:.2f} ({fc['expected_return'] * 100:+.2f}%)",
        f"Banda 95%:         [{fc['lower_95']:.2f}, {fc['upper_95']:.2f}]",
        "",
        "-- Riesgo --",
        f"Volatilidad anual: {risk['annual_vol'] * 100:.1f}%",
        f"Max drawdown:      {risk['max_drawdown'] * 100:.1f}%",
        f"Stop sugerido:     {risk['stop_price']:.2f}",
        f"Tamaño posición:   {risk['suggested_shares']} acciones (${risk['position_value']:.0f})",
        "",
        "-- Señal --",
        f"Acción:            {s['action']} (score {s['score']:+.2f}, confianza {s['confidence']:.2f})",
        "Razones:",
        *[f"  - {r}" for r in s["reasons"]],
        "",
        "-- Backtest (línea base SMA crossover) --",
        f"Retorno estrategia: {bt['total_return'] * 100:+.1f}%",
        f"Retorno buy&hold:   {bt['buy_hold_return'] * 100:+.1f}%",
        f"Exceso:             {bt['excess_return'] * 100:+.1f}%",
        f"Sharpe:             {bt['sharpe']:.2f}",
        f"Win rate:           {bt['win_rate'] * 100:.0f}%  Trades: {bt['trades']}",
    ]
    return "\n".join(lines)


def _fmt(value: object) -> str:
    return "n/a" if value is None else f"{float(value):.2f}"  # type: ignore[arg-type]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    config = EngineConfig(
        symbol=args.symbol,
        source=args.source,
        csv_path=args.csv_path,
        period_days=args.period_days,
        forecast_horizon=args.horizon,
        initial_capital=args.capital,
        use_cache=not args.no_cache,
        enable_fundamentals=not args.no_fundamentals,
        fundamentals_source=args.fundamentals_source,
    )
    try:
        ctx = build_engine(config).run()
    except Exception as exc:  # noqa: BLE001
        print(f"Error en el motor: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "symbol": ctx.symbol,
                    "indicators": ctx.indicators,
                    "fundamentals": ctx.fundamentals,
                    "forecast": ctx.forecast,
                    "risk": ctx.risk,
                    "signal": ctx.signal,
                    "backtest": ctx.backtest,
                    "log": ctx.log,
                },
                default=float,
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(_report(ctx))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
