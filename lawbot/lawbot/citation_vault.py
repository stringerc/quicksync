from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def chunk_id_from_text(source_system: str, verbatim: str) -> str:
    h = hashlib.sha256(f"{source_system}:{verbatim}".encode()).hexdigest()[:16]
    return f"chk_{h}"


_WS_RE = re.compile(r"\s+")


def normalize_for_match(s: str) -> str:
    return _WS_RE.sub(" ", s.strip()).lower()


@dataclass
class CitationVault:
    conn: sqlite3.Connection

    def store_chunk(
        self,
        source_system: str,
        verbatim_text: str,
        source_url: str | None = None,
        citation_label: str | None = None,
        raw_meta: dict[str, Any] | None = None,
    ) -> str:
        cid = chunk_id_from_text(source_system, verbatim_text)
        self.conn.execute(
            """
            INSERT OR REPLACE INTO citation_chunks
            (id, source_system, source_url, citation_label, verbatim_text, retrieved_at, raw_meta_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid,
                source_system,
                source_url,
                citation_label,
                verbatim_text,
                utc_now(),
                json.dumps(raw_meta or {}),
            ),
        )
        self.conn.commit()
        return cid

    def get_chunk(self, chunk_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT id, source_system, source_url, citation_label, verbatim_text, raw_meta_json FROM citation_chunks WHERE id = ?",
            (chunk_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "source_system": row[1],
            "source_url": row[2],
            "citation_label": row[3],
            "verbatim_text": row[4],
            "meta": json.loads(row[5] or "{}"),
        }

    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT id, source_system, source_url, citation_label,
                   substr(verbatim_text, 1, 400) AS excerpt, retrieved_at
            FROM citation_chunks ORDER BY retrieved_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "id": r[0],
                "source_system": r[1],
                "source_url": r[2],
                "citation_label": r[3],
                "excerpt": r[4],
                "retrieved_at": r[5],
            }
            for r in rows
        ]


def verify_quotes_in_vault(answer_text: str, vault: CitationVault, allowed_ids: list[str]) -> tuple[bool, list[str]]:
    """
    Check that text inside <quote chunk="chk_...">...</quote> exists in vault for that id.
    """
    errors: list[str] = []
    pattern = re.compile(r'<quote\s+chunk="([^"]+)">\s*(.*?)\s*</quote>', re.DOTALL | re.IGNORECASE)
    for m in pattern.finditer(answer_text):
        cid, inner = m.group(1), m.group(2)
        if cid not in allowed_ids:
            errors.append(f"Chunk id {cid} not in current retrieval set.")
            continue
        row = vault.get_chunk(cid)
        if not row:
            errors.append(f"Unknown chunk id {cid}.")
            continue
        n_inner = normalize_for_match(inner)
        n_ver = normalize_for_match(row["verbatim_text"])
        if n_inner not in n_ver and n_inner != n_ver:
            errors.append(f"Quote body does not match vault text for {cid}.")
    return (len(errors) == 0, errors)


def new_session_retrieval_id() -> str:
    return f"ret_{uuid.uuid4().hex[:12]}"
