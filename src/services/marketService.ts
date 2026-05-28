// Cliente del motor de pronóstico bursátil (engine/api).
// Configura la URL con EXPO_PUBLIC_ENGINE_API_URL.

import {
  AnalysisResult,
  HealthResponse,
  ScreenResponse,
  SignalSummary,
  WatchlistResponse,
} from '../types/market';

const API_URL =
  process.env.EXPO_PUBLIC_ENGINE_API_URL ?? 'http://192.168.1.100:8000';

type QueryValue = string | number | boolean | undefined;

function buildUrl(path: string, params: Record<string, QueryValue> = {}): string {
  const url = new URL(path, API_URL);
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function getJson<T>(url: string, timeoutMs = 30000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  let response: Response;
  try {
    response = await fetch(url, { signal: controller.signal });
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new Error(
        `La API no respondió en ${timeoutMs / 1000}s. ¿Está corriendo el motor?`
      );
    }
    throw new Error(
      'No se pudo conectar con la API del motor. Revisa la URL y la red.'
    );
  } finally {
    clearTimeout(timer);
  }
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const body = (await response.json()) as { error?: string };
      if (body?.error) {
        detail = body.error;
      }
    } catch {
      // respuesta sin cuerpo JSON; se mantiene el detalle por status
    }
    throw new Error(`Error del motor: ${detail}`);
  }
  return (await response.json()) as T;
}

export type AnalysisOptions = {
  source?: 'synthetic' | 'csv' | 'yfinance';
  horizon?: number;
  models?: string[];
  wfSplits?: number;
  fundamentals?: boolean;
};

function optionParams(options: AnalysisOptions): Record<string, QueryValue> {
  return {
    source: options.source,
    horizon: options.horizon,
    models: options.models?.join(','),
    wf_splits: options.wfSplits,
    fundamentals: options.fundamentals,
  };
}

// yfinance descarga datos, así que damos más margen que con datos sintéticos.
function timeoutFor(options: AnalysisOptions): number {
  return options.source === 'yfinance' ? 60000 : 30000;
}

export async function checkHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>(buildUrl('/health'));
}

export async function fetchSignal(
  symbol: string,
  options: AnalysisOptions = {}
): Promise<SignalSummary> {
  return getJson<SignalSummary>(
    buildUrl('/signal', { symbol, ...optionParams(options) }),
    timeoutFor(options)
  );
}

export async function fetchAnalysis(
  symbol: string,
  options: AnalysisOptions = {}
): Promise<AnalysisResult> {
  return getJson<AnalysisResult>(
    buildUrl('/analyze', { symbol, ...optionParams(options) }),
    timeoutFor(options)
  );
}

export type ScreenOptions = AnalysisOptions & {
  universe?: 'emerging' | 'large';
  symbols?: string[];
  top?: number;
};

// El screening corre el análisis por cada símbolo del universo; con yfinance
// puede tardar bastante, así que damos un margen amplio.
export async function fetchScreen(options: ScreenOptions = {}): Promise<ScreenResponse> {
  const { universe, symbols, top, ...analysis } = options;
  const timeout = analysis.source === 'yfinance' ? 180000 : 60000;
  return getJson<ScreenResponse>(
    buildUrl('/screen', {
      universe,
      symbols: symbols?.join(','),
      top,
      ...optionParams(analysis),
    }),
    timeout
  );
}

export async function fetchWatchlist(
  symbols: string[],
  options: AnalysisOptions = {}
): Promise<SignalSummary[]> {
  const data = await getJson<WatchlistResponse>(
    buildUrl('/watchlist', { symbols: symbols.join(','), ...optionParams(options) }),
    timeoutFor(options)
  );
  return data.results;
}
