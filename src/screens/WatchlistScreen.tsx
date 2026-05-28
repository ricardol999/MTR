import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
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

function formatPct(value: number): string {
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(2)}%`;
}

export default function WatchlistScreen() {
  const [items, setItems] = useState<SignalSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const results = await fetchWatchlist(WATCHLIST, { horizon: 5 });
      setItems(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
        <Text style={styles.muted}>Cargando señales...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Señales del mercado</Text>
      {error ? <Text style={styles.error}>{error}</Text> : null}
      <FlatList
        data={items}
        keyExtractor={(item) => item.symbol}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
        renderItem={({ item }) => (
          <View style={styles.row}>
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
          </View>
        )}
        ListEmptyComponent={<Text style={styles.muted}>Sin datos.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 60, paddingHorizontal: 16 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 22, fontWeight: '700', marginBottom: 12 },
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
