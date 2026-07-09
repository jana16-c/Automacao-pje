from __future__ import annotations

from pathlib import Path
from time import sleep

from pje_automation.diagnostics.dom_probe import DomProbe
from pje_automation.domain.errors import AutomationError
from pje_automation.domain.models import Record, WorkbookPreview
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
            preview = build_preview(workbook, history_workbook=history_workbook, limit=None)
            preview.valid_records = self._select_records_for_execution(
                preview,
                history_file_provided=history_workbook is not None,
                apply_test_mode_limit=True,
            )
            return preview
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
                preview = build_preview(workbook, history_workbook=history_workbook, limit=None)
                records = self._select_records_for_execution(
                    preview,
                    history_file_provided=history_workbook is not None,
                    apply_test_mode_limit=True,
                )
            finally:
                if history_workbook is not None:
                    history_workbook.close()
                workbook.close()
            if not records:
                raise ValueError("Nenhum registro valido foi encontrado na planilha.")

            connection = connect_database(layout.database_path)
            try:
                repository = JobRepository(connection)
                workflow = Workflow(self.browser_manager, self.selectors, repository)
                processed_records: list[Record] = []
                failed_records: list[str] = []
                continue_on_error = bool(self.browser_manager.config["execution"].get("continue_on_record_error", False))

                for record in records:
                    try:
                        self._run_record_with_retries(
                            workflow=workflow,
                            record=record,
                            model_path=model_resolution.resolved_pjc,
                            pdf_dir=layout.pdf_dir,
                            pjc_dir=layout.pjc_dir,
                            evidence_dir=layout.evidence_dir,
                            logger=logger,
                        )
                    except Exception as exc:
                        if not continue_on_error:
                            raise
                        failed_records.append(f"{record.record_id}: {exc}")
                        logger.error("Falha definitiva no registro %s: %s", record.record_id, exc)
                        continue
                    processed_records.append(record)

                if not processed_records and failed_records:
                    raise ValueError(f"Nenhum registro foi processado com sucesso. Primeiro erro: {failed_records[0]}")
                if failed_records:
                    return f"{len(processed_records)} registros processados; {len(failed_records)} com erro."
                if len(processed_records) == 1:
                    return f"Registro {processed_records[0].record_id} processado."
                return f"{len(processed_records)} registros processados."
            finally:
                connection.close()
        finally:
            shutdown_logging(logger)

    def _select_records_for_execution(
        self,
        preview: WorkbookPreview,
        history_file_provided: bool,
        apply_test_mode_limit: bool,
    ) -> list[Record]:
        records = list(preview.valid_records)
        if history_file_provided:
            matched_records = [record for record in records if any(serie.valores for serie in record.historicos)]
            if not matched_records:
                raise ValueError(
                    "Nenhum registro da planilha de controle correspondeu ao historico salarial por CPF, matricula ou nome."
                )
            records = matched_records

        if apply_test_mode_limit and self._test_mode_first_record_only():
            return records[:1]
        return records

    def _run_record_with_retries(
        self,
        workflow: Workflow,
        record: Record,
        model_path: Path,
        pdf_dir: Path,
        pjc_dir: Path,
        evidence_dir: Path,
        logger,
    ) -> None:
        max_attempts = max(1, int(self.browser_manager.config["execution"].get("max_retries_per_step", 1)) + 1)
        last_error: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info("Tentativa %s/%s para o registro %s", attempt, max_attempts, record.record_id)
                workflow.run_single_record(
                    record=record,
                    model_path=model_path,
                    pdf_dir=pdf_dir,
                    pjc_dir=pjc_dir,
                    evidence_dir=evidence_dir,
                )
                return
            except Exception as exc:
                last_error = exc
                if not self._should_retry_workflow(exc, attempt, max_attempts):
                    raise
                logger.warning("Falha transitoria na tentativa %s/%s para %s: %s", attempt, max_attempts, record.record_id, exc)
                sleep(self._retry_backoff_seconds())
        if last_error is not None:
            raise last_error

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

    def _test_mode_first_record_only(self) -> bool:
        return bool(self.browser_manager.config["execution"].get("test_mode_first_record_only", False))
