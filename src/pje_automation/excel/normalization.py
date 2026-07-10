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


def normalize_registration(value: object) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    digits = "".join(ch for ch in str(value).strip() if ch.isdigit())
    return digits or str(value).strip()


def normalize_process_digits(value: object) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


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


def normalize_competencia(value: object) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.strftime("%m/%Y")
    if isinstance(value, date):
        return value.strftime("%m/%Y")
    if isinstance(value, (int, float)):
        base = datetime(1899, 12, 30)
        return (base + timedelta(days=float(value))).strftime("%m/%Y")

    text = str(value).strip()
    for fmt in ("%m/%Y", "%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%m/%Y")
        except ValueError:
            continue
    return text or None


def parse_decimal(value: object) -> Decimal:
    if value in (None, ""):
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    if isinstance(value, int):
        return Decimal(value).quantize(Decimal("0.01"))
    if isinstance(value, float):
        return Decimal(str(value)).quantize(Decimal("0.01"))
    text = normalize_decimal_text(str(value).strip())
    try:
        return Decimal(text).quantize(Decimal("0.01"))
    except InvalidOperation as exc:
        raise ValueError(f"Valor monetario invalido: {value!r}") from exc


def normalize_decimal_text(text: str) -> str:
    compact = text.replace(" ", "")
    if not compact:
        return compact

    has_dot = "." in compact
    has_comma = "," in compact
    if has_dot and has_comma:
        last_dot = compact.rfind(".")
        last_comma = compact.rfind(",")
        if last_dot > last_comma:
            return compact.replace(",", "")
        return compact.replace(".", "").replace(",", ".")

    if has_comma:
        return normalize_single_separator_decimal(compact, ",")
    if has_dot:
        return normalize_single_separator_decimal(compact, ".")
    return compact


def normalize_single_separator_decimal(text: str, separator: str) -> str:
    if text.count(separator) == 1:
        left, right = text.split(separator)
        if 1 <= len(right) <= 3:
            return f"{left}.{right}"
        return text.replace(separator, "")

    parts = text.split(separator)
    last = parts[-1]
    if 1 <= len(last) <= 3:
        return f"{''.join(parts[:-1])}.{last}"
    return "".join(parts)
