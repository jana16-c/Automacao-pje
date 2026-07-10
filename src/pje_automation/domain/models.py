from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .states import JobState


@dataclass(slots=True)
class HistoricalValue:
    competencia: str
    valor: Decimal


@dataclass(slots=True)
class HistoricalSeries:
    nome: str
    valores: list[HistoricalValue] = field(default_factory=list)


@dataclass(slots=True)
class RecordSource:
    sheet: str
    row: int


@dataclass(slots=True)
class Record:
    record_id: str
    nome: str
    cpf: str
    data_admissao: str | None
    data_demissao: str | None
    processo: str | None
    historicos: list[HistoricalSeries]
    source: RecordSource


@dataclass(slots=True)
class WorkbookPreview:
    valid_records: list[Record]
    invalid_rows: list[str]
    ambiguous_rows: list[str]
    sheet_names: list[str]
    ignored_control_sheets: list[str] = field(default_factory=list)
    ignored_history_sheets: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ModelResolution:
    original_path: Path
    resolved_pjc: Path
    extracted_dir: Path | None = None


@dataclass(slots=True)
class OutputLayout:
    root: Path
    pdf_dir: Path
    pjc_dir: Path
    logs_dir: Path
    evidence_dir: Path
    control_dir: Path
    database_path: Path


@dataclass(slots=True)
class AppPaths:
    model_file: Path
    excel_file: Path
    history_file: Path | None
    output_dir: Path


@dataclass(slots=True)
class ProbeResult:
    output_dir: Path
    screenshot_file: Path
    html_file: Path
    elements_file: Path
    selectors_file: Path
    url: str
    generated_at: datetime


@dataclass(slots=True)
class JobRecord:
    record_id: str
    nome: str
    cpf_masked: str
    state: JobState
    updated_at: datetime
    resume_state: JobState | None = None
    attempt_count: int = 0
    error_code: str | None = None
    error_message: str | None = None
    error_details: str | None = None
