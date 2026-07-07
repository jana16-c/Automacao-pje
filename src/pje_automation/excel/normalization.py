from __future__ import annotations

import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation


def normalize_header(value: object) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("_", " ").replace("-", " ")
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return " ".join(normalized.split())


def normalize_name_key(value: str) -> str:
    return normalize_header(value).upper()


def normalize_cpf(value: object) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits.zfill(11) if digits else ""


def normalize_date(value: object) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, (int, float)):
        base = datetime(1899, 12, 30)
        return (base + timedelta(days=float(value))).strftime("%d/%m/%Y")

    text = str(value).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return text or None


def parse_decimal(value: object) -> Decimal:
    if value in (None, ""):
        return Decimal("0.00")
    text = str(value).strip().replace(".", "").replace(",", ".")
    try:
        return Decimal(text).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Valor monetario invalido: {value!r}") from exc
