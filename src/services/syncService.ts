import { listScans } from '../db/database';

const API_URL =
  process.env.EXPO_PUBLIC_SYNC_API_URL ??
  'http://192.168.1.100:3000/api/scans';

export async function syncPendingScans() {
  const scans = await listScans();

  const pending = scans.filter(
    (scan) => scan.syncStatus !== 'synced'
  );

  let synced = 0;
  let failed = 0;

  for (const scan of pending) {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          localId: scan.id,
          barcode: scan.barcode,
          barcodeType: scan.barcodeType,
          labelText: scan.labelText,
          scannedAt: scan.scannedAt,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      synced++;
    } catch (error) {
      failed++;
      console.error('Sync failed:', error);
    }
  }

  return {
    total: pending.length,
    synced,
    failed,
  };
}