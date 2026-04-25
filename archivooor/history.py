"""SQLite-backed history tracking for archival submissions."""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 1

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS submissions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    url           TEXT    NOT NULL,
    job_id        TEXT    UNIQUE,
    submitted_at  TEXT    NOT NULL,
    status        TEXT    NOT NULL,
    original_url  TEXT,
    timestamp     TEXT,
    duration_sec  REAL,
    status_ext    TEXT,
    completed_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_submissions_url ON submissions (url);
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions (status);
CREATE INDEX IF NOT EXISTS idx_submissions_submitted_at ON submissions (submitted_at);
"""


def _default_db_path() -> str:
    try:
        import click

        app_dir = click.get_app_dir("archivooor")
    except ImportError:
        app_dir = os.path.join(os.path.expanduser("~"), ".config", "archivooor")
    return os.path.join(app_dir, "history.db")


class HistoryDB:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _default_db_path()
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._local = threading.local()
        conn = self._get_connection()
        self._init_db(conn)

    def _get_connection(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn = conn
        return conn

    def _init_db(self, conn: sqlite3.Connection) -> None:
        (version,) = conn.execute("PRAGMA user_version").fetchone()
        if version < SCHEMA_VERSION:
            conn.executescript(_SCHEMA_SQL)
            conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            conn.commit()

    def record_submission(
        self, url: str, job_id: Optional[str], status: str
    ) -> Optional[int]:
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        try:
            cur = conn.execute(
                "INSERT INTO submissions (url, job_id, submitted_at, status) VALUES (?, ?, ?, ?)",
                (url, job_id, now, status),
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            logger.debug("Duplicate job_id %s for url %s", job_id, url)
            return None

    def update_completion(
        self,
        job_id: str,
        status: str,
        original_url: Optional[str] = None,
        timestamp: Optional[str] = None,
        duration_sec: Optional[float] = None,
        status_ext: Optional[str] = None,
    ) -> None:
        conn = self._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """\
            UPDATE submissions
            SET status = ?, original_url = ?, timestamp = ?,
                duration_sec = ?, status_ext = ?, completed_at = ?
            WHERE job_id = ?""",
            (status, original_url, timestamp, duration_sec, status_ext, now, job_id),
        )
        conn.commit()

    def query(
        self,
        url: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        conn = self._get_connection()
        clauses: list[str] = []
        params: list[object] = []
        if url:
            clauses.append("url LIKE ?")
            params.append(f"%{url}%")
        if status:
            clauses.append("status = ?")
            params.append(status)
        if since:
            clauses.append("submitted_at >= ?")
            params.append(since)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM submissions{where} ORDER BY submitted_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def clear(self) -> int:
        conn = self._get_connection()
        cur = conn.execute("DELETE FROM submissions")
        conn.commit()
        return cur.rowcount

    def close(self) -> None:
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None
