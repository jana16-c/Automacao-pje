from __future__ import annotations

from datetime import datetime, timezone
from sqlite3 import Connection

from pje_automation.domain.models import JobRecord, Record
from pje_automation.domain.states import JobState
from pje_automation.utils.names import mask_cpf


class JobRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def upsert(self, record: Record, state: JobState, error_code: str | None = None, error_message: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """
            INSERT INTO jobs(record_id, nome, cpf_masked, state, error_code, error_message, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(record_id) DO UPDATE SET
                nome = excluded.nome,
                cpf_masked = excluded.cpf_masked,
                state = excluded.state,
                error_code = excluded.error_code,
                error_message = excluded.error_message,
                updated_at = excluded.updated_at
            """,
            (record.record_id, record.nome, mask_cpf(record.cpf), state.value, error_code, error_message, now),
        )
        self.connection.commit()

    def list_jobs(self) -> list[JobRecord]:
        rows = self.connection.execute(
            "SELECT record_id, nome, cpf_masked, state, updated_at, error_code, error_message FROM jobs ORDER BY updated_at DESC"
        ).fetchall()
        return [
            JobRecord(
                record_id=row[0],
                nome=row[1],
                cpf_masked=row[2],
                state=JobState(row[3]),
                updated_at=datetime.fromisoformat(row[4]),
                error_code=row[5],
                error_message=row[6],
            )
            for row in rows
        ]
