"""Agente de señal: combina técnico + pronóstico en una recomendación."""

from __future__ import annotations

from engine.core.agent import BaseAgent
from engine.core.context import MarketContext


class SignalAgent(BaseAgent):
    """Pondera varias evidencias en un score de -1 (venta) a +1 (compra).

    Reglas (cada una aporta a un score acumulado):
      * Cruce de medias (tendencia)
      * RSI (sobrecompra/sobreventa)
      * Histograma MACD (momentum)
      * Retorno esperado del pronóstico
    """

    name = "SignalAgent"

    def run(self, context: MarketContext) -> MarketContext:
        ind = context.indicators
        fc = context.forecast
        reasons: list[str] = []
        score = 0.0

        if ind.get("trend_up"):
            score += 0.25
            reasons.append("SMA rápida > SMA lenta (tendencia alcista)")
        else:
            score -= 0.25
            reasons.append("SMA rápida < SMA lenta (tendencia bajista)")

        rsi = ind.get("rsi")
        if rsi is not None:
            if rsi < 30:
                score += 0.25
                reasons.append(f"RSI {rsi:.0f} en sobreventa")
            elif rsi > 70:
                score -= 0.25
                reasons.append(f"RSI {rsi:.0f} en sobrecompra")

        macd_hist = ind.get("macd_hist")
        if macd_hist is not None:
            if macd_hist > 0:
                score += 0.2
                reasons.append("MACD con momentum positivo")
            else:
                score -= 0.2
                reasons.append("MACD con momentum negativo")

        exp_ret = fc.get("expected_return")
        if exp_ret is not None:
            if exp_ret > 0.01:
                score += 0.3
                reasons.append(f"Pronóstico {exp_ret * 100:+.1f}%")
            elif exp_ret < -0.01:
                score -= 0.3
                reasons.append(f"Pronóstico {exp_ret * 100:+.1f}%")

        score = max(-1.0, min(1.0, score))
        if score >= 0.3:
            action = "BUY"
        elif score <= -0.3:
            action = "SELL"
        else:
            action = "HOLD"

        context.signal = {
            "action": action,
            "score": round(score, 3),
            "confidence": round(abs(score), 3),
            "reasons": reasons,
        }
        context.note(self.name, f"Señal={action} score={score:+.2f}.")
        return context
