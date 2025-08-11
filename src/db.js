import Database from 'better-sqlite3';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

let dbInstance = null;

export function getDb() {
  if (dbInstance) return dbInstance;
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = path.dirname(__filename);
  const dataDir = path.join(__dirname, '..', 'data');
  if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });
  const dbPath = path.join(dataDir, 'app.db');
  dbInstance = new Database(dbPath);
  dbInstance.pragma('journal_mode = WAL');

  initializeSchema(dbInstance);
  return dbInstance;
}

function initializeSchema(db) {
  db.exec(`
    CREATE TABLE IF NOT EXISTS leads (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      full_name TEXT NOT NULL,
      phone_e164 TEXT NOT NULL,
      email TEXT,
      interest TEXT,
      source TEXT,
      status TEXT,
      qualified_reason TEXT,
      created_at INTEGER,
      updated_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS call_events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      call_sid TEXT,
      status TEXT,
      created_at INTEGER
    );
  `);
}