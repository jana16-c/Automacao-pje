from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_database(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS jobs (
            record_id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            cpf_masked TEXT NOT NULL,
            state TEXT NOT NULL,
            resume_state TEXT,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            error_code TEXT,
            error_message TEXT,
            error_details TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    _ensure_column(connection, "jobs", "resume_state", "TEXT")
    _ensure_column(connection, "jobs", "attempt_count", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(connection, "jobs", "error_details", "TEXT")
    connection.execute(
        """
        UPDATE jobs
        SET resume_state = state
        WHERE resume_state IS NULL
          AND state NOT IN ('ERRO', 'CONCLUIDO')
        """
    )
    connection.commit()
    return connection


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = {
        row[1]
        for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column in existing:
        return
    connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
