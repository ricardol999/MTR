"""Pruebas de humo del motor con el proveedor sintético (offline)."""

from __future__ import annotations

import numpy as np

from engine.alerts import Alert, AlertSink, FileAlertSink
from engine.api.server import handle_request
from engine.config import EngineConfig
from engine.data.cache import PriceCache
from engine.data.fundamentals import SyntheticFundamentalsProvider
from engine.data.providers import SyntheticDataProvider
from engine.factory import build_engine
from engine.models import available_model_names, build_models, walk_forward
from engine.models.classical import HoltLinearModel
from engine.scheduler.runner import run_once, should_alert
from engine.scheduler.state import SignalState

_FAST_QS = "source=synthetic&cache=false&models=drift,holt&wf_splits=10"


def _fast_config(symbol: str = "TEST") -> EngineConfig:
    return EngineConfig(
        symbol=symbol,
        source="synthetic",
        use_cache=False,
        forecast_models=("drift", "holt"),
        walk_forward_splits=10,
    )


def _run(symbol: str = "TEST"):
    cfg = EngineConfig(
        symbol=symbol,
        source="synthetic",
        period_days=300,
        use_cache=False,
        forecast_models=("drift", "linear", "holt", "ar"),
        walk_forward_splits=15,
    )
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


def test_fundamentales_producen_score_en_rango():
    ctx = _run()
    assert ctx.fundamentals
    assert -1.0 <= ctx.fundamentals["score"] <= 1.0
    assert set(ctx.fundamentals["metrics"]) >= {"pe", "roe", "debt_to_equity"}


def test_fundamentales_son_deterministas():
    a = SyntheticFundamentalsProvider().get_fundamentals("XYZ")
    b = SyntheticFundamentalsProvider().get_fundamentals("XYZ")
    assert a == b


def test_cache_guarda_y_recupera(tmp_path):
    cache = PriceCache(str(tmp_path / "prices.db"))
    df = SyntheticDataProvider().get_history("CSH", 120)
    cache.put("CSH", "synthetic", df)
    got = cache.get("CSH", "synthetic", period_days=100, max_age_days=10_000)
    assert got is not None
    assert len(got) == 100
    assert np.allclose(got["close"].tail(50).to_numpy(), df["close"].tail(50).to_numpy())


def test_cache_obsoleta_devuelve_none(tmp_path):
    cache = PriceCache(str(tmp_path / "prices.db"))
    df = SyntheticDataProvider().get_history("OLD", 120)
    cache.put("OLD", "synthetic", df)
    # max_age negativo fuerza que cualquier dato se considere obsoleto.
    assert cache.get("OLD", "synthetic", period_days=100, max_age_days=-5) is None


def test_forecast_reporta_modelos_y_mejor():
    ctx = _run()
    fc = ctx.forecast
    assert fc["best_model"] in fc["models"]
    assert set(fc["models"]) == {"drift", "linear", "holt", "ar"}
    for r in fc["models"].values():
        assert np.isfinite(r["forecast"])


def test_walk_forward_metricas_no_negativas():
    prices = SyntheticDataProvider().get_history("WF", 250)["close"].to_numpy()
    m = walk_forward(HoltLinearModel(), prices, horizon=5, n_splits=10, min_train=60)
    assert m["n"] > 0
    assert m["rmse"] >= 0 and m["mae"] >= 0
    assert 0.0 <= m["dir_acc"] <= 1.0


def test_registry_incluye_modelos_base():
    names = available_model_names()
    assert {"drift", "linear", "holt", "ar"}.issubset(set(names))


def test_modelos_opcionales_pronostican_si_disponibles():
    prices = SyntheticDataProvider().get_history("OPT", 200)["close"].to_numpy()
    for model in build_models(["arima", "gbr"]):
        value = model.forecast(prices, horizon=5)
        assert np.isfinite(value) and value > 0


def test_api_health():
    status, body = handle_request("/health", "")
    assert status == 200
    assert body["status"] == "ok"
    assert "drift" in body["models"]


def test_api_signal_y_analyze():
    status, body = handle_request("/signal", f"symbol=AAPL&{_FAST_QS}")
    assert status == 200
    assert body["action"] in {"BUY", "SELL", "HOLD"}

    status, body = handle_request("/analyze", f"symbol=AAPL&{_FAST_QS}")
    assert status == 200
    assert body["symbol"] == "AAPL" and "forecast" in body


def test_api_watchlist_y_404():
    status, body = handle_request("/watchlist", f"symbols=AAPL,MSFT&{_FAST_QS}")
    assert status == 200
    assert len(body["results"]) == 2

    status, body = handle_request("/nope", "")
    assert status == 404


def test_should_alert_logica():
    assert should_alert(None, "BUY") is True
    assert should_alert(None, "HOLD") is False
    assert should_alert("HOLD", "SELL") is True
    assert should_alert("BUY", "BUY") is False


class _CollectingSink(AlertSink):
    def __init__(self) -> None:
        self.alerts: list[Alert] = []

    def emit(self, alert: Alert) -> None:
        self.alerts.append(alert)


def test_scheduler_no_realerta_sin_cambios(tmp_path):
    state = SignalState(str(tmp_path / "state.db"))
    sink = _CollectingSink()
    config = _fast_config()
    run_once(["AAPL", "MSFT"], config, [sink], state)
    # Segunda pasada con datos idénticos: ninguna señal cambia -> sin alertas.
    second = run_once(["AAPL", "MSFT"], config, [sink], state)
    assert second == []


def test_file_alert_sink_escribe_jsonl(tmp_path):
    path = tmp_path / "alerts.jsonl"
    sink = FileAlertSink(str(path))
    summary = {
        "symbol": "AAPL", "action": "BUY", "score": 0.5, "expected_return": 0.03,
        "last_price": 100.0, "forecast": 103.0,
    }
    sink.emit(Alert.from_summary(summary, previous_action=None))
    assert path.read_text().strip().count("\n") == 0
    assert '"symbol": "AAPL"' in path.read_text()
