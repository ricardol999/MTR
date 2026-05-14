import * as SQLite from 'expo-sqlite';

import { NewScan, ScanRow, SyncStatus } from '../types/scan';

const DATABASE_NAME = 'mtr_scanner.db';

let dbPromise: Promise<SQLite.SQLiteDatabase> | null = null;

function getDb() {
  if (!dbPromise) {
    dbPromise = SQLite.openDatabaseAsync(DATABASE_NAME);
  }

  return dbPromise;
}

function mapScanRow(row: Record<string, unknown>): ScanRow {
  return {
    id: Number(row.id),
    barcode: String(row.barcode),
    barcodeType: String(row.barcode_type),
    labelText: row.label_text === null ? null : String(row.label_text),
    scannedAt: String(row.scanned_at),
    syncStatus: String(row.sync_status) as SyncStatus,
    syncedAt: row.synced_at === null ? null : String(row.synced_at),
    remoteId: row.remote_id === null ? null : String(row.remote_id),
    lastError: row.last_error === null ? null : String(row.last_error),
  };
}

export async function initializeDatabase() {
  const db = await getDb();

  await db.execAsync(`
    PRAGMA journal_mode = WAL;

    CREATE TABLE IF NOT EXISTS scans (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      barcode TEXT NOT NULL,
      barcode_type TEXT NOT NULL,
      label_text TEXT,
      scanned_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
      sync_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (sync_status IN ('pending', 'synced', 'failed')),
      synced_at TEXT,
      remote_id TEXT,
      last_error TEXT
    );
  `);
}

export async function insertScan(scan: NewScan) {
  const db = await getDb();

  const result = await db.runAsync(
    `INSERT INTO scans
     (barcode, barcode_type, label_text, sync_status)
     VALUES (?, ?, ?, 'pending')`,
    [
      scan.barcode,
      scan.barcodeType,
      scan.labelText ?? null,
    ]
  );

  return result.lastInsertRowId;
}

export async function listScans(limit = 50) {
  const db = await getDb();

  const rows =
    await db.getAllAsync<Record<string, unknown>>(
      `SELECT *
       FROM scans
       ORDER BY datetime(scanned_at) DESC
       LIMIT ?`,
      [limit]
    );

  return rows.map(mapScanRow);
}