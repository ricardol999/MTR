// Tipos del motor de análisis y pronóstico bursátil expuesto por la API
// (engine/api). Reflejan las respuestas de /signal, /watchlist y /analyze.

export type SignalAction = 'BUY' | 'SELL' | 'HOLD';

export type SignalSummary = {
  symbol: string;
  action: SignalAction;
  score: number;
  confidence: number;
  last_price: number;
  forecast: number;
  expected_return: number;
  best_model: string;
  horizon_days: number;
};

export type WatchlistResponse = {
  results: SignalSummary[];
};

export type ScreenRow = {
  symbol: string;
  action: SignalAction;
  last_price: number;
  forecast: number;
  expected_return: number;
  best_model: string;
  fundamental_score: number | null;
  solidity: number;
  direction_reliability: number;
  error_quality: number;
  signal_strength: number;
  fundamental: number;
};

export type ScreenError = {
  symbol: string;
  error: string;
};

export type ScreenResponse = {
  ranked: ScreenRow[];
  errors: ScreenError[];
};

export type ModelMetrics = {
  forecast: number;
  mae: number | null;
  rmse: number | null;
  mape: number | null;
  dir_acc: number | null;
  n: number;
};

export type Forecast = {
  horizon_days: number;
  last_price: number;
  point: number;
  best_model: string;
  ensemble: number | null;
  expected_return: number;
  lower_95: number;
  upper_95: number;
  daily_vol: number;
  models: Record<string, ModelMetrics>;
};

export type Signal = {
  action: SignalAction;
  score: number;
  confidence: number;
  reasons: string[];
};

export type Risk = {
  annual_vol: number;
  max_drawdown: number;
  stop_price: number;
  suggested_shares: number;
  position_value: number;
};

export type Backtest = {
  total_return: number;
  buy_hold_return: number;
  sharpe: number;
  max_drawdown: number;
  win_rate: number;
  trades: number;
};

export type AnalysisResult = {
  symbol: string;
  indicators: Record<string, number | boolean | null>;
  fundamentals: {
    score: number;
    metrics: Record<string, number | null>;
  };
  forecast: Forecast;
  risk: Risk;
  signal: Signal;
  backtest: Backtest;
  log: string[];
};

export type HealthResponse = {
  status: string;
  version: string;
  models: string[];
};
