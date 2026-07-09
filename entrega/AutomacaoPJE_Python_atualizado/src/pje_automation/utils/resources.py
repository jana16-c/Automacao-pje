from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative: str) -> Path:
    relative_path = Path(relative)

    if getattr(sys, "frozen", False):
        executable_root = Path(sys.executable).resolve().parent
        external_candidate = executable_root / relative_path
        if external_candidate.exists():
            return external_candidate

    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[3]))
    return base / relative_path
