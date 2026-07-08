from __future__ import annotations

from pathlib import Path
from time import sleep

from pje_automation.diagnostics.dom_probe import DomProbe
from pje_automation.domain.errors import AutomationError
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

    def validate_inputs(
        self,
        model_file: Path,
        excel_file: Path,
        output_dir: Path,
        history_file: Path | None = None,
    ) -> WorkbookPreview:
        paths = validate_app_paths(model_file, excel_file, output_dir, history_file=history_file)
        self.browser_manager.ensure_pje_available()
        workbook = open_workbook(paths.excel_file)
        history_workbook = open_workbook(paths.history_file) if paths.history_file else None
        try:
            return build_preview(workbook, history_workbook=history_workbook)
        finally:
            if history_workbook is not None:
                history_workbook.close()
            workbook.close()

    def run_probe(self, output_dir: Path | None = None):
        base_output = output_dir or Path("output") / "probe"
        base_output.mkdir(parents=True, exist_ok=True)
        probe = DomProbe(browser_manager=self.browser_manager, selectors=self.selectors)
        return probe.run(base_output)

    def run_mvp(
        self,
        model_file: Path,
        excel_file: Path,
        output_dir: Path,
        history_file: Path | None = None,
    ) -> str:
        paths = validate_app_paths(model_file, excel_file, output_dir, history_file=history_file)
        model_resolution = resolve_model_file(paths.model_file)
        layout = ensure_output_layout(paths.output_dir)
        logger = configure_logging(layout.logs_dir / "execucao.log")
        logger.info("Iniciando execucao MVP")
        try:
            workbook = open_workbook(paths.excel_file)
            history_workbook = open_workbook(paths.history_file) if paths.history_file else None
            try:
                preview = build_preview(workbook, history_workbook=history_workbook, limit=1)
            finally:
                if history_workbook is not None:
                    history_workbook.close()
                workbook.close()
            if not preview.valid_records:
                raise ValueError("Nenhum registro valido foi encontrado na planilha.")

            connection = connect_database(layout.database_path)
            try:
                repository = JobRepository(connection)
                workflow = Workflow(self.browser_manager, self.selectors, repository)
                max_attempts = max(1, int(self.browser_manager.config["execution"].get("max_retries_per_step", 1)) + 1)
                last_error: Exception | None = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        logger.info("Tentativa %s/%s para o registro %s", attempt, max_attempts, preview.valid_records[0].record_id)
                        workflow.run_single_record(
                            record=preview.valid_records[0],
                            model_path=model_resolution.resolved_pjc,
                            pdf_dir=layout.pdf_dir,
                            pjc_dir=layout.pjc_dir,
                            evidence_dir=layout.evidence_dir,
                        )
                        break
                    except Exception as exc:
                        last_error = exc
                        if not self._should_retry_workflow(exc, attempt, max_attempts):
                            raise
                        logger.warning("Falha transitória na tentativa %s/%s: %s", attempt, max_attempts, exc)
                        sleep(self._retry_backoff_seconds())
                else:
                    if last_error is not None:
                        raise last_error
                return f"Registro {preview.valid_records[0].record_id} processado."
            finally:
                connection.close()
        finally:
            shutdown_logging(logger)

    def _should_retry_workflow(self, exc: Exception, attempt: int, max_attempts: int) -> bool:
        if attempt >= max_attempts:
            return False
        if isinstance(exc, AutomationError):
            return exc.code in {
                "PJE_SERVER_ERROR",
                "SELECTOR_NOT_FOUND",
                "RELATORIO_DESATUALIZADO",
                "FIELD_DISABLED",
                "FIELD_NOT_PERSISTED",
                "HISTORICO_VALIDACAO",
            }
        return False

    def _retry_backoff_seconds(self) -> int:
        return int(self.browser_manager.config["execution"].get("retry_backoff_seconds", 4))
