from __future__ import annotations

from pathlib import Path

from pje_automation.diagnostics.dom_probe import DomProbe
from pje_automation.domain.models import WorkbookPreview
from pje_automation.excel.mapper import build_preview
from pje_automation.excel.reader import open_workbook
from pje_automation.gui.main_window import MainWindow
from pje_automation.persistence.database import connect_database
from pje_automation.persistence.repository import JobRepository
from pje_automation.pje.browser import BrowserManager
from pje_automation.pje.selectors import SelectorRepository
from pje_automation.pje.workflow import Workflow
from pje_automation.utils.logging import configure_logging, shutdown_logging
from pje_automation.utils.paths import ensure_output_layout
from pje_automation.validation.inputs import resolve_model_file, validate_app_paths


class Application:
    def __init__(self, base_url_override: str | None = None) -> None:
        self.browser_manager = BrowserManager(base_url_override=base_url_override)
        self.selectors = SelectorRepository()

    def run_gui(self) -> None:
        window = MainWindow(self)
        window.mainloop()

    def validate_inputs(self, model_file: Path, excel_file: Path, output_dir: Path) -> WorkbookPreview:
        paths = validate_app_paths(model_file, excel_file, output_dir)
        self.browser_manager.ensure_pje_available()
        workbook = open_workbook(paths.excel_file)
        try:
            return build_preview(workbook)
        finally:
            workbook.close()

    def run_probe(self, output_dir: Path | None = None):
        base_output = output_dir or Path("output") / "probe"
        base_output.mkdir(parents=True, exist_ok=True)
        probe = DomProbe(browser_manager=self.browser_manager, selectors=self.selectors)
        return probe.run(base_output)

    def run_mvp(self, model_file: Path, excel_file: Path, output_dir: Path) -> str:
        paths = validate_app_paths(model_file, excel_file, output_dir)
        model_resolution = resolve_model_file(paths.model_file)
        layout = ensure_output_layout(paths.output_dir)
        logger = configure_logging(layout.logs_dir / "execucao.log")
        logger.info("Iniciando execucao MVP")
        try:
            workbook = open_workbook(paths.excel_file)
            try:
                preview = build_preview(workbook, limit=1)
            finally:
                workbook.close()
            if not preview.valid_records:
                raise ValueError("Nenhum registro valido foi encontrado na planilha.")

            connection = connect_database(layout.database_path)
            try:
                repository = JobRepository(connection)
                workflow = Workflow(self.browser_manager, self.selectors, repository)
                workflow.run_single_record(
                    record=preview.valid_records[0],
                    model_path=model_resolution.resolved_pjc,
                    pdf_dir=layout.pdf_dir,
                    pjc_dir=layout.pjc_dir,
                    evidence_dir=layout.evidence_dir,
                )
                return f"Registro {preview.valid_records[0].record_id} processado."
            finally:
                connection.close()
        finally:
            shutdown_logging(logger)
