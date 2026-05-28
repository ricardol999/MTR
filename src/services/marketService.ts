// Cliente del motor de pronóstico bursátil (engine/api).
// Configura la URL con EXPO_PUBLIC_ENGINE_API_URL.

import {
  AnalysisResult,
  HealthResponse,
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

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
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
  fundamentals?: boolean;
};

function optionParams(options: AnalysisOptions): Record<string, QueryValue> {
  return {
    source: options.source,
    horizon: options.horizon,
    models: options.models?.join(','),
    fundamentals: options.fundamentals,
  };
}

export async function checkHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>(buildUrl('/health'));
}

export async function fetchSignal(
  symbol: string,
  options: AnalysisOptions = {}
): Promise<SignalSummary> {
  return getJson<SignalSummary>(
    buildUrl('/signal', { symbol, ...optionParams(options) })
  );
}

export async function fetchAnalysis(
  symbol: string,
  options: AnalysisOptions = {}
): Promise<AnalysisResult> {
  return getJson<AnalysisResult>(
    buildUrl('/analyze', { symbol, ...optionParams(options) })
  );
}

export async function fetchWatchlist(
  symbols: string[],
  options: AnalysisOptions = {}
): Promise<SignalSummary[]> {
  const data = await getJson<WatchlistResponse>(
    buildUrl('/watchlist', { symbols: symbols.join(','), ...optionParams(options) })
  );
  return data.results;
}
