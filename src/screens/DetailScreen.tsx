import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { fetchAnalysis } from '../services/marketService';
import { AnalysisResult, SignalAction } from '../types/market';

const ACTION_COLORS: Record<SignalAction, string> = {
  BUY: '#1b8a5a',
  SELL: '#c0392b',
  HOLD: '#7f8c8d',
};

type Props = {
  symbol: string;
  source: 'synthetic' | 'yfinance';
  onBack: () => void;
};

function pct(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'n/a';
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`;
}

function num(value: number | boolean | null | undefined, digits = 2): string {
  if (typeof value !== 'number') return 'n/a';
  return value.toFixed(digits);
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.kv}>
      <Text style={styles.kvLabel}>{label}</Text>
      <Text style={styles.kvValue}>{value}</Text>
    </View>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {children}
    </View>
  );
}

export default function DetailScreen({ symbol, source, onBack }: Props) {
  const [data, setData] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAnalysis(symbol, {
        source,
        horizon: 5,
        models: ['drift', 'holt', 'ar'],
        wfSplits: 8,
      });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  }, [symbol, source]);

  useEffect(() => {
    load();
  }, [load]);

  const header = (
    <View style={styles.header}>
      <TouchableOpacity onPress={onBack} style={styles.back}>
        <Text style={styles.backText}>‹ Volver</Text>
      </TouchableOpacity>
      <Text style={styles.title}>{symbol}</Text>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.container}>
        {header}
        <View style={styles.center}>
          <ActivityIndicator size="large" />
          <Text style={styles.muted}>Analizando {symbol}...</Text>
        </View>
      </View>
    );
  }

  if (error || !data) {
    return (
      <View style={styles.container}>
        {header}
        <View style={styles.center}>
          <Text style={styles.error}>{error ?? 'Sin datos'}</Text>
          <TouchableOpacity onPress={load} style={styles.retry}>
            <Text style={styles.retryText}>Reintentar</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const { signal, forecast, indicators, fundamentals, risk, backtest } = data;

  return (
    <View style={styles.container}>
      {header}
      <ScrollView contentContainerStyle={styles.scroll}>
        <View style={[styles.badge, { backgroundColor: ACTION_COLORS[signal.action] }]}>
          <Text style={styles.badgeText}>
            {signal.action} · score {num(signal.score)}
          </Text>
        </View>

        <Section title="Pronóstico">
          <Row label="Precio actual" value={num(forecast.last_price)} />
          <Row
            label={`Pronóstico ${forecast.horizon_days}d`}
            value={`${num(forecast.point)} (${pct(forecast.expected_return)})`}
          />
          <Row label="Mejor modelo" value={forecast.best_model} />
          <Row
            label="Banda 95%"
            value={`${num(forecast.lower_95)} – ${num(forecast.upper_95)}`}
          />
          {Object.entries(forecast.models).map(([name, m]) => (
            <Row
              key={name}
              label={`  ${name}`}
              value={`fc ${num(m.forecast)} · RMSE ${num(m.rmse)} · dir ${
                m.dir_acc === null ? 'n/a' : `${Math.round(m.dir_acc * 100)}%`
              }`}
            />
          ))}
        </Section>

        <Section title="Señal — razones">
          {signal.reasons.map((reason, i) => (
            <Text key={i} style={styles.reason}>
              • {reason}
            </Text>
          ))}
        </Section>

        <Section title="Indicadores técnicos">
          <Row label="RSI" value={num(indicators.rsi)} />
          <Row label="MACD hist." value={num(indicators.macd_hist)} />
          <Row
            label="Tendencia"
            value={indicators.trend_up ? 'Alcista' : 'Bajista'}
          />
          <Row label="SMA rápida / lenta" value={`${num(indicators.sma_fast)} / ${num(indicators.sma_slow)}`} />
          <Row label="ATR" value={num(indicators.atr)} />
        </Section>

        <Section title="Fundamental">
          <Row label="Score" value={num(fundamentals.score)} />
          <Row label="P/E" value={num(fundamentals.metrics.pe)} />
          <Row label="ROE" value={pct(fundamentals.metrics.roe)} />
          <Row label="Deuda/Capital" value={num(fundamentals.metrics.debt_to_equity)} />
          <Row label="Margen" value={pct(fundamentals.metrics.profit_margin)} />
        </Section>

        <Section title="Riesgo">
          <Row label="Volatilidad anual" value={pct(risk.annual_vol)} />
          <Row label="Max drawdown" value={pct(risk.max_drawdown)} />
          <Row label="Stop sugerido" value={num(risk.stop_price)} />
          <Row
            label="Tamaño posición"
            value={`${risk.suggested_shares} acc · ${num(risk.position_value, 0)}`}
          />
        </Section>

        <Section title="Backtest (SMA crossover)">
          <Row label="Retorno estrategia" value={pct(backtest.total_return)} />
          <Row label="Buy & Hold" value={pct(backtest.buy_hold_return)} />
          <Row label="Sharpe" value={num(backtest.sharpe)} />
          <Row label="Max drawdown" value={pct(backtest.max_drawdown)} />
          <Row
            label="Win rate · trades"
            value={`${Math.round(backtest.win_rate * 100)}% · ${backtest.trades}`}
          />
        </Section>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 60, paddingHorizontal: 16 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 80 },
  header: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  back: { paddingVertical: 6, paddingRight: 12 },
  backText: { color: '#2563eb', fontSize: 17 },
  title: { fontSize: 26, fontWeight: '700' },
  scroll: { paddingBottom: 40 },
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    marginVertical: 10,
  },
  badgeText: { color: '#fff', fontWeight: '700', fontSize: 15 },
  section: { marginTop: 18 },
  sectionTitle: { fontSize: 16, fontWeight: '700', marginBottom: 8, color: '#111' },
  kv: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 5,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#eee',
  },
  kvLabel: { color: '#555' },
  kvValue: { fontWeight: '600', color: '#111' },
  reason: { color: '#444', paddingVertical: 3 },
  muted: { color: '#7f8c8d', marginTop: 8 },
  error: { color: '#c0392b', marginBottom: 12, textAlign: 'center' },
  retry: { backgroundColor: '#2563eb', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 6 },
  retryText: { color: '#fff', fontWeight: '600' },
});
