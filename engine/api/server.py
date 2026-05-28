"""API HTTP del motor sobre la librería estándar (sin dependencias extra).

Rutas:
    GET /health                      -> estado y modelos disponibles
    GET /analyze?symbol=AAPL&...     -> análisis completo (JSON del motor)
    GET /signal?symbol=AAPL&...      -> resumen señal + pronóstico
    GET /watchlist?symbols=AAPL,MSFT -> resúmenes para varios símbolos

Parámetros de consulta soportados: symbol, source, horizon, period_days,
models (coma), wf_splits, fundamentals (true/false), fundamentals_source,
capital, cache (true/false).
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from engine import __version__
from engine.config import EngineConfig
from engine.models import available_model_names
from engine.screening import screen
from engine.service import run_analysis, signal_summary
from engine.universe import UNIVERSES


def _first(qs: dict[str, list[str]], key: str, default: str | None = None) -> str | None:
    values = qs.get(key)
    return values[0] if values else default


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_config_from_query(qs: dict[str, list[str]]) -> EngineConfig:
    """Construye un EngineConfig a partir de los parámetros de consulta."""
    models = _first(qs, "models")
    source = _first(qs, "source", "synthetic") or "synthetic"
    # Si los precios son reales (yfinance), los fundamentales también lo son,
    # salvo que se pida explícitamente otra fuente.
    default_fund = "yfinance" if source == "yfinance" else "synthetic"
    return EngineConfig(
        symbol=(_first(qs, "symbol", "AAPL") or "AAPL").upper(),
        source=source,
        csv_path=_first(qs, "csv_path"),
        period_days=int(_first(qs, "period_days", "365") or 365),
        forecast_horizon=int(_first(qs, "horizon", "5") or 5),
        forecast_models=(
            tuple(m.strip() for m in models.split(",")) if models else None
        ),
        walk_forward_splits=int(_first(qs, "wf_splits", "30") or 30),
        initial_capital=float(_first(qs, "capital", "10000") or 10000),
        use_cache=_bool(_first(qs, "cache"), True),
        enable_fundamentals=_bool(_first(qs, "fundamentals"), True),
        fundamentals_source=_first(qs, "fundamentals_source", default_fund) or default_fund,
    )


def handle_request(path: str, query: str) -> tuple[int, dict]:
    """Enruta una petición y devuelve (status_code, body_dict). Sin I/O de red.

    Separado del handler HTTP para poder probarlo sin levantar un socket.
    """
    qs = parse_qs(query)
    try:
        if path == "/health":
            return 200, {
                "status": "ok",
                "version": __version__,
                "models": available_model_names(),
            }
        if path == "/analyze":
            return 200, run_analysis(build_config_from_query(qs))
        if path == "/signal":
            return 200, signal_summary(build_config_from_query(qs))
        if path == "/watchlist":
            raw = _first(qs, "symbols", "") or ""
            symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]
            if not symbols:
                return 400, {"error": "Falta el parámetro 'symbols'."}
            results = []
            for sym in symbols:
                params = dict(qs, symbol=[sym])
                results.append(signal_summary(build_config_from_query(params)))
            return 200, {"results": results}
        if path == "/screen":
            universe = _first(qs, "universe")
            raw = _first(qs, "symbols", "") or ""
            if raw:
                symbols = [s.strip().upper() for s in raw.split(",") if s.strip()]
            elif universe in UNIVERSES:
                symbols = UNIVERSES[universe]
            else:
                return 400, {
                    "error": f"Indica 'symbols' o 'universe' ({sorted(UNIVERSES)})."
                }
            top = _first(qs, "top")
            return 200, screen(
                symbols,
                build_config_from_query(qs),
                top_n=int(top) if top else None,
            )
        return 404, {"error": f"Ruta no encontrada: {path}"}
    except ValueError as exc:
        return 400, {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return 500, {"error": str(exc)}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - firma impuesta por la stdlib
        parsed = urlparse(self.path)
        status, body = handle_request(parsed.path, parsed.query)
        payload = json.dumps(body, default=float, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def handle(self) -> None:
        # Clientes (Safari/iOS) abren conexiones de sondeo que cierran sin enviar
        # nada; ignoramos esos cortes para no ensuciar la consola.
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def log_message(self, *args: object) -> None:  # silencia el log por defecto
        pass


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), _Handler)
