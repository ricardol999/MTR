"""Agente de análisis fundamental: valora calidad y precio del negocio.

Carga métricas fundamentales y las resume en un score de -1 (caro/débil) a
+1 (barato/sólido). Cada métrica disponible aporta a un promedio; las que
faltan se ignoran para no penalizar por datos ausentes.
"""

from __future__ import annotations

from engine.core.agent import BaseAgent
from engine.core.context import MarketContext
from engine.data.fundamentals import get_fundamentals_provider


def _score_lower_better(value: float | None, good: float, bad: float) -> float | None:
    """1.0 si value<=good, -1.0 si value>=bad, lineal en medio."""
    if value is None:
        return None
    if value <= good:
        return 1.0
    if value >= bad:
        return -1.0
    return 1.0 - 2.0 * (value - good) / (bad - good)


def _score_higher_better(value: float | None, bad: float, good: float) -> float | None:
    if value is None:
        return None
    if value >= good:
        return 1.0
    if value <= bad:
        return -1.0
    return -1.0 + 2.0 * (value - bad) / (good - bad)


class FundamentalAgent(BaseAgent):
    name = "FundamentalAgent"

    def run(self, context: MarketContext) -> MarketContext:
        cfg = context.config
        provider = get_fundamentals_provider(cfg.fundamentals_source)
        metrics = provider.get_fundamentals(cfg.symbol)

        components = {
            "pe": _score_lower_better(metrics.get("pe"), good=12, bad=35),
            "pb": _score_lower_better(metrics.get("pb"), good=1.5, bad=8),
            "ps": _score_lower_better(metrics.get("ps"), good=1.5, bad=10),
            "roe": _score_higher_better(metrics.get("roe"), bad=0.05, good=0.20),
            "debt_to_equity": _score_lower_better(
                metrics.get("debt_to_equity"), good=0.5, bad=2.0
            ),
            "profit_margin": _score_higher_better(
                metrics.get("profit_margin"), bad=0.0, good=0.20
            ),
            "revenue_growth": _score_higher_better(
                metrics.get("revenue_growth"), bad=0.0, good=0.20
            ),
        }
        available = [v for v in components.values() if v is not None]
        score = sum(available) / len(available) if available else 0.0

        context.fundamentals = {
            "source": cfg.fundamentals_source,
            "metrics": metrics,
            "components": components,
            "score": round(score, 3),
        }
        context.note(
            self.name,
            f"Score fundamental={score:+.2f} "
            f"(PE={_fmt(metrics.get('pe'))} ROE={_fmt(metrics.get('roe'))} "
            f"D/E={_fmt(metrics.get('debt_to_equity'))}).",
        )
        return context


def _fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2f}"
