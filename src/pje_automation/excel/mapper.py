from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from openpyxl.workbook.workbook import Workbook

from pje_automation.domain.models import HistoricalSeries, Record, RecordSource, WorkbookPreview
from pje_automation.excel.normalization import normalize_cpf, normalize_date, normalize_header


HEADER_ALIASES = {
    "nome": {"nome", "reclamante", "empregado", "nome reclamante"},
    "cpf": {"cpf", "cpf reclamante", "documento", "documento fiscal"},
    "data_admissao": {"admissao", "data admissao", "dt admissao"},
    "data_demissao": {"demissao", "data demissao", "dt demissao", "data final"},
    "processo": {"processo", "numero processo", "numero do processo"},
}


@dataclass(slots=True)
class SheetMapping:
    header_row: int
    columns: dict[str, int]


def build_preview(workbook: Workbook, limit: int = 20) -> WorkbookPreview:
    valid_records: list[Record] = []
    invalid_rows: list[str] = []
    ambiguous_rows: list[str] = []

    for worksheet in workbook.worksheets:
        mapping = detect_mapping(worksheet.iter_rows(values_only=True))
        if not mapping:
            continue

        for row_index, row in enumerate(
            worksheet.iter_rows(min_row=mapping.header_row + 1, values_only=True),
            start=mapping.header_row + 1,
        ):
            nome = cell_value(row, mapping.columns.get("nome"))
            if not nome:
                continue
            cpf = normalize_cpf(cell_value(row, mapping.columns.get("cpf")))
            data_demissao = normalize_date(cell_value(row, mapping.columns.get("data_demissao")))
            if not cpf or not data_demissao:
                invalid_rows.append(f"{worksheet.title}:{row_index}")
                continue

            record_id = cpf or f"{worksheet.title}-{row_index}"
            valid_records.append(
                Record(
                    record_id=record_id,
                    nome=str(nome).strip(),
                    cpf=cpf,
                    data_admissao=normalize_date(cell_value(row, mapping.columns.get("data_admissao"))),
                    data_demissao=data_demissao,
                    processo=to_optional_str(cell_value(row, mapping.columns.get("processo"))),
                    historicos=[HistoricalSeries(nome="BASE INFORMADA", valores=[])],
                    source=RecordSource(sheet=worksheet.title, row=row_index),
                )
            )
            if len(valid_records) >= limit:
                break
        if len(valid_records) >= limit:
            break

    if not valid_records:
        ambiguous_rows.append("Nenhuma linha elegivel foi encontrada com nome, CPF e data de demissao.")

    return WorkbookPreview(
        valid_records=valid_records,
        invalid_rows=invalid_rows,
        ambiguous_rows=ambiguous_rows,
        sheet_names=workbook.sheetnames,
    )


def detect_mapping(rows: Iterable[tuple[object, ...]]) -> SheetMapping | None:
    for row_index, row in enumerate(rows, start=1):
        columns: dict[str, int] = {}
        for index, value in enumerate(row):
            header = normalize_header(value)
            if not header:
                continue
            for field, aliases in HEADER_ALIASES.items():
                if header in aliases:
                    columns[field] = index
        if "nome" in columns and "cpf" in columns and "data_demissao" in columns:
            return SheetMapping(header_row=row_index, columns=columns)
        if row_index >= 15:
            break
    return None


def cell_value(row: tuple[object, ...], index: int | None) -> object | None:
    if index is None or index >= len(row):
        return None
    return row[index]


def to_optional_str(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None
