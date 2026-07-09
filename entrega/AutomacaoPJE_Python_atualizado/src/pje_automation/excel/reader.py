from __future__ import annotations

from pathlib import Path

from openpyxl import load_workbook
from openpyxl.workbook.workbook import Workbook


def open_workbook(path: Path) -> Workbook:
    return load_workbook(path, data_only=True, read_only=True)
