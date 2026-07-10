from __future__ import annotations

from pathlib import Path
from threading import Event, Thread
from datetime import datetime
from time import monotonic, sleep
from traceback import format_exception

from openpyxl import Workbook
from selenium.common.exceptions import TimeoutException, WebDriverException

from pje_automation.diagnostics.dom_probe import DomProbe
from pje_automation.domain.errors import AutomationCancelledError, AutomationError
from pje_automation.domain.models import JobRecord, Record, WorkbookPreview
from pje_automation.domain.states import JobState
from pje_automation.excel.mapper import build_preview
from pje_automation.excel.reader import open_workbook
from pje_automation.gui.main_window import MainWindow
from pje_automation.persistence.database import connect_database
from pje_automation.persistence.repository import JobRepository
from pje_automation.pje.browser import BrowserManager
from pje_automation.pje.selectors import SelectorRepository
from pje_automation.pje.workflow import Workflow
from pje_automation.utils.logging import configure_logging, shutdown_logging
from pje_automation.utils.names import mask_cpf, sanitize_filename
from pje_automation.utils.paths import ensure_output_layout
from pje_automation.validation.inputs import resolve_model_file, validate_app_paths


class Application:
    def __init__(self, base_url_override: str | None = None) -> None:
        self.browser_manager = BrowserManager(base_url_override=base_url_override)
        self.selectors = SelectorRepository()
        self._cancel_event = Event()
        self._active_driver = None

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
        self.browser_manager.wait_until_pje_available()
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
        self.clear_stop_request()
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
                workflow = Workflow(
                    self.browser_manager,
                    self.selectors,
                    repository,
                    should_cancel=self.is_stop_requested,
                    register_driver=self.set_active_driver,
                    logger=logger,
                )
                processed_records: list[Record] = []
                failed_records: list[tuple[Record, Exception, JobRecord | None, Path | None]] = []
                continue_on_error = bool(self.browser_manager.config["execution"].get("continue_on_record_error", False))
                execution_plan, skipped_records = self._build_execution_plan(records, repository, layout.pdf_dir, layout.pjc_dir, logger)

                for index, (record, resume_state) in enumerate(execution_plan, start=1):
                    self._ensure_not_cancelled()
                    try:
                        self._run_record_with_retries(
                            workflow=workflow,
                            record=record,
                            model_path=model_resolution.resolved_pjc,
                            pdf_dir=layout.pdf_dir,
                            pjc_dir=layout.pjc_dir,
                            evidence_dir=layout.evidence_dir,
                            logger=logger,
                            resume_state=resume_state,
                        )
                    except Exception as exc:
                        job_snapshot = repository.get_job(record.record_id)
                        detail_log = self._write_failure_detail_log(
                            layout.logs_dir / "falhas",
                            record,
                            exc,
                            job_snapshot,
                            layout.evidence_dir / sanitize_filename(record.record_id),
                        )
                        if not continue_on_error:
                            raise
                        failed_records.append((record, exc, job_snapshot, detail_log))
                        logger.error("Falha definitiva no registro %s: %s | detalhes=%s", record.record_id, exc, detail_log)
                        if index < len(execution_plan):
                            self._maybe_pause_after_batch(index, logger)
                        continue
                    processed_records.append(record)
                    if index < len(execution_plan):
                        self._maybe_pause_after_batch(index, logger)

                self._ensure_not_cancelled()
                failure_report = None
                if failed_records:
                    failure_report = self._write_failure_report(layout.control_dir / "falhas.xlsx", failed_records)
                skipped_count = len(skipped_records)
                if not processed_records and failed_records:
                    return self._build_summary_message(0, len(failed_records), skipped_count, failure_report)
                if failed_records:
                    return self._build_summary_message(len(processed_records), len(failed_records), skipped_count, failure_report)
                if skipped_count:
                    return self._build_summary_message(len(processed_records), 0, skipped_count, failure_report)
                if len(processed_records) == 1:
                    return f"Registro {processed_records[0].record_id} processado."
                return f"{len(processed_records)} registros processados."
            finally:
                connection.close()
        finally:
            self.set_active_driver(None)
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
        resume_state: JobState | None,
    ) -> None:
        max_attempts = self._max_record_attempts()
        last_error: Exception | None = None
        attempt_history: list[dict[str, object]] = []
        resume_state_on_attempt = resume_state
        for attempt in range(1, max_attempts + 1):
            self._ensure_not_cancelled()
            workflow.repository.mark_attempt(record)
            watchdog_heartbeat, watchdog_stop_event, watchdog_thread, watchdog_state = self._start_attempt_watchdog(
                record,
                attempt,
                logger,
            )
            workflow.heartbeat = watchdog_heartbeat
            effective_resume_state = resume_state_on_attempt if (attempt == 1 or self._resume_recent_calculation_enabled()) else None
            try:
                self.browser_manager.wait_until_pje_available()
                logger.info("Tentativa %s/%s para o registro %s", attempt, max_attempts, record.record_id)
                workflow.run_single_record(
                    record=record,
                    model_path=model_path,
                    pdf_dir=pdf_dir,
                    pjc_dir=pjc_dir,
                    evidence_dir=evidence_dir,
                    resume_recent=effective_resume_state is not None,
                    resume_state=effective_resume_state,
                )
                return
            except Exception as exc:
                last_error = exc
                error_attempts = self._max_attempts_for_error(exc)
                current_job = workflow.repository.get_job(record.record_id)
                attempt_history.append(
                    {
                        "attempt": attempt,
                        "max_attempts": error_attempts,
                        "error_code": exc.code if isinstance(exc, AutomationError) else type(exc).__name__,
                        "message": str(exc),
                        "resume_state": effective_resume_state.value if effective_resume_state is not None else "",
                        "watchdog_triggered": watchdog_state["triggered"],
                        "last_context": watchdog_state["last_context"],
                    }
                )
                logger.exception(
                    "Tentativa %s/%s falhou para o registro %s",
                    attempt,
                    error_attempts,
                    record.record_id,
                )
                if isinstance(exc, AutomationError) and exc.code == "RECENT_CALC_NOT_FOUND":
                    resume_state_on_attempt = None
                elif self._resume_recent_calculation_enabled() and current_job is not None:
                    resume_state_on_attempt = current_job.resume_state
                if not self._should_retry_workflow(exc, attempt, error_attempts):
                    setattr(exc, "attempt_history", attempt_history)
                    raise
                logger.warning(
                    "Falha transitoria na tentativa %s/%s para %s: %s",
                    attempt,
                    error_attempts,
                    record.record_id,
                    exc,
                )
                self._sleep_with_cancel(self._retry_backoff_seconds())
            finally:
                workflow.heartbeat = None
                self._stop_attempt_watchdog(watchdog_stop_event, watchdog_thread)
        if last_error is not None:
            setattr(last_error, "attempt_history", attempt_history)
            raise last_error

    def _should_retry_workflow(self, exc: Exception, attempt: int, max_attempts: int) -> bool:
        if attempt >= max_attempts:
            return False
        if isinstance(exc, AutomationError):
            return exc.code in {
                "PJE_SERVER_ERROR",
                "PJE_UNAVAILABLE",
                "RECENT_CALC_NOT_FOUND",
                "SELECTOR_NOT_FOUND",
                "RELATORIO_DESATUALIZADO",
                "FIELD_DISABLED",
                "FIELD_NOT_PERSISTED",
                "HISTORICO_VALIDACAO",
            }
        return isinstance(exc, (TimeoutException, WebDriverException))

    def _max_record_attempts(self) -> int:
        return max(self._default_record_attempts(), self._server_error_attempts())

    def _max_attempts_for_error(self, exc: Exception) -> int:
        if self._is_instability_error(exc):
            return self._server_error_attempts()
        return self._default_record_attempts()

    def _default_record_attempts(self) -> int:
        return max(1, int(self.browser_manager.config["execution"].get("max_retries_per_step", 1)) + 1)

    def _server_error_attempts(self) -> int:
        retries = self.browser_manager.config["execution"].get("max_retries_pje_server_error", 3)
        return max(self._default_record_attempts(), int(retries) + 1)

    def _resume_recent_calculation_enabled(self) -> bool:
        return bool(self.browser_manager.config["execution"].get("resume_recent_calculation", True))

    def _write_failure_report(self, path: Path, failed_records: list[tuple[Record, Exception, JobRecord | None, Path | None]]) -> Path:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Falhas"
        sheet.append(
            [
                "Registro",
                "Nome",
                "CPF",
                "Aba",
                "Linha",
                "Erro",
                "Mensagem",
                "Estado",
                "Retomar de",
                "Tentativas",
                "Detalhes do erro",
                "Log detalhado",
            ]
        )
        for record, exc, job, detail_log in failed_records:
            error_code = exc.code if isinstance(exc, AutomationError) else type(exc).__name__
            sheet.append(
                [
                    record.record_id,
                    record.nome,
                    mask_cpf(record.cpf),
                    record.source.sheet,
                    record.source.row,
                    error_code,
                    str(exc),
                    job.state.value if job is not None else "",
                    job.resume_state.value if job is not None and job.resume_state is not None else "",
                    job.attempt_count if job is not None else "",
                    job.error_details if job is not None else "",
                    str(detail_log) if detail_log else "",
                ]
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            workbook.save(path)
            return path
        except PermissionError:
            fallback = path.with_name(f"{path.stem}_{datetime.now():%Y%m%d_%H%M%S}{path.suffix}")
            workbook.save(fallback)
            return fallback

    def _retry_backoff_seconds(self) -> int:
        return int(self.browser_manager.config["execution"].get("retry_backoff_seconds", 4))

    def _record_watchdog_timeout_seconds(self) -> int:
        return max(30, int(self.browser_manager.config["execution"].get("record_watchdog_timeout_seconds", 240)))

    def _watchdog_poll_seconds(self) -> float:
        return max(1.0, float(self.browser_manager.config["execution"].get("watchdog_poll_seconds", 5)))

    def _cooldown_every_records(self) -> int:
        return max(0, int(self.browser_manager.config["execution"].get("cooldown_every_records", 5)))

    def _cooldown_seconds(self) -> int:
        return max(0, int(self.browser_manager.config["execution"].get("cooldown_seconds", 120)))

    def _resume_previous_run_enabled(self) -> bool:
        return bool(self.browser_manager.config["execution"].get("resume_previous_run", True))

    def _overwrite_valid_outputs_enabled(self) -> bool:
        return bool(self.browser_manager.config["execution"].get("overwrite_valid_outputs", False))

    def _test_mode_first_record_only(self) -> bool:
        return bool(self.browser_manager.config["execution"].get("test_mode_first_record_only", False))

    def request_stop(self) -> None:
        self._cancel_event.set()
        driver = self._active_driver
        if driver is None:
            return
        try:
            driver.quit()
        except Exception:
            return

    def clear_stop_request(self) -> None:
        self._cancel_event.clear()

    def is_stop_requested(self) -> bool:
        return self._cancel_event.is_set()

    def set_active_driver(self, driver) -> None:
        self._active_driver = driver

    def _ensure_not_cancelled(self) -> None:
        if self.is_stop_requested():
            raise AutomationCancelledError("AUTOMATION_CANCELLED", "Execucao cancelada pelo usuario.")

    def _sleep_with_cancel(self, seconds: int) -> None:
        remaining = max(float(seconds), 0.0)
        while remaining > 0:
            self._ensure_not_cancelled()
            interval = min(0.1, remaining)
            sleep(interval)
            remaining -= interval

    def _build_execution_plan(
        self,
        records: list[Record],
        repository: JobRepository,
        pdf_dir: Path,
        pjc_dir: Path,
        logger,
    ) -> tuple[list[tuple[Record, JobState | None]], list[Record]]:
        if not self._resume_previous_run_enabled():
            return [(record, None) for record in records], []

        jobs_by_id = {job.record_id: job for job in repository.list_jobs()}
        plan: list[tuple[Record, JobState | None]] = []
        skipped_records: list[Record] = []
        for record in records:
            existing_job = jobs_by_id.get(record.record_id)
            if self._should_skip_completed_record(record, existing_job, pdf_dir, pjc_dir):
                skipped_records.append(record)
                logger.info("Pulando registro %s porque ele ja esta concluido com saidas presentes.", record.record_id)
                continue
            resume_state = self._resume_state_from_job(existing_job)
            plan.append((record, resume_state))
        return plan, skipped_records

    def _should_skip_completed_record(
        self,
        record: Record,
        existing_job: JobRecord | None,
        pdf_dir: Path,
        pjc_dir: Path,
    ) -> bool:
        if existing_job is None or existing_job.state != JobState.CONCLUIDO:
            return False
        if self._overwrite_valid_outputs_enabled():
            return False
        pdf_path, pjc_path = self._record_output_paths(record, pdf_dir, pjc_dir)
        return pdf_path.exists() and pjc_path.exists()

    def _record_output_paths(self, record: Record, pdf_dir: Path, pjc_dir: Path) -> tuple[Path, Path]:
        safe_name = sanitize_filename(record.nome)
        return pdf_dir / f"{safe_name}.pdf", pjc_dir / f"{safe_name}.pjc"

    def _resume_state_from_job(self, job: JobRecord | None) -> JobState | None:
        if job is None:
            return None
        if job.state == JobState.CONCLUIDO:
            return None
        if job.resume_state is not None:
            return job.resume_state
        if job.state not in {JobState.PENDENTE, JobState.ERRO}:
            return job.state
        return None

    def _is_instability_error(self, exc: Exception) -> bool:
        if isinstance(exc, AutomationError):
            return exc.code in {"PJE_SERVER_ERROR", "PJE_UNAVAILABLE"}
        return isinstance(exc, (TimeoutException, WebDriverException))

    def _maybe_pause_after_batch(self, handled_records: int, logger) -> None:
        cooldown_every = self._cooldown_every_records()
        cooldown_seconds = self._cooldown_seconds()
        if cooldown_every <= 0 or cooldown_seconds <= 0:
            return
        if handled_records % cooldown_every != 0:
            return
        logger.info(
            "Pausa preventiva apos %s calculos concluidos nesta execucao. Aguardando %s segundos.",
            handled_records,
            cooldown_seconds,
        )
        self._sleep_with_cancel(cooldown_seconds)

    def _write_failure_detail_log(
        self,
        directory: Path,
        record: Record,
        exc: Exception,
        job: JobRecord | None,
        evidence_dir: Path,
    ) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = directory / f"{sanitize_filename(record.record_id)}_{timestamp}.log"
        error_code = exc.code if isinstance(exc, AutomationError) else type(exc).__name__
        lines = [
            f"registro={record.record_id}",
            f"nome={record.nome}",
            f"cpf={mask_cpf(record.cpf)}",
            f"aba_origem={record.source.sheet}",
            f"linha_origem={record.source.row}",
            f"erro={error_code}",
            f"mensagem={exc}",
        ]
        if job is not None:
            lines.extend(
                [
                    f"estado_persistido={job.state.value}",
                    f"estado_retomada={job.resume_state.value if job.resume_state is not None else ''}",
                    f"tentativas={job.attempt_count}",
                    f"estado_atualizado_em={job.updated_at.isoformat()}",
                    f"erro_persistido={job.error_code or ''}",
                    f"mensagem_persistida={job.error_message or ''}",
                ]
            )
            if job.error_details:
                lines.extend(
                    [
                        "",
                        "detalhes_persistidos:",
                        job.error_details,
                    ]
                )
        attempt_history = getattr(exc, "attempt_history", [])
        if attempt_history:
            lines.append("")
            lines.append("tentativas:")
            for item in attempt_history:
                lines.append(
                    "- tentativa={attempt} max={max_attempts} resume_state={resume_state} watchdog={watchdog_triggered} ultimo_contexto={last_context} erro={error_code} mensagem={message}".format(
                        **item
                    )
                )
        if evidence_dir.exists():
            evidence_files = sorted(str(item) for item in evidence_dir.iterdir() if item.is_file())
            if evidence_files:
                lines.append("")
                lines.append("evidencias:")
                lines.extend(evidence_files)
        lines.append("")
        lines.append("traceback:")
        lines.extend("".join(format_exception(type(exc), exc, exc.__traceback__)).splitlines())
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _start_attempt_watchdog(self, record: Record, attempt: int, logger):
        state = {
            "last_heartbeat_at": monotonic(),
            "last_context": "START",
            "triggered": False,
        }
        stop_event = Event()

        def heartbeat(context: str | None = None) -> None:
            state["last_heartbeat_at"] = monotonic()
            if context:
                state["last_context"] = context

        def watch() -> None:
            timeout_seconds = self._record_watchdog_timeout_seconds()
            poll_seconds = self._watchdog_poll_seconds()
            while not stop_event.wait(poll_seconds):
                if monotonic() - state["last_heartbeat_at"] < timeout_seconds:
                    continue
                state["triggered"] = True
                logger.error(
                    "Watchdog encerrou a tentativa %s do registro %s apos %s segundos sem progresso. Ultimo contexto=%s",
                    attempt,
                    record.record_id,
                    timeout_seconds,
                    state["last_context"],
                )
                driver = self._active_driver
                if driver is None:
                    return
                try:
                    driver.quit()
                except Exception:
                    return

        thread = Thread(target=watch, name=f"pje-watchdog-{record.record_id}-{attempt}", daemon=True)
        thread.start()
        return heartbeat, stop_event, thread, state

    def _stop_attempt_watchdog(self, stop_event: Event, thread: Thread) -> None:
        stop_event.set()
        thread.join(timeout=1)

    def _build_summary_message(
        self,
        processed_count: int,
        failed_count: int,
        skipped_count: int,
        failure_report: Path | None,
    ) -> str:
        parts: list[str] = []
        if processed_count == 1:
            parts.append("1 registro processado")
        elif processed_count > 1:
            parts.append(f"{processed_count} registros processados")
        else:
            parts.append("Nenhum registro processado")
        if failed_count:
            parts.append(f"{failed_count} com erro")
        if skipped_count:
            parts.append(f"{skipped_count} ja concluidos reaproveitados")
        message = "; ".join(parts) + "."
        if failure_report is not None:
            message = f"{message} Lista: {failure_report}"
        return message
