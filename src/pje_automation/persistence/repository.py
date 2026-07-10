from __future__ import annotations

from datetime import datetime, timezone
from sqlite3 import Connection

from pje_automation.domain.models import JobRecord, Record
from pje_automation.domain.states import JobState
from pje_automation.utils.names import mask_cpf


class JobRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def upsert(self, record: Record, state: JobState) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """
            INSERT INTO jobs(record_id, nome, cpf_masked, state, resume_state, attempt_count, error_code, error_message, error_details, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, NULL, NULL, NULL, ?)
            ON CONFLICT(record_id) DO UPDATE SET
                nome = excluded.nome,
                cpf_masked = excluded.cpf_masked,
                state = excluded.state,
                resume_state = excluded.resume_state,
                error_code = NULL,
                error_message = NULL,
                error_details = NULL,
                updated_at = excluded.updated_at
            """,
            (record.record_id, record.nome, mask_cpf(record.cpf), state.value, state.value, now),
        )
        self.connection.commit()

    def mark_attempt(self, record: Record) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """
            INSERT INTO jobs(record_id, nome, cpf_masked, state, resume_state, attempt_count, error_code, error_message, error_details, updated_at)
            VALUES (?, ?, ?, ?, NULL, 1, NULL, NULL, NULL, ?)
            ON CONFLICT(record_id) DO UPDATE SET
                nome = excluded.nome,
                cpf_masked = excluded.cpf_masked,
                attempt_count = jobs.attempt_count + 1,
                updated_at = excluded.updated_at
            """,
            (record.record_id, record.nome, mask_cpf(record.cpf), JobState.PENDENTE.value, now),
        )
        self.connection.commit()

    def mark_error(
        self,
        record: Record,
        *,
        resume_state: JobState | None,
        error_code: str | None,
        error_message: str | None,
        error_details: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.connection.execute(
            """
            INSERT INTO jobs(record_id, nome, cpf_masked, state, resume_state, attempt_count, error_code, error_message, error_details, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            ON CONFLICT(record_id) DO UPDATE SET
                nome = excluded.nome,
                cpf_masked = excluded.cpf_masked,
                state = excluded.state,
                resume_state = COALESCE(excluded.resume_state, jobs.resume_state),
                error_code = excluded.error_code,
                error_message = excluded.error_message,
                error_details = excluded.error_details,
                updated_at = excluded.updated_at
            """,
            (
                record.record_id,
                record.nome,
                mask_cpf(record.cpf),
                JobState.ERRO.value,
                resume_state.value if resume_state is not None else None,
                error_code,
                error_message,
                error_details,
                now,
            ),
        )
        self.connection.commit()

    def list_jobs(self) -> list[JobRecord]:
        rows = self.connection.execute(
            """
            SELECT record_id, nome, cpf_masked, state, updated_at, resume_state, attempt_count, error_code, error_message, error_details
            FROM jobs
            ORDER BY updated_at DESC
            """
        ).fetchall()
        return [
            JobRecord(
                record_id=row[0],
                nome=row[1],
                cpf_masked=row[2],
                state=JobState(row[3]),
                updated_at=datetime.fromisoformat(row[4]),
                resume_state=JobState(row[5]) if row[5] else None,
                attempt_count=int(row[6] or 0),
                error_code=row[7],
                error_message=row[8],
                error_details=row[9],
            )
            for row in rows
        ]

    def get_job(self, record_id: str) -> JobRecord | None:
        row = self.connection.execute(
            """
            SELECT record_id, nome, cpf_masked, state, updated_at, resume_state, attempt_count, error_code, error_message, error_details
            FROM jobs
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()
        if row is None:
            return None
        return JobRecord(
            record_id=row[0],
            nome=row[1],
            cpf_masked=row[2],
            state=JobState(row[3]),
            updated_at=datetime.fromisoformat(row[4]),
            resume_state=JobState(row[5]) if row[5] else None,
            attempt_count=int(row[6] or 0),
            error_code=row[7],
            error_message=row[8],
            error_details=row[9],
        )
