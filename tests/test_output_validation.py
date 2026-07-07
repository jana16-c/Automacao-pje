from pathlib import Path
from zipfile import ZipFile

import pytest

from pje_automation.domain.errors import OutputValidationError
from pje_automation.validation.outputs import validate_pdf, validate_pje_archive


def test_validate_pdf_accepts_valid_signature(tmp_path: Path) -> None:
    pdf = tmp_path / "ok.pdf"
    pdf.write_bytes(b"%PDF-" + b"x" * 2000)
    validate_pdf(pdf)


def test_validate_pdf_rejects_small_file(tmp_path: Path) -> None:
    pdf = tmp_path / "bad.pdf"
    pdf.write_bytes(b"%PDF-")
    with pytest.raises(OutputValidationError):
        validate_pdf(pdf)


def test_validate_pje_archive_requires_internal_pjc(tmp_path: Path) -> None:
    archive = tmp_path / "calc.pjc"
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr("calc.pjc", "conteudo")
    assert validate_pje_archive(archive) == ["calc.pjc"]


def test_validate_pje_archive_rejects_plain_text_file(tmp_path: Path) -> None:
    archive = tmp_path / "calc.pjc"
    archive.write_text("nao e pacote", encoding="utf-8")
    with pytest.raises(OutputValidationError):
        validate_pje_archive(archive)
