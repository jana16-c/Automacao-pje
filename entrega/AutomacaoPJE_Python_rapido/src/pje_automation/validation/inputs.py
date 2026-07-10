from __future__ import annotations

import tempfile
from pathlib import Path
from zipfile import ZipFile

from pje_automation.domain.execution import ExecutionMode, execution_mode_requires_model
from pje_automation.domain.errors import InputValidationError
from pje_automation.domain.models import AppPaths, ModelResolution


def validate_app_paths(
    model_file: Path | None,
    excel_file: Path,
    output_dir: Path,
    history_file: Path | None = None,
    execution_mode: ExecutionMode = ExecutionMode.NOVO_CALCULO,
) -> AppPaths:
    resolved_model_file = model_file
    if execution_mode_requires_model(execution_mode):
        if resolved_model_file is None or not resolved_model_file.exists():
            raise InputValidationError("MODEL_INVALID", "Arquivo modelo nao encontrado")
        if resolved_model_file.suffix.lower() not in {".pjc", ".zip"}:
            raise InputValidationError("MODEL_INVALID", "Modelo deve ser .pjc ou .zip")
    if not excel_file.exists():
        raise InputValidationError("EXCEL_MAPPING_ERROR", "Planilha nao encontrada")
    if excel_file.suffix.lower() not in {".xlsx", ".xlsm"}:
        raise InputValidationError("EXCEL_MAPPING_ERROR", "Planilha deve ser .xlsx ou .xlsm")
    if history_file is not None:
        if not history_file.exists():
            raise InputValidationError("EXCEL_MAPPING_ERROR", "Planilha de historico nao encontrada")
        if history_file.suffix.lower() not in {".xlsx", ".xlsm"}:
            raise InputValidationError("EXCEL_MAPPING_ERROR", "Planilha de historico deve ser .xlsx ou .xlsm")
    output_dir.mkdir(parents=True, exist_ok=True)
    return AppPaths(model_file=resolved_model_file, excel_file=excel_file, history_file=history_file, output_dir=output_dir)


def resolve_model_file(path: Path) -> ModelResolution:
    if path.suffix.lower() == ".pjc":
        return ModelResolution(original_path=path, resolved_pjc=path)

    temp_dir = Path(tempfile.mkdtemp(prefix="pje_model_"))
    with ZipFile(path) as archive:
        pjc_files = [name for name in archive.namelist() if name.lower().endswith(".pjc")]
        if len(pjc_files) != 1:
            raise InputValidationError(
                "MODEL_INVALID",
                "O ZIP do modelo precisa conter exatamente um arquivo .pjc",
            )
        archive.extract(pjc_files[0], temp_dir)
        extracted = temp_dir / pjc_files[0]
        return ModelResolution(original_path=path, resolved_pjc=extracted, extracted_dir=temp_dir)
