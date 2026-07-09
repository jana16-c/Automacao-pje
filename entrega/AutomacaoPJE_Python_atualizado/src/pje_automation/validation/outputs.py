from __future__ import annotations

from pathlib import Path
from zipfile import BadZipFile, ZipFile

from pje_automation.domain.errors import OutputValidationError


def validate_pdf(path: Path) -> None:
    if not path.exists() or path.stat().st_size < 1024:
        raise OutputValidationError("PDF_INVALID", "PDF ausente ou pequeno demais")
    with path.open("rb") as handle:
        if handle.read(5) != b"%PDF-":
            raise OutputValidationError("PDF_INVALID", "Arquivo nao possui assinatura PDF")


def validate_pje_archive(path: Path) -> list[str]:
    if not path.exists() or path.stat().st_size == 0:
        raise OutputValidationError("PJC_INVALID", "Arquivo exportado ausente ou vazio")

    try:
        with ZipFile(path) as archive:
            corrupted = archive.testzip()
            if corrupted:
                raise OutputValidationError("PJC_INVALID", f"Item corrompido: {corrupted}")
            pjc_files = [name for name in archive.namelist() if name.lower().endswith(".pjc")]
            if not pjc_files:
                raise OutputValidationError("PJC_INVALID", "Arquivo exportado nao contem .pjc interno")
            return pjc_files
    except BadZipFile as exc:
        raise OutputValidationError("PJC_INVALID", "Arquivo exportado nao e um pacote PJe valido") from exc


def validate_pje_zip(path: Path) -> list[str]:
    return validate_pje_archive(path)
