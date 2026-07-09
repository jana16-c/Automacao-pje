from __future__ import annotations

import logging
from pathlib import Path

from .names import mask_cpf


class CpfMaskingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rendered = super().format(record)
        return mask_cpf(rendered) if rendered.isdigit() and len(rendered) == 11 else rendered


def configure_logging(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("pje_automation")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream)
    logger.addHandler(file_handler)
    return logger


def shutdown_logging(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        handler.flush()
        handler.close()
        logger.removeHandler(handler)
