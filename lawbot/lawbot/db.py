import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS profile_kv (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS timeline (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  content TEXT NOT NULL,
  meta_json TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS citation_chunks (
  id TEXT PRIMARY KEY,
  source_system TEXT NOT NULL,
  source_url TEXT,
  citation_label TEXT,
  verbatim_text TEXT NOT NULL,
  retrieved_at TEXT NOT NULL DEFAULT (datetime('now')),
  raw_meta_json TEXT
);

CREATE TABLE IF NOT EXISTS sessions (
  id TEXT PRIMARY KEY,
  summary TEXT,
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE TABLE IF NOT EXISTS llm_daily_counts (
  day TEXT NOT NULL,
  metric TEXT NOT NULL,
  count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, metric)
);

-- Session-scoped embedding RAG: cosine retrieval over prior chat excerpts (see lawbot/session_rag.py).
CREATE TABLE IF NOT EXISTS session_embedding_chunks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  vault_chunk_id TEXT NOT NULL,
  embedding_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(session_id, vault_chunk_id)
);

-- CourtListener search result cache (full retrieval payload JSON) to cut duplicate API calls.
CREATE TABLE IF NOT EXISTS cl_search_cache (
  query_key TEXT PRIMARY KEY,
  response_json TEXT NOT NULL,
  created_at REAL NOT NULL DEFAULT (strftime('%s', 'now'))
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
