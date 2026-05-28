"""Pruebas de humo del motor con el proveedor sintético (offline)."""

from __future__ import annotations

import numpy as np

from engine.config import EngineConfig
from engine.data.providers import SyntheticDataProvider
from engine.factory import build_engine


def _run(symbol: str = "TEST"):
    cfg = EngineConfig(symbol=symbol, source="synthetic", period_days=300)
    return build_engine(cfg).run()


def test_pipeline_completo_produce_todas_las_secciones():
    ctx = _run()
    assert ctx.prices is not None and not ctx.prices.empty
    assert ctx.indicators and ctx.forecast and ctx.risk and ctx.signal and ctx.backtest


def test_proveedor_sintetico_es_determinista():
    a = SyntheticDataProvider().get_history("ABC", 100)
    b = SyntheticDataProvider().get_history("ABC", 100)
    assert np.allclose(a["close"].to_numpy(), b["close"].to_numpy())


def test_senal_es_valida():
    ctx = _run()
    assert ctx.signal["action"] in {"BUY", "SELL", "HOLD"}
    assert -1.0 <= ctx.signal["score"] <= 1.0


def test_pronostico_dentro_de_banda():
    ctx = _run()
    fc = ctx.forecast
    assert fc["lower_95"] <= fc["point"] <= fc["upper_95"]


def test_backtest_sin_lookahead_devuelve_metricas():
    ctx = _run()
    bt = ctx.backtest
    assert bt["bars"] > 0
    assert "sharpe" in bt and "max_drawdown" in bt
    assert bt["max_drawdown"] <= 0.0
