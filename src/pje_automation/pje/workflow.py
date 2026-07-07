from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from pje_automation.diagnostics.evidence import save_evidence
from pje_automation.domain.errors import WorkflowExecutionError
from pje_automation.domain.models import Record
from pje_automation.domain.states import JobState
from pje_automation.persistence.repository import JobRepository
from pje_automation.pje.browser import BrowserManager
from pje_automation.pje.downloads import collect_pdf, collect_pjc
from pje_automation.pje.selectors import SelectorRepository
from pje_automation.pje.waits import wait_for_condition, wait_for_element, wait_for_page_ready, wait_for_present_element
from pje_automation.utils.names import sanitize_filename
from pje_automation.validation.outputs import validate_pdf, validate_pje_archive


class Workflow:
    def __init__(self, browser_manager: BrowserManager, selectors: SelectorRepository, repository: JobRepository) -> None:
        self.browser_manager = browser_manager
        self.selectors = selectors
        self.repository = repository

    def run_single_record(self, record: Record, model_path: Path, pdf_dir: Path, pjc_dir: Path, evidence_dir: Path) -> None:
        self.repository.upsert(record, JobState.VALIDANDO_DADOS)
        with TemporaryDirectory(prefix=f"pje_run_{record.record_id}_") as temp_download_dir:
            temp_dir = Path(temp_download_dir)
            staged_model = self._stage_model_for_browser(model_path, temp_dir)
            driver = self.browser_manager.open_driver(download_dir=temp_dir)
            try:
                self.browser_manager.open_base_page(driver)
                self._import_model(driver, staged_model, record)
                self._fill_identity(driver, record)
                self._refresh_verbas(driver, record)
                self._refresh_fgts(driver, record)
                self._refresh_contribuicao_social(driver, record)
                self._process_historico(driver, record)
                self._liquidate_and_export(driver, record, pdf_dir, pjc_dir)
                self.repository.upsert(record, JobState.CONCLUIDO)
            except Exception as exc:
                prefix = sanitize_filename(record.record_id)
                save_evidence(driver, evidence_dir / prefix, "erro_fluxo")
                self.repository.upsert(record, JobState.ERRO, error_code="WORKFLOW_ERROR", error_message=str(exc))
                raise
            finally:
                driver.quit()

    def _stage_model_for_browser(self, model_path: Path, staging_dir: Path) -> Path:
        staged = staging_dir / "modelo_importacao.pjc"
        shutil.copyfile(model_path, staged)
        return staged

    def _import_model(self, driver, model_path: Path, record: Record) -> None:
        self.repository.upsert(record, JobState.IMPORTANDO_MODELO)
        clicked_import = False
        for selector_key in ("home.importar_calculo", "probe.menu.importar"):
            try:
                for locator in self.selectors.get(selector_key):
                    try:
                        action = wait_for_present_element(driver, locator)
                        driver.execute_script("arguments[0].click();", action)
                        self._wait_for_idle(driver)
                        clicked_import = True
                        break
                    except Exception:
                        continue
                if clicked_import:
                    break
            except Exception:
                continue

        for locator in self.selectors.get("import.file_input"):
            try:
                field = wait_for_present_element(driver, locator)
                field.send_keys(str(model_path.resolve()))
                if not clicked_import:
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", field)
                self._click_optional(driver, "import.confirmar")
                self._wait_for_idle(driver)
                return
            except Exception:
                continue
        raise WorkflowExecutionError("SELECTOR_NOT_FOUND", "Nao foi possivel localizar o input de importacao do modelo.")

    def _fill_identity(self, driver, record: Record) -> None:
        self.repository.upsert(record, JobState.PREENCHENDO_IDENTIFICACAO)
        self._fill_first_available(driver, "calculo.nome_reclamante", record.nome)
        self._fill_first_available(driver, "calculo.cpf", record.cpf)
        if record.data_demissao:
            self._click_required(driver, "calculo.tab_parametros")
            self._fill_first_available(driver, "calculo.data_final", record.data_demissao)
        self.repository.upsert(record, JobState.SALVANDO_PARAMETROS)
        self._click_required(driver, "calculo.salvar")
        self._wait_for_idle(driver)

    def _fill_first_available(self, driver, selector_key: str, value: str) -> None:
        for locator in self.selectors.get(selector_key):
            try:
                field = wait_for_present_element(driver, locator)
                self._set_field_value(driver, field, value)
                return
            except Exception:
                continue
        raise WorkflowExecutionError("SELECTOR_NOT_FOUND", f"Nao foi possivel preencher {selector_key}.")

    def _set_field_value(self, driver, field, value: str) -> None:
        disabled = field.get_attribute("disabled")
        readonly = field.get_attribute("readonly")
        if disabled or readonly or not field.is_enabled():
            driver.execute_script(
                """
                arguments[0].removeAttribute('disabled');
                arguments[0].removeAttribute('readonly');
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                arguments[0].blur();
                """,
                field,
                value,
            )
            return

        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
            field.click()
            field.clear()
            field.send_keys(value)
        except Exception:
            driver.execute_script(
                """
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                arguments[0].blur();
                """,
                field,
                value,
            )

    def _click_required(self, driver, selector_key: str, url_fragment: str | None = None) -> None:
        for locator in self.selectors.get(selector_key):
            try:
                element = wait_for_present_element(driver, locator)
                driver.execute_script("arguments[0].click();", element)
                if url_fragment:
                    wait_for_condition(driver, lambda current: url_fragment in current.current_url, timeout=30)
                self._wait_for_idle(driver)
                return
            except Exception:
                continue
        raise WorkflowExecutionError("SELECTOR_NOT_FOUND", f"Nao foi possivel acionar {selector_key}.")

    def _click_optional(self, driver, selector_key: str) -> None:
        try:
            for locator in self.selectors.get(selector_key):
                try:
                    element = wait_for_present_element(driver, locator)
                    driver.execute_script("arguments[0].click();", element)
                    self._wait_for_idle(driver)
                    return
                except Exception:
                    continue
        except Exception:
            return

    def _wait_for_idle(self, driver) -> None:
        wait_for_page_ready(driver, timeout=30)

    def _refresh_verbas(self, driver, record: Record) -> None:
        self.repository.upsert(record, JobState.REGERANDO_VERBAS)
        self._click_required(driver, "menu.verbas")

    def _refresh_fgts(self, driver, record: Record) -> None:
        self.repository.upsert(record, JobState.REGERANDO_FGTS)
        self._click_required(driver, "menu.fgts", url_fragment="fgts.jsf")
        self._click_required(driver, "fgts.salvar")

    def _refresh_contribuicao_social(self, driver, record: Record) -> None:
        self.repository.upsert(record, JobState.REGERANDO_CONTRIBUICAO_SOCIAL)
        self._click_required(driver, "menu.contribuicao_social", url_fragment="inss.jsf")
        self._click_required(driver, "contribuicao.salvar")

    def _process_historico(self, driver, record: Record) -> None:
        self.repository.upsert(record, JobState.PREENCHENDO_HISTORICO)
        self._click_required(driver, "menu.historico_salarial", url_fragment="historico-salarial.jsf")
        if not any(serie.valores for serie in record.historicos):
            return

    def _liquidate_and_export(self, driver, record: Record, pdf_dir: Path, pjc_dir: Path) -> None:
        self.repository.upsert(record, JobState.LIQUIDANDO)
        self._click_required(driver, "menu.liquidar", url_fragment="liquidacao.jsf")
        self._click_required(driver, "liquidar.executar")

        self.repository.upsert(record, JobState.GERANDO_PDF)
        safe_name = sanitize_filename(record.nome)
        download_dir_raw = getattr(driver, "_pje_download_dir", None)
        download_dir = Path(download_dir_raw) if download_dir_raw else None
        if not download_dir:
            raise WorkflowExecutionError("DOWNLOAD_CONFIG", "Nao foi possivel determinar o diretorio de download do navegador.")

        self._click_required(driver, "menu.imprimir", url_fragment="relatorio-calculo.jsf")
        self._click_required(driver, "imprimir.executar")
        pdf_path = collect_pdf(download_dir)
        validate_pdf(pdf_path)
        shutil.move(str(pdf_path), pdf_dir / f"{safe_name}.pdf")

        self.repository.upsert(record, JobState.EXPORTANDO_PJC)
        self._click_required(driver, "menu.exportar", url_fragment="exportacao.jsf")
        self._click_required(driver, "exportar.executar")
        pjc_path = collect_pjc(download_dir)
        validate_pje_archive(pjc_path)
        shutil.move(str(pjc_path), pjc_dir / f"{safe_name}.pjc")

        self.repository.upsert(record, JobState.VALIDANDO_SAIDAS)
