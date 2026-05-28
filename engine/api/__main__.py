"""Punto de entrada de la API: python -m engine.api --host 0.0.0.0 --port 8000."""

from __future__ import annotations

import argparse

from engine.api.server import create_server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engine.api", description="API del motor.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    server = create_server(args.host, args.port)
    print(f"Motor escuchando en http://{args.host}:{args.port}")
    print("Rutas: /health /analyze /signal /watchlist")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
