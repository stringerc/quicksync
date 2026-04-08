from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class MemoryStore:
    conn: sqlite3.Connection

    def ensure_session(self, session_id: str | None) -> str:
        sid = session_id or str(uuid.uuid4())
        self.conn.execute(
            "INSERT OR IGNORE INTO sessions (id, summary, updated_at) VALUES (?, '', ?)",
            (sid, utc_now()),
        )
        self.conn.commit()
        return sid

    def set_profile(self, key: str, value: str) -> None:
        self.conn.execute(
            """
            INSERT INTO profile_kv (key, value, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, value, utc_now()),
        )
        self.conn.commit()

    def get_profile(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM profile_kv WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def all_profile(self) -> dict[str, str]:
        rows = self.conn.execute("SELECT key, value FROM profile_kv").fetchall()
        return {r[0]: r[1] for r in rows}

    def add_timeline(
        self,
        session_id: str,
        kind: str,
        content: str,
        meta: dict[str, Any] | None = None,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO timeline (session_id, kind, content, meta_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, kind, content, json.dumps(meta or {}), utc_now()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def recent_timeline(self, session_id: str, limit: int = 40) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT id, kind, content, meta_json, created_at FROM timeline
            WHERE session_id = ? ORDER BY id DESC LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for r in reversed(rows):
            out.append(
                {
                    "id": r[0],
                    "kind": r[1],
                    "content": r[2],
                    "meta": json.loads(r[3] or "{}"),
                    "created_at": r[4],
                }
            )
        return out

    def append_message(self, session_id: str, role: str, content: str) -> None:
        self.conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, utc_now()),
        )
        self.conn.execute(
            "UPDATE sessions SET updated_at = ? WHERE id = ?",
            (utc_now(), session_id),
        )
        self.conn.commit()

    def recent_messages(self, session_id: str, limit: int = 30) -> list[dict[str, str]]:
        rows = self.conn.execute(
            """
            SELECT role, content, created_at FROM messages
            WHERE session_id = ? ORDER BY id DESC LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in reversed(rows)]

    def count_messages(self, session_id: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return int(row[0]) if row else 0

    def set_session_summary(self, session_id: str, summary: str) -> None:
        self.conn.execute(
            "UPDATE sessions SET summary = ?, updated_at = ? WHERE id = ?",
            (summary, utc_now(), session_id),
        )
        self.conn.commit()

    def get_session_summary(self, session_id: str) -> str | None:
        row = self.conn.execute("SELECT summary FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return row[0] if row else None

    def list_sessions(self, limit: int = 30) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT s.id, s.updated_at, s.summary,
                   (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) AS msg_count,
                   (SELECT content FROM messages m2
                    WHERE m2.session_id = s.id AND m2.role = 'user'
                    ORDER BY m2.id ASC LIMIT 1) AS preview
            FROM sessions s
            ORDER BY datetime(s.updated_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            prev = (r[4] or "")[:120]
            out.append(
                {
                    "session_id": r[0],
                    "updated_at": r[1],
                    "summary": r[2] or "",
                    "message_count": r[3] or 0,
                    "preview": prev,
                }
            )
        return out

    def messages_in_order(self, session_id: str, limit: int = 500) -> list[dict[str, str]]:
        rows = self.conn.execute(
            """
            SELECT role, content, created_at FROM messages
            WHERE session_id = ? ORDER BY id ASC LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
        return [{"role": r[0], "content": r[1], "created_at": r[2]} for r in rows]
