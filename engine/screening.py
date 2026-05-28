"""Screening: rankea un universo de tickers por la solidez de su pronóstico.

La "solidez" intenta capturar *cuánto confiar* en la señal, no solo su dirección.
Combina, de forma transparente:

* **direction_reliability**: con qué frecuencia el mejor modelo acertó la
  dirección en la validación walk-forward (lo más importante).
* **error_quality**: error del modelo (RMSE) relativo al precio; menor es mejor.
* **signal_strength**: magnitud del score de la señal combinada.
* **fundamental**: calidad/valor fundamental normalizado a 0-1.

Pensado para correr en PC bajo demanda (con yfinance es lento por símbolo).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable
from typing import Any

from engine.config import EngineConfig
from engine.service import run_analysis

# RMSE relativo (sobre el precio) a partir del cual el error se considera malo.
_REL_ERROR_CEILING = 0.06

_WEIGHTS = {
    "direction": 0.45,
    "error": 0.20,
    "signal": 0.20,
    "fundamental": 0.15,
}


def forecast_solidity(analysis: dict[str, Any]) -> dict[str, float]:
    """Calcula el score de solidez (0-1) y sus componentes a partir de un análisis."""
    fc = analysis["forecast"]
    signal = analysis["signal"]
    fundamentals = analysis.get("fundamentals") or {}

    best = fc["models"].get(fc["best_model"], {})
    dir_acc = best.get("dir_acc")
    rmse = best.get("rmse")
    last_price = fc["last_price"]

    direction = dir_acc if dir_acc is not None else 0.5

    if rmse is not None and last_price > 0:
        rel_error = (rmse / last_price) / _REL_ERROR_CEILING
        error_quality = max(0.0, min(1.0, 1.0 - rel_error))
    else:
        error_quality = 0.0

    signal_strength = min(1.0, abs(signal["score"]))

    fund_score = fundamentals.get("score")
    fundamental = (fund_score + 1.0) / 2.0 if fund_score is not None else 0.5

    solidity = (
        _WEIGHTS["direction"] * direction
        + _WEIGHTS["error"] * error_quality
        + _WEIGHTS["signal"] * signal_strength
        + _WEIGHTS["fundamental"] * fundamental
    )

    return {
        "solidity": round(solidity, 3),
        "direction_reliability": round(direction, 3),
        "error_quality": round(error_quality, 3),
        "signal_strength": round(signal_strength, 3),
        "fundamental": round(fundamental, 3),
    }


def screen(
    symbols: Iterable[str],
    base_config: EngineConfig,
    top_n: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Analiza cada símbolo y devuelve un ranking por solidez.

    Devuelve ``{"ranked": [...], "errors": [...]}``. Los símbolos que fallan
    (p. ej. ticker inexistente) se reportan aparte sin abortar el resto.
    """
    ranked: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for symbol in symbols:
        symbol = symbol.upper()
        config = dataclasses.replace(base_config, symbol=symbol)
        try:
            analysis = run_analysis(config)
        except Exception as exc:  # noqa: BLE001
            errors.append({"symbol": symbol, "error": str(exc)})
            continue

        fc = analysis["forecast"]
        fundamentals = analysis.get("fundamentals") or {}
        ranked.append(
            {
                "symbol": analysis["symbol"],
                "action": analysis["signal"]["action"],
                "last_price": fc["last_price"],
                "forecast": fc["point"],
                "expected_return": fc["expected_return"],
                "best_model": fc["best_model"],
                "fundamental_score": fundamentals.get("score"),
                **forecast_solidity(analysis),
            }
        )

    ranked.sort(key=lambda row: row["solidity"], reverse=True)
    if top_n is not None:
        ranked = ranked[:top_n]
    return {"ranked": ranked, "errors": errors}
