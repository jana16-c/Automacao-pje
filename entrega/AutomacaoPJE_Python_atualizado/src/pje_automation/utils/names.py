from __future__ import annotations

import re


INVALID_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
MULTIPLE_UNDERSCORES = re.compile(r"_+")


def sanitize_filename(value: str, fallback: str = "registro") -> str:
    cleaned = INVALID_WINDOWS_CHARS.sub("_", value.strip())
    cleaned = cleaned.rstrip(". ")
    cleaned = MULTIPLE_UNDERSCORES.sub("_", cleaned)
    cleaned = cleaned.strip("_")
    return cleaned or fallback


def mask_cpf(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if len(digits) < 4:
        return "***"
    return f"{digits[:3]}.***.***-{digits[-2:]}"
