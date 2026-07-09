from __future__ import annotations

from pathlib import Path

from pje_automation.pje.waits import wait_for_download


def collect_pdf(download_dir: Path) -> Path:
    return wait_for_download(download_dir, ".pdf")


def collect_pjc(download_dir: Path) -> Path:
    return wait_for_download(download_dir, ".pjc")
