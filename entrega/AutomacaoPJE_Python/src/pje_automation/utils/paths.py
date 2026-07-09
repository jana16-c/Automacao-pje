from __future__ import annotations

from pathlib import Path

from pje_automation.domain.models import OutputLayout


def ensure_output_layout(root: Path) -> OutputLayout:
    pdf_dir = root / "PDF"
    pjc_dir = root / "PJC"
    logs_dir = root / "logs"
    evidence_dir = root / "evidencias"
    control_dir = root / "controle"

    for path in (pdf_dir, pjc_dir, logs_dir, evidence_dir, control_dir):
        path.mkdir(parents=True, exist_ok=True)

    return OutputLayout(
        root=root,
        pdf_dir=pdf_dir,
        pjc_dir=pjc_dir,
        logs_dir=logs_dir,
        evidence_dir=evidence_dir,
        control_dir=control_dir,
        database_path=control_dir / "execucao.sqlite3",
    )
