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
            error_code TEXT,
            error_message TEXT,
            updated_at TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection
