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

import { fetchScreen } from '../services/marketService';
import { ScreenRow, SignalAction } from '../types/market';
import { DataSource } from './WatchlistScreen';

const ACTION_COLORS: Record<SignalAction, string> = {
  BUY: '#1b8a5a',
  SELL: '#c0392b',
  HOLD: '#7f8c8d',
};

type Universe = 'emerging' | 'large';

type Props = {
  source: DataSource;
  onToggleSource: (source: DataSource) => void;
  onSelect: (symbol: string) => void;
};

function formatPct(value: number): string {
  return `${value >= 0 ? '+' : ''}${(value * 100).toFixed(1)}%`;
}

// Verde fuerte para alta solidez, ámbar media, gris baja.
function solidityColor(value: number): string {
  if (value >= 0.6) return '#1b8a5a';
  if (value >= 0.45) return '#d68910';
  return '#7f8c8d';
}

export default function ScreenScreen({ source, onToggleSource, onSelect }: Props) {
  const [universe, setUniverse] = useState<Universe>('emerging');
  const [rows, setRows] = useState<ScreenRow[]>([]);
  const [skipped, setSkipped] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchScreen({
        universe,
        source,
        horizon: 5,
        models: ['drift', 'holt', 'ar'],
        wfSplits: 8,
      });
      setRows(data.ranked);
      setSkipped(data.errors.map((e) => e.symbol));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido');
    } finally {
      setLoading(false);
    }
  }, [universe, source]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Oportunidades</Text>
      <Text style={styles.subtitle}>Rankeadas por solidez del pronóstico</Text>

      <View style={styles.toggle}>
        {(['emerging', 'large'] as Universe[]).map((opt) => (
          <TouchableOpacity
            key={opt}
            onPress={() => setUniverse(opt)}
            style={[styles.toggleBtn, universe === opt && styles.toggleBtnActive]}
          >
            <Text
              style={[styles.toggleText, universe === opt && styles.toggleTextActive]}
            >
              {opt === 'emerging' ? 'Emergentes' : 'Grandes'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

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
          <Text style={styles.muted}>
            Analizando universo{source === 'yfinance' ? ' (datos reales, puede tardar)' : ''}...
          </Text>
        </View>
      ) : (
        <FlatList
          data={rows}
          keyExtractor={(item) => item.symbol}
          refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
          renderItem={({ item, index }) => (
            <TouchableOpacity style={styles.row} onPress={() => onSelect(item.symbol)}>
              <View style={styles.rank}>
                <Text style={styles.rankText}>{index + 1}</Text>
              </View>
              <View style={styles.body}>
                <View style={styles.headerRow}>
                  <Text style={styles.symbol}>{item.symbol}</Text>
                  <View
                    style={[styles.badge, { backgroundColor: ACTION_COLORS[item.action] }]}
                  >
                    <Text style={styles.badgeText}>{item.action}</Text>
                  </View>
                </View>
                <Text style={styles.muted}>
                  {item.last_price.toFixed(2)} → {item.forecast.toFixed(2)} (
                  {formatPct(item.expected_return)}) · dir {(item.direction_reliability * 100).toFixed(0)}%
                  {item.fundamental_score !== null
                    ? ` · fund ${item.fundamental_score >= 0 ? '+' : ''}${item.fundamental_score.toFixed(2)}`
                    : ''}
                </Text>
                <View style={styles.barTrack}>
                  <View
                    style={[
                      styles.barFill,
                      {
                        width: `${Math.round(item.solidity * 100)}%`,
                        backgroundColor: solidityColor(item.solidity),
                      },
                    ]}
                  />
                </View>
              </View>
              <Text style={[styles.solidity, { color: solidityColor(item.solidity) }]}>
                {(item.solidity * 100).toFixed(0)}
              </Text>
            </TouchableOpacity>
          )}
          ListEmptyComponent={<Text style={styles.muted}>Sin resultados.</Text>}
          ListFooterComponent={
            skipped.length ? (
              <Text style={styles.skipped}>No se pudo analizar: {skipped.join(', ')}</Text>
            ) : null
          }
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 60, paddingHorizontal: 16 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 60 },
  title: { fontSize: 22, fontWeight: '700' },
  subtitle: { color: '#7f8c8d', marginBottom: 12 },
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
    alignItems: 'center',
    paddingVertical: 14,
    gap: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#ddd',
  },
  rank: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#eef2ff',
    alignItems: 'center',
    justifyContent: 'center',
  },
  rankText: { color: '#2563eb', fontWeight: '700' },
  body: { flex: 1 },
  headerRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  symbol: { fontSize: 18, fontWeight: '600' },
  muted: { color: '#7f8c8d', marginTop: 4 },
  barTrack: {
    height: 6,
    borderRadius: 3,
    backgroundColor: '#eee',
    marginTop: 8,
    overflow: 'hidden',
  },
  barFill: { height: 6, borderRadius: 3 },
  solidity: { fontSize: 20, fontWeight: '700', width: 34, textAlign: 'right' },
  badge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6 },
  badgeText: { color: '#fff', fontWeight: '700', fontSize: 12 },
  error: { color: '#c0392b', marginBottom: 8 },
  skipped: { color: '#b9770e', marginTop: 12, fontSize: 12 },
});
