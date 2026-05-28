"""CLI de screening: rankea un universo por solidez del pronóstico.

Ejemplos:
    python -m engine.screen --universe emerging --source yfinance --top 10
    python -m engine.screen --symbols PLTR,SOFI,NVDA --source synthetic
"""

from __future__ import annotations

import argparse
import sys

from engine.config import EngineConfig
from engine.screening import screen
from engine.universe import UNIVERSES


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="engine.screen", description="Screening por solidez.")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--universe", choices=sorted(UNIVERSES), help="Universo predefinido.")
    group.add_argument("--symbols", help="Símbolos separados por coma.")
    p.add_argument("--source", default="synthetic", choices=["synthetic", "csv", "yfinance"])
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--models", default="drift,holt,ar", help="Modelos (coma).")
    p.add_argument("--wf-splits", type=int, default=8)
    p.add_argument("--top", type=int, default=None, help="Mostrar solo los N mejores.")
    args = p.parse_args(argv)

    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols = UNIVERSES[args.universe or "emerging"]

    # Con datos reales, también fundamentales reales.
    fundamentals_source = "yfinance" if args.source == "yfinance" else "synthetic"
    config = EngineConfig(
        source=args.source,
        forecast_horizon=args.horizon,
        forecast_models=tuple(m.strip() for m in args.models.split(",")),
        walk_forward_splits=args.wf_splits,
        fundamentals_source=fundamentals_source,
    )

    print(f"Analizando {len(symbols)} símbolos vía {args.source}...", file=sys.stderr)
    result = screen(symbols, config, top_n=args.top)

    print(f"{'#':>2}  {'SÍMBOLO':<8} {'SEÑAL':<5} {'PRECIO':>9} {'PRON.':>9} "
          f"{'RET':>7} {'SOLIDEZ':>7} {'DIR':>5} {'FUND':>6}")
    for i, r in enumerate(result["ranked"], 1):
        fund = "n/a" if r["fundamental_score"] is None else f"{r['fundamental_score']:+.2f}"
        print(
            f"{i:>2}  {r['symbol']:<8} {r['action']:<5} {r['last_price']:>9.2f} "
            f"{r['forecast']:>9.2f} {r['expected_return'] * 100:>6.1f}% "
            f"{r['solidity']:>7.2f} {r['direction_reliability'] * 100:>4.0f}% {fund:>6}"
        )

    if result["errors"]:
        print("\nErrores:", file=sys.stderr)
        for e in result["errors"]:
            print(f"  {e['symbol']}: {e['error']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
