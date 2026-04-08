"""Daily caps for optional Anthropic escalation when NVIDIA/OpenAI-compatible is also configured."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from lawbot.config import settings

METRIC_ANTHROPIC_ESCALATION = "anthropic_escalation"
_METRIC_ANTHROPIC = METRIC_ANTHROPIC_ESCALATION


def _today_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_daily_count(conn: sqlite3.Connection, metric: str, day: str | None = None) -> int:
    d = day or _today_utc()
    row = conn.execute(
        "SELECT count FROM llm_daily_counts WHERE day = ? AND metric = ?",
        (d, metric),
    ).fetchone()
    return int(row[0]) if row else 0


def increment_daily_count(conn: sqlite3.Connection, metric: str, day: str | None = None) -> None:
    d = day or _today_utc()
    conn.execute(
        """
        INSERT INTO llm_daily_counts (day, metric, count) VALUES (?, ?, 1)
        ON CONFLICT(day, metric) DO UPDATE SET count = llm_daily_counts.count + 1
        """,
        (d, metric),
    )
    conn.commit()


def can_use_anthropic_escalation(conn: sqlite3.Connection) -> bool:
    cap = settings.max_anthropic_escalations_per_day
    if cap < 0:
        return True
    if cap == 0:
        return False
    return get_daily_count(conn, _METRIC_ANTHROPIC) < cap


def record_anthropic_escalation(conn: sqlite3.Connection) -> None:
    increment_daily_count(conn, _METRIC_ANTHROPIC)
