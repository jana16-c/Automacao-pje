from decimal import Decimal

from pje_automation.excel.normalization import normalize_cpf, normalize_date, normalize_header, parse_decimal


def test_normalize_cpf_preserves_leading_zeroes() -> None:
    assert normalize_cpf("1234567890") == "01234567890"


def test_normalize_date_excel_serial() -> None:
    assert normalize_date(45414) == "02/05/2024"


def test_normalize_header_removes_accents() -> None:
    assert normalize_header(" Data Demissão ") == "data demissao"


def test_parse_decimal_accepts_brazilian_format() -> None:
    assert parse_decimal("1.234,56") == Decimal("1234.56")
