import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import DetailScreen from './src/screens/DetailScreen';
import ScreenScreen from './src/screens/ScreenScreen';
import WatchlistScreen, { DataSource } from './src/screens/WatchlistScreen';

type Tab = 'watchlist' | 'screen';

export default function App() {
  const [selected, setSelected] = useState<string | null>(null);
  const [source, setSource] = useState<DataSource>('synthetic');
  const [tab, setTab] = useState<Tab>('watchlist');

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="auto" />
      {selected ? (
        <DetailScreen
          symbol={selected}
          source={source}
          onBack={() => setSelected(null)}
        />
      ) : (
        <>
          <View style={styles.content}>
            {tab === 'watchlist' ? (
              <WatchlistScreen
                source={source}
                onToggleSource={setSource}
                onSelect={setSelected}
              />
            ) : (
              <ScreenScreen
                source={source}
                onToggleSource={setSource}
                onSelect={setSelected}
              />
            )}
          </View>
          <View style={styles.tabBar}>
            {([
              ['watchlist', 'Señales'],
              ['screen', 'Oportunidades'],
            ] as [Tab, string][]).map(([key, label]) => (
              <TouchableOpacity
                key={key}
                style={styles.tab}
                onPress={() => setTab(key)}
              >
                <Text style={[styles.tabText, tab === key && styles.tabTextActive]}>
                  {label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  content: { flex: 1 },
  tabBar: {
    flexDirection: 'row',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#ddd',
  },
  tab: { flex: 1, alignItems: 'center', paddingVertical: 14 },
  tabText: { color: '#7f8c8d', fontWeight: '600' },
  tabTextActive: { color: '#2563eb' },
});
