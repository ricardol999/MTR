import { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView, StyleSheet } from 'react-native';

import DetailScreen from './src/screens/DetailScreen';
import WatchlistScreen, { DataSource } from './src/screens/WatchlistScreen';

export default function App() {
  const [selected, setSelected] = useState<string | null>(null);
  const [source, setSource] = useState<DataSource>('synthetic');

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
        <WatchlistScreen
          source={source}
          onToggleSource={setSource}
          onSelect={setSelected}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
});
