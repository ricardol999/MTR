"""Universos de tickers por defecto para screening.

Son listas editables de punto de partida, no recomendaciones. Puedes pasar tus
propios símbolos en su lugar.
"""

from __future__ import annotations

# Acciones emergentes / de crecimiento (mayor riesgo, mayor potencial).
EMERGING = [
    "PLTR", "SOFI", "RIVN", "IONQ", "RKLB",
    "AFRM", "DKNG", "HOOD", "CRWD", "NET",
]

# Grandes capitalizaciones para portafolio.
LARGE_CAP = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",
    "META", "TSLA", "JPM", "V", "WMT",
]

UNIVERSES: dict[str, list[str]] = {
    "emerging": EMERGING,
    "large": LARGE_CAP,
}
