export type SyncStatus = 'pending' | 'synced' | 'failed';

export type ScanRow = {
  id: number;
  barcode: string;
  barcodeType: string;
  labelText: string | null;
  scannedAt: string;
  syncStatus: SyncStatus;
  syncedAt: string | null;
  remoteId: string | null;
  lastError: string | null;
};

export type NewScan = {
  barcode: string;
  barcodeType: string;
  labelText?: string | null;
};

export type ScanPayload = {
  localId: number;
  barcode: string;
  barcodeType: string;
  labelText: string | null;
  scannedAt: string;
};

export type SyncResponse = {
  remoteId?: string | number;
};
