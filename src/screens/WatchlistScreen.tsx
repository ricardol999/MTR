import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { fetchWatchlist } from '../services/marketService';
import { SignalAction, SignalSummary } from '../types/market';

const WATCHLIST = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN'];

const ACTION_COLORS: Record<SignalAction, string> = {
  BUY: '#1b8a5a',
  SELL: '#c0392b',
  HOLD: '#7f8c8d',
};

export type DataSource = 'synthetic' | 'yfinance';

type Props = {
  source: DataSource;
  onToggleSource: (source: DataSource) => void;
  onSelect: (symbol: string) => void;
};

function formatPct(value: number): string {
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`;
}

export default function WatchlistScreen({ source, onToggleSource, onSelect }: Props) {
  const [items, setItems] = useState<SignalSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Modelos ligeros y pocos orígenes de validación: respuesta en segundos.
      const results = await fetchWatchlist(WATCHLIST, {
        horizon: 5,
        models: ['drift', 'holt'],
        wfSplits: 8,
        source,
      });
      setItems(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  }, [source]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Señales del mercado</Text>

      <View style={styles.toggle}>
        {(['synthetic', 'yfinance'] as DataSource[]).map((opt) => (
          <TouchableOpacity
            key={opt}
            onPress={() => onToggleSource(opt)}
            style={[styles.toggleBtn, source === opt && styles.toggleBtnActive]}
          >
            <Text style={[styles.toggleText, source === opt && styles.toggleTextActive]}>
              {opt === 'synthetic' ? 'Sintético' : 'Real (yfinance)'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" />
          <Text style={styles.muted}>Cargando señales...</Text>
        </View>
      ) : (
        <FlatList
          data={items}
          keyExtractor={(item) => item.symbol}
          refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
          renderItem={({ item }) => (
            <TouchableOpacity style={styles.row} onPress={() => onSelect(item.symbol)}>
              <View>
                <Text style={styles.symbol}>{item.symbol}</Text>
                <Text style={styles.muted}>
                  {item.last_price.toFixed(2)} → {item.forecast.toFixed(2)} (
                  {formatPct(item.expected_return)})
                </Text>
              </View>
              <View
                style={[styles.badge, { backgroundColor: ACTION_COLORS[item.action] }]}
              >
                <Text style={styles.badgeText}>{item.action}</Text>
              </View>
            </TouchableOpacity>
          )}
          ListEmptyComponent={<Text style={styles.muted}>Sin datos.</Text>}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 60, paddingHorizontal: 16 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 60 },
  title: { fontSize: 22, fontWeight: '700', marginBottom: 12 },
  toggle: { flexDirection: 'row', marginBottom: 12, gap: 8 },
  toggleBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#eee',
  },
  toggleBtnActive: { backgroundColor: '#2563eb' },
  toggleText: { color: '#555', fontWeight: '600' },
  toggleTextActive: { color: '#fff' },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#ddd',
  },
  symbol: { fontSize: 18, fontWeight: '600' },
  muted: { color: '#7f8c8d', marginTop: 4 },
  error: { color: '#c0392b', marginBottom: 8 },
  badge: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 6 },
  badgeText: { color: '#fff', fontWeight: '700' },
});
