from __future__ import annotations

import re
import shutil
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from time import sleep

from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.by import By

from pje_automation.diagnostics.evidence import save_evidence
from pje_automation.domain.errors import AutomationCancelledError, WorkflowExecutionError
from pje_automation.domain.models import HistoricalSeries, Record
from pje_automation.excel.normalization import normalize_cpf, normalize_name_key
from pje_automation.domain.states import JobState
from pje_automation.persistence.repository import JobRepository
from pje_automation.pje.browser import BrowserManager
from pje_automation.pje.downloads import collect_pdf, collect_pjc
from pje_automation.pje.selectors import SelectorRepository
from pje_automation.pje.waits import wait_for_condition, wait_for_page_ready, wait_for_present_element
from pje_automation.utils.names import sanitize_filename
from pje_automation.validation.outputs import validate_pdf, validate_pje_archive


class Workflow:
    def __init__(
        self,
        browser_manager: BrowserManager,
        selectors: SelectorRepository,
        repository: JobRepository,
        should_cancel=None,
        register_driver=None,
    ) -> None:
        self.browser_manager = browser_manager
        self.selectors = selectors
        self.repository = repository
        self.should_cancel = should_cancel
        self.register_driver = register_driver

    def run_single_record(self, record: Record, model_path: Path, pdf_dir: Path, pjc_dir: Path, evidence_dir: Path) -> None:
        self._ensure_not_cancelled()
        self.repository.upsert(record, JobState.VALIDANDO_DADOS)
        with TemporaryDirectory(prefix=f"pje_run_{record.record_id}_") as temp_download_dir:
            temp_dir = Path(temp_download_dir)
            staged_model = self._stage_model_for_browser(model_path, temp_dir)
            driver = self.browser_manager.open_driver(download_dir=temp_dir)
            if self.register_driver is not None:
                self.register_driver(driver)
            try:
                self._ensure_not_cancelled()
                self.browser_manager.open_base_page(driver)
                self._import_model(driver, staged_model, record)
                self._ensure_not_cancelled()
                self._fill_identity(driver, record)
                self._ensure_not_cancelled()
                self._refresh_verbas(driver, record)
                self._ensure_not_cancelled()
                self._refresh_fgts(driver, record)
                self._ensure_not_cancelled()
                self._refresh_contribuicao_social(driver, record)
                self._ensure_not_cancelled()
                self._process_historico(driver, record)
                self._ensure_not_cancelled()
                self._liquidate_and_export(driver, record, pdf_dir, pjc_dir)
                self.repository.upsert(record, JobState.CONCLUIDO)
            except Exception as exc:
                prefix = sanitize_filename(record.record_id)
                save_evidence(driver, evidence_dir / prefix, "erro_fluxo")
                self.repository.upsert(record, JobState.ERRO, error_code="WORKFLOW_ERROR", error_message=str(exc))
                raise
            finally:
                if self.register_driver is not None:
                    self.register_driver(None)
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
        self._ensure_cpf_selected(driver)
        self._wait_for_field_enabled(driver, "calculo.cpf")
        self._fill_document_field_with_retry(driver, "calculo.cpf", record.cpf)
        self.repository.upsert(record, JobState.SALVANDO_PARAMETROS)
        self._click_required(driver, "calculo.salvar")
        self._wait_for_success_feedback(driver, timeout=self._operation_timeout_seconds())
        if record.data_demissao:
            self._open_parameters_tab(driver)
            self._fill_field_if_needed(driver, "calculo.data_demissao", record.data_demissao)
            self._wait_for_field_value(driver, "calculo.data_demissao", record.data_demissao)
            self._fill_field_if_needed(driver, "calculo.data_final", record.data_demissao)
            self._wait_for_field_value(driver, "calculo.data_final", record.data_demissao)
            self._wait_for_idle(driver)
            self.repository.upsert(record, JobState.SALVANDO_PARAMETROS)
            self._click_required(driver, "calculo.salvar")
            self._wait_for_success_feedback(driver, timeout=self._operation_timeout_seconds())

    def _ensure_cpf_selected(self, driver) -> None:
        for locator in self.selectors.get("calculo.cpf_tipo_cpf"):
            try:
                element = wait_for_present_element(driver, locator, timeout=self._element_timeout_seconds())
                driver.execute_script("arguments[0].click();", element)
                self._wait_for_idle(driver)
                return
            except Exception:
                continue
        raise WorkflowExecutionError("SELECTOR_NOT_FOUND", "Nao foi possivel marcar o tipo de documento CPF.")

    def _fill_first_available(self, driver, selector_key: str, value: str) -> None:
        for locator in self.selectors.get(selector_key):
            try:
                field = wait_for_present_element(driver, locator, timeout=self._element_timeout_seconds())
                self._set_field_value(driver, field, value)
                return
            except Exception:
                continue
        raise WorkflowExecutionError("SELECTOR_NOT_FOUND", f"Nao foi possivel preencher {selector_key}.")

    def _fill_field_if_needed(self, driver, selector_key: str, value: str) -> None:
        current_value = self._get_first_field_value(driver, selector_key)
        if current_value == value:
            return
        self._fill_first_available(driver, selector_key, value)

    def _get_first_field_value(self, driver, selector_key: str) -> str:
        for locator in self.selectors.get(selector_key):
            try:
                field = wait_for_present_element(driver, locator, timeout=self._element_timeout_seconds())
                return (field.get_attribute("value") or "").strip()
            except Exception:
                continue
        return ""

    def _set_field_value(self, driver, field, value: str) -> None:
        field_id = field.get_attribute("id") or ""
        masked_value = self._format_masked_document_value(field_id, value)
        effective_value = masked_value or value
        if field_id.endswith("InputDate"):
            driver.execute_script(
                """
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));
                """,
                field,
                effective_value,
            )
            self._sync_calendar_hidden_value(driver, field, effective_value)
            return

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
                effective_value,
            )
            self._sync_calendar_hidden_value(driver, field, effective_value)
            return

        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", field)
            field.click()
            field.clear()
            field.send_keys(effective_value)
            self._sync_calendar_hidden_value(driver, field, effective_value)
            self._pace()
        except Exception:
            driver.execute_script(
                """
                arguments[0].value = arguments[1];
                arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
                arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
                arguments[0].blur();
                """,
                field,
                effective_value,
            )
            self._sync_calendar_hidden_value(driver, field, effective_value)
            self._pace()

    def _fill_document_field_with_retry(self, driver, selector_key: str, value: str, attempts: int = 3) -> None:
        last_error: Exception | None = None
        for _ in range(attempts):
            try:
                self._fill_first_available(driver, selector_key, value)
                self._wait_for_field_match(driver, selector_key, lambda current: normalize_cpf(current) == normalize_cpf(value), timeout=5)
                return
            except Exception as exc:
                last_error = exc
                self._ensure_cpf_selected(driver)
                self._wait_for_field_enabled(driver, selector_key, timeout=5)
        if last_error is not None:
            raise last_error

    def _format_masked_document_value(self, field_id: str, value: str) -> str | None:
        digits = normalize_cpf(value)
        if field_id.endswith("reclamanteNumeroDocumentoFiscal") and len(digits) == 11:
            return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
        return None

    def _open_parameters_tab(self, driver) -> None:
        switched = False
        try:
            switched = bool(
                driver.execute_script(
                    """
                    const panelInput = document.getElementById('formulario:j_id138_input');
                    if (!panelInput || !window.RichFaces || typeof RichFaces.switchTab !== 'function') {
                      return false;
                    }
                    RichFaces.switchTab('formulario:j_id138', 'formulario:tabParametrosCalculo', 'tabParametrosCalculo');
                    return true;
                    """
                )
            )
        except Exception:
            switched = False
        if not switched:
            self._click_required(driver, "calculo.tab_parametros")
        self._wait_for_parameters_tab_ready(driver)

    def _wait_for_parameters_tab_ready(self, driver) -> None:
        def _parameters_ready(current_driver) -> bool:
            return bool(
                current_driver.execute_script(
                    """
                    const panel = document.getElementById('formulario:tabParametrosCalculo');
                    const input = document.getElementById('formulario:j_id138_input');
                    const demissao = document.getElementById('formulario:dataDemissaoInputDate');
                    if (!panel || !input || !demissao) {
                      return false;
                    }
                    const style = window.getComputedStyle(panel);
                    return input.value === 'tabParametrosCalculo' && style.display !== 'none';
                    """
                )
            )

        wait_for_condition(driver, _parameters_ready, timeout=self._operation_timeout_seconds())
        self._wait_for_idle(driver)

    def _sync_calendar_hidden_value(self, driver, field, value: str) -> None:
        field_id = field.get_attribute("id") or ""
        if not field_id.endswith("InputDate"):
            return
        hidden_id = field_id.replace("InputDate", "InputCurrentDate")
        try:
            month_year = datetime.strptime(value, "%d/%m/%Y").strftime("%m/%Y")
        except ValueError:
            return
        driver.execute_script(
            """
            const hidden = document.getElementById(arguments[0]);
            if (!hidden) {
              return;
            }
            hidden.value = arguments[1];
            hidden.dispatchEvent(new Event('input', { bubbles: true }));
            hidden.dispatchEvent(new Event('change', { bubbles: true }));
            """,
            hidden_id,
            month_year,
        )

    def _wait_for_field_value(self, driver, selector_key: str, expected_value: str, timeout: int = 15) -> None:
        self._wait_for_field_match(driver, selector_key, lambda current: current == expected_value, timeout=timeout)

    def _wait_for_field_match(self, driver, selector_key: str, predicate, timeout: int = 15) -> None:
        effective_timeout = max(timeout, self._element_timeout_seconds())
        for locator in self.selectors.get(selector_key):
            try:
                def _matches(current_driver) -> bool:
                    field = wait_for_present_element(current_driver, locator, timeout=effective_timeout)
                    current_value = (field.get_attribute("value") or "").strip()
                    return predicate(current_value)

                wait_for_condition(driver, _matches, timeout=effective_timeout)
                return
            except Exception:
                continue
        raise WorkflowExecutionError("FIELD_NOT_PERSISTED", f"O campo {selector_key} nao permaneceu com o valor esperado.")

    def _wait_for_field_enabled(self, driver, selector_key: str, timeout: int = 15) -> None:
        effective_timeout = max(timeout, self._element_timeout_seconds())
        for locator in self.selectors.get(selector_key):
            try:
                def _enabled(current_driver) -> bool:
                    field = wait_for_present_element(current_driver, locator, timeout=effective_timeout)
                    disabled = field.get_attribute("disabled")
                    return field.is_enabled() and not disabled

                wait_for_condition(driver, _enabled, timeout=effective_timeout)
                return
            except Exception:
                continue
        raise WorkflowExecutionError("FIELD_DISABLED", f"O campo {selector_key} nao habilitou para preenchimento.")

    def _click_required(self, driver, selector_key: str, url_fragment: str | None = None) -> None:
        for locator in self.selectors.get(selector_key):
            try:
                element = wait_for_present_element(driver, locator, timeout=self._element_timeout_seconds())
                driver.execute_script("arguments[0].click();", element)
                if url_fragment:
                    wait_for_condition(driver, lambda current: url_fragment in current.current_url, timeout=self._operation_timeout_seconds())
                self._wait_for_idle(driver)
                return
            except WorkflowExecutionError:
                raise
            except Exception:
                continue
        raise WorkflowExecutionError("SELECTOR_NOT_FOUND", f"Nao foi possivel acionar {selector_key}.")

    def _click_optional(self, driver, selector_key: str) -> None:
        try:
            for locator in self.selectors.get(selector_key):
                try:
                    element = wait_for_present_element(driver, locator, timeout=self._element_timeout_seconds())
                    driver.execute_script("arguments[0].click();", element)
                    self._wait_for_idle(driver)
                    return
                except Exception:
                    continue
        except Exception:
            return

    def _wait_for_idle(self, driver) -> None:
        self._ensure_not_cancelled()
        self._accept_pending_alert(driver, timeout=1.5)
        wait_for_page_ready(driver, timeout=self._element_timeout_seconds())
        self._ensure_not_cancelled()
        self._accept_pending_alert(driver, timeout=0.5)
        self._raise_if_known_business_error(driver)
        self._raise_if_server_error(driver)
        self._pace()

    def _refresh_verbas(self, driver, record: Record) -> None:
        self.repository.upsert(record, JobState.REGERANDO_VERBAS)
        self._click_required(driver, "menu.verbas", url_fragment="verba-calculo.jsf")
        selected = self._select_verbas_for_regeneration(driver)
        if selected <= 0:
            raise WorkflowExecutionError(
                "VERBAS_SEM_SELECAO",
                "Nenhuma verba principal ou reflexo selecionavel foi encontrada para regeracao.",
            )
        self._click_required(driver, "verbas.regerar")
        self._confirm_regeneration(driver, "verbas")

    def _refresh_fgts(self, driver, record: Record) -> None:
        self.repository.upsert(record, JobState.REGERANDO_FGTS)
        self._click_required(driver, "menu.fgts", url_fragment="fgts.jsf")
        self._click_required(driver, "fgts.ocorrencias", url_fragment="parametrizar-fgts.jsf")
        self._click_required(driver, "fgts.regerar")
        self._confirm_regeneration(driver, "fgts")

    def _refresh_contribuicao_social(self, driver, record: Record) -> None:
        self.repository.upsert(record, JobState.REGERANDO_CONTRIBUICAO_SOCIAL)
        self._click_required(driver, "menu.contribuicao_social", url_fragment="inss.jsf")
        self._click_required(driver, "contribuicao.ocorrencias")
        self._click_required(driver, "contribuicao.regerar")
        self._confirm_regeneration(driver, "contribuicao")

    def _process_historico(self, driver, record: Record) -> None:
        self.repository.upsert(record, JobState.PREENCHENDO_HISTORICO)
        self._click_required(driver, "menu.historico_salarial", url_fragment="historico-salarial.jsf")
        historicos = [serie for serie in record.historicos if serie.valores]
        if not historicos:
            return
        for index, serie in enumerate(historicos):
            if index:
                self._click_required(driver, "menu.historico_salarial", url_fragment="historico-salarial.jsf")
            self._edit_historical_series(driver, serie)

    def _liquidate_and_export(self, driver, record: Record, pdf_dir: Path, pjc_dir: Path) -> None:
        self.repository.upsert(record, JobState.LIQUIDANDO)
        self._run_liquidation(driver)

        self.repository.upsert(record, JobState.GERANDO_PDF)
        safe_name = sanitize_filename(record.nome)
        download_dir_raw = getattr(driver, "_pje_download_dir", None)
        download_dir = Path(download_dir_raw) if download_dir_raw else None
        if not download_dir:
            raise WorkflowExecutionError("DOWNLOAD_CONFIG", "Nao foi possivel determinar o diretorio de download do navegador.")

        pdf_path = self._download_pdf(driver, download_dir)
        shutil.move(str(pdf_path), pdf_dir / f"{safe_name}.pdf")

        self.repository.upsert(record, JobState.EXPORTANDO_PJC)
        pjc_path = self._download_pjc(driver, download_dir)
        shutil.move(str(pjc_path), pjc_dir / f"{safe_name}.pjc")

        self.repository.upsert(record, JobState.VALIDANDO_SAIDAS)

    def _download_pdf(self, driver, download_dir: Path) -> Path:
        return self._collect_download_with_retry(
            driver=driver,
            download_dir=download_dir,
            suffix=".pdf",
            output_name="PDF",
            trigger=lambda: (
                self._open_print_page_ready(driver),
                self._click_required(driver, "imprimir.executar"),
            ),
            collector=collect_pdf,
            validator=validate_pdf,
        )

    def _download_pjc(self, driver, download_dir: Path) -> Path:
        return self._collect_download_with_retry(
            driver=driver,
            download_dir=download_dir,
            suffix=".pjc",
            output_name="PJC",
            trigger=lambda: (
                self._click_required(driver, "menu.exportar", url_fragment="exportacao.jsf"),
                self._click_required(driver, "exportar.executar"),
            ),
            collector=collect_pjc,
            validator=validate_pje_archive,
        )

    def _collect_download_with_retry(self, driver, download_dir: Path, suffix: str, output_name: str, trigger, collector, validator) -> Path:
        attempts = self._output_retry_attempts()
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            self._ensure_not_cancelled()
            self._clear_download_artifacts(download_dir, suffix)
            try:
                trigger()
                path = collector(download_dir)
                validator(path)
                return path
            except Exception as exc:
                last_error = exc
                if attempt >= attempts:
                    break
                self._wait_for_idle(driver)
        if last_error is not None:
            raise last_error
        raise WorkflowExecutionError(f"{output_name}_DOWNLOAD_FAILED", f"Falha ao gerar {output_name}.")

    def _clear_download_artifacts(self, download_dir: Path, suffix: str) -> None:
        suffix_lower = suffix.lower()
        for item in download_dir.iterdir():
            name_lower = item.name.lower()
            if item.is_file() and (item.suffix.lower() == suffix_lower or name_lower.endswith(f"{suffix_lower}.crdownload")):
                try:
                    item.unlink()
                except FileNotFoundError:
                    continue

    def _output_retry_attempts(self) -> int:
        return max(1, int(self.browser_manager.config.get("execution", {}).get("output_retry_attempts", 2)))

    def _confirm_regeneration(self, driver, selector_prefix: str) -> None:
        self._accept_pending_alert(driver, timeout=1.5)
        self._click_visible_confirmation_ok(driver)
        self._click_if_present(driver, f"{selector_prefix}.manter_alteracoes", timeout=5)
        self._accept_pending_alert(driver, timeout=1.5)
        self._click_visible_confirmation_ok(driver)
        self._click_if_present(driver, f"{selector_prefix}.confirmar", timeout=5)
        self._accept_pending_alert(driver, timeout=2)
        self._click_visible_confirmation_ok(driver)
        self._wait_for_success_feedback(driver, timeout=self._operation_timeout_seconds())

    def _run_liquidation(self, driver) -> None:
        self._click_required(driver, "menu.liquidar", url_fragment="liquidacao.jsf")
        self._click_required(driver, "liquidar.executar")
        self._wait_for_success_feedback(driver, timeout=self._operation_timeout_seconds())

    def _open_print_page_ready(self, driver) -> None:
        self._click_required(driver, "menu.imprimir", url_fragment="relatorio-calculo.jsf")
        if self._has_stale_report_error(driver):
            self._run_liquidation(driver)
            self._click_required(driver, "menu.imprimir", url_fragment="relatorio-calculo.jsf")
            if self._has_stale_report_error(driver):
                raise WorkflowExecutionError(
                    "RELATORIO_DESATUALIZADO",
                    "O PJe continuou exigindo nova liquidacao antes da impressao.",
                )

    def _edit_historical_series(self, driver, serie: HistoricalSeries) -> None:
        row_index = self._find_history_row(driver, serie.nome)
        edit_button = wait_for_present_element(driver, (By.ID, f"formulario:listagem:{row_index}:alterarHistorico"))
        driver.execute_script("arguments[0].click();", edit_button)
        self._wait_for_idle(driver)

        self._click_optional(driver, "historico.tipo_valor_informado")
        self._fill_historical_grid(driver, serie)
        self._click_required(driver, "historico.salvar")
        self._wait_for_success_feedback(driver, timeout=self._operation_timeout_seconds())

    def _find_history_row(self, driver, historico_nome: str) -> int:
        normalized_name = normalize_name_key(historico_nome)
        row_index = driver.execute_script(
            """
            const target = arguments[0];
            const rows = Array.from(document.querySelectorAll("[id^='formulario:listagem:'][id$=':nome']"));
            for (const row of rows) {
              const text = (row.value || row.innerText || row.textContent || '').trim();
              const normalized = text
                .normalize('NFD')
                .replace(/[\\u0300-\\u036f]/g, '')
                .replace(/[_-]+/g, ' ')
                .replace(/\\s+/g, ' ')
                .trim()
                .toUpperCase();
              if (normalized !== target) {
                continue;
              }
              const match = row.id.match(/formulario:listagem:(\\d+):nome$/);
              if (match) {
                return Number(match[1]);
              }
            }
            return null;
            """,
            normalized_name,
        )
        if row_index is None:
            row_index = self._find_history_row_by_similarity(driver, historico_nome)
        if row_index is None:
            raise WorkflowExecutionError("HISTORICO_NOT_FOUND", f"Historico salarial nao localizado: {historico_nome}")
        return int(row_index)

    def _find_history_row_by_similarity(self, driver, historico_nome: str) -> int | None:
        rows = driver.execute_script(
            """
            return Array.from(document.querySelectorAll("[id^='formulario:listagem:'][id$=':nome']")).map((row) => {
              const match = row.id.match(/formulario:listagem:(\\d+):nome$/);
              if (!match) {
                return null;
              }
              return {
                index: Number(match[1]),
                nome: (row.value || row.innerText || row.textContent || '').trim(),
              };
            }).filter(Boolean);
            """
        )
        target_tokens = self._history_name_tokens(historico_nome)
        if not target_tokens:
            return None

        best_index: int | None = None
        best_score = 0.0
        for item in rows:
            candidate_tokens = self._history_name_tokens(item["nome"])
            if not candidate_tokens:
                continue
            intersection = len(target_tokens & candidate_tokens)
            score = intersection / max(len(target_tokens), len(candidate_tokens))
            if "NOTURNO" in target_tokens and "NOTURNO" in candidate_tokens:
                score += 0.5
            if "ADICIONAL" in target_tokens and "ADICIONAL" in candidate_tokens:
                score += 0.25
            if score > best_score:
                best_score = score
                best_index = int(item["index"])
        if best_score < 0.6:
            return None
        return best_index

    def _history_name_tokens(self, value: str) -> set[str]:
        normalized = (
            value.upper()
            .replace("ADI", "ADICIONAL ")
            .replace("AD.", "ADICIONAL ")
            .replace("AD ", "ADICIONAL ")
            .replace("NOT.", "NOTURNO ")
            .replace("NOT ", "NOTURNO ")
            .replace("REFLE", "REFLEXO ")
        )
        tokens = {
            token
            for token in re.findall(r"[A-Z0-9]+", normalized)
            if token
        }
        replacements = {
            "DIF": "DIFERENCA",
            "AD": "ADICIONAL",
            "ADI": "ADICIONAL",
            "NOT": "NOTURNO",
            "REFLEXOS": "REFLEXO",
        }
        expanded = {replacements.get(token, token) for token in tokens}
        stop_tokens = {
            "DIF",
            "DIFERENCA",
            "REFLEXO",
            "XOS",
            "PAGO",
            "DIV",
            "CALCULO",
            "HOMOLOGADO",
            "VALOR",
            "BASE",
            "DO",
            "DA",
            "DE",
            "220",
        }
        return {token for token in expanded if token not in stop_tokens}

    def _fill_historical_grid(self, driver, serie: HistoricalSeries) -> None:
        grid_rows = driver.execute_script(
            """
            return Array.from(document.querySelectorAll("[id^='formulario:listagemMC:'][id$=':valor']")).map((input) => {
              const match = input.id.match(/formulario:listagemMC:(\\d+):valor$/);
              if (!match) {
                return null;
              }
              const rowIndex = match[1];
              const competencia = document.getElementById(`formulario:listagemMC:${rowIndex}:data`);
              if (!competencia) {
                return null;
              }
              return { competencia: (competencia.textContent || '').trim(), id: input.id };
            }).filter(Boolean);
            """
        )
        input_by_competencia = {item["competencia"]: item["id"] for item in grid_rows}
        missing = [item.competencia for item in serie.valores if item.competencia not in input_by_competencia]
        if missing:
            raise WorkflowExecutionError(
                "HISTORICO_COMPETENCIA",
                f"Competencias nao encontradas no historico: {', '.join(missing[:5])}",
            )

        values_by_competencia = {item["competencia"]: "0,00" for item in grid_rows}
        values_by_competencia.update({item.competencia: self._format_currency(item.valor) for item in serie.valores})
        payload = [{"id": item["id"], "value": values_by_competencia[item["competencia"]]} for item in grid_rows]
        result = driver.execute_async_script(
            """
            const payload = arguments[0];
            const delayMs = arguments[1];
            const done = arguments[arguments.length - 1];
            const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

            (async () => {
              let written = 0;
              for (const item of payload) {
                const input = document.getElementById(item.id);
                if (!input) {
                  continue;
                }
                input.focus();
                input.value = item.value;
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.dispatchEvent(new Event('blur', { bubbles: true }));
                written += 1;
                if (delayMs > 0) {
                  await sleep(delayMs);
                }
              }
              done({ ok: true, written });
            })().catch(error => done({ ok: false, error: String(error) }));
            """,
            payload,
            self._history_delay_ms(),
        )
        if not result or not result.get("ok"):
            raise WorkflowExecutionError("HISTORICO_PREENCHIMENTO", f"Falha ao preencher historico salarial: {result}")
        self._wait_for_idle(driver)
        if self._history_validation_enabled():
            self._validate_history_grid(driver, payload)

    def _format_currency(self, value: Decimal) -> str:
        return f"{value.quantize(Decimal('0.01')):.2f}".replace(".", ",")

    def _select_verbas_for_regeneration(self, driver) -> int:
        selected = driver.execute_script(
            """
            const normalize = (value) => (value || '')
              .normalize('NFD')
              .replace(/[\\u0300-\\u036f]/g, '')
              .replace(/\\s+/g, ' ')
              .trim()
              .toUpperCase();
            const isCandidate = (input) => {
              if (!input || input.disabled || input.type !== 'checkbox') {
                return false;
              }
              const id = input.id || '';
              const name = input.name || '';
              if (id.includes('tipoRegeracao') || name.includes('tipoRegeracao')) {
                return false;
              }
              const row = input.closest('tr');
              const rowText = normalize(row ? (row.innerText || row.textContent) : '');
              return rowText.includes('VERBA PRINCIPAL') || rowText.includes('REFLEXO');
            };
            const preferred = Array.from(document.querySelectorAll("input[type='checkbox']")).filter(isCandidate);
            const fallback = Array.from(document.querySelectorAll("tr input[type='checkbox']")).filter((input) => {
              if (!input || input.disabled || input.checked) {
                return false;
              }
              const id = input.id || '';
              const name = input.name || '';
              return !id.includes('tipoRegeracao') && !name.includes('tipoRegeracao');
            });
            const targets = preferred.length ? preferred : fallback;
            let count = 0;
            for (const input of targets) {
              if (input.checked) {
                count += 1;
                continue;
              }
              input.click();
              input.dispatchEvent(new Event('change', { bubbles: true }));
              if (input.checked) {
                count += 1;
              }
            }
            return count;
            """
        )
        self._wait_for_idle(driver)
        return int(selected or 0)

    def _wait_for_success_feedback(self, driver, timeout: int) -> None:
        def _success_visible(current_driver) -> bool:
            try:
                if self._click_visible_confirmation_ok(current_driver):
                    return False
                self._accept_pending_alert(current_driver, timeout=0)
                self._raise_if_known_business_error(current_driver)
                self._raise_if_server_error(current_driver)
                return bool(
                    current_driver.execute_script(
                        """
                        const labels = Array.from(document.querySelectorAll('.sucesso .rich-messages-label, .sucesso, #divMensagem'));
                        const text = labels.map((node) => node.innerText || node.textContent || '').join(' ').toUpperCase();
                        return text.includes('OPERAÇÃO REALIZADA COM SUCESSO') || text.includes('OPERACAO REALIZADA COM SUCESSO');
                        """
                    )
                )
            except WorkflowExecutionError:
                raise
            except Exception:
                return False

        wait_for_condition(driver, _success_visible, timeout=timeout)
        self._wait_for_idle(driver)

    def _has_stale_report_error(self, driver) -> bool:
        try:
            return bool(
                driver.execute_script(
                    """
                    const text = (document.body.innerText || document.body.textContent || '')
                      .normalize('NFD')
                      .replace(/[\\u0300-\\u036f]/g, '')
                      .toUpperCase();
                    return text.includes('E NECESSARIO LIQUIDAR NOVAMENTE PARA ATUALIZACAO DE DADOS DOS RELATORIOS');
                    """
                )
            )
        except Exception:
            return False

    def _operation_timeout_seconds(self) -> int:
        return int(self.browser_manager.config["pje_calc"].get("operation_timeout_seconds", 180))

    def _click_if_present(self, driver, selector_key: str, timeout: int = 30) -> bool:
        effective_timeout = max(timeout, self._element_timeout_seconds())
        try:
            for locator in self.selectors.get(selector_key):
                try:
                    element = wait_for_present_element(driver, locator, timeout=effective_timeout)
                    driver.execute_script("arguments[0].click();", element)
                    self._wait_for_idle(driver)
                    return True
                except Exception:
                    continue
        except Exception:
            return False
        return False

    def _click_visible_confirmation_ok(self, driver) -> bool:
        try:
            clicked = bool(
                driver.execute_script(
                    """
                    const isVisible = (element) => {
                      if (!element) {
                        return false;
                      }
                      const style = window.getComputedStyle(element);
                      const rect = element.getBoundingClientRect();
                      return style.display !== 'none'
                        && style.visibility !== 'hidden'
                        && rect.width > 0
                        && rect.height > 0;
                    };

                    const textMatches = (element) => {
                      const text = (element.value || element.innerText || element.textContent || '').trim();
                      return ['OK', 'Ok', 'ok'].includes(text);
                    };

                    const candidates = Array.from(
                      document.querySelectorAll("a, button, input[type='button'], input[type='submit'], span")
                    );

                    for (const candidate of candidates) {
                      if (!textMatches(candidate) || !isVisible(candidate)) {
                        continue;
                      }
                      const clickable = candidate.closest("a,button,input,[role='button'],td,span") || candidate;
                      clickable.click();
                      return true;
                    }
                    return false;
                    """
                )
            )
        except Exception:
            return False
        if clicked:
            self._pace()
        return clicked

    def _accept_pending_alert(self, driver, timeout: float = 1.0) -> bool:
        deadline = monotonic() + max(timeout, 0)
        while True:
            try:
                alert = driver.switch_to.alert
                _ = alert.text
                alert.accept()
                self._pace()
                return True
            except NoAlertPresentException:
                if monotonic() >= deadline:
                    return False
                sleep(0.1)
            except Exception:
                return False

    def _page_text(self, driver) -> str:
        return str(
            driver.execute_script(
                """
                return (document.body.innerText || document.body.textContent || '')
                  .normalize('NFD')
                  .replace(/[\\u0300-\\u036f]/g, '')
                  .replace(/\\s+/g, ' ')
                  .trim()
                  .toUpperCase();
                """
            )
        )

    def _raise_if_known_business_error(self, driver) -> None:
        try:
            page_text = self._page_text(driver)
        except Exception:
            return

        if "E NECESSARIO SELECIONAR PELO MENOS UMA VERBA PRINCIPAL OU REFLEXO" in page_text:
            raise WorkflowExecutionError(
                "VERBAS_SEM_SELECAO",
                "O PJe exige selecionar pelo menos uma Verba Principal ou Reflexo antes de regerar.",
            )
        if "REGERAR AS OCORRENCIAS DO FGTS" in page_text:
            raise WorkflowExecutionError(
                "FGTS_REGERAR_PENDENTE",
                "A liquidacao indicou que o FGTS precisa ser regerado novamente antes de prosseguir.",
            )
        if "REGERAR AS OCORRENCIAS DA CONTRIBUICAO SOCIAL" in page_text or "REGERAR AS OCORRENCIAS DE CONTRIBUICAO SOCIAL" in page_text:
            raise WorkflowExecutionError(
                "CONTRIBUICAO_REGERAR_PENDENTE",
                "A liquidacao indicou que a Contribuicao Social precisa ser regerada novamente antes de prosseguir.",
            )

    def _raise_if_server_error(self, driver) -> None:
        try:
            page_text = self._page_text(driver)
        except Exception:
            return
        if "ERRO INTERNO NO SERVIDOR" in page_text or "OCORREU UM ERRO INESPERADO NO SISTEMA" in page_text:
            raise WorkflowExecutionError(
                "PJE_SERVER_ERROR",
                "O PJe retornou erro interno no servidor durante a execucao.",
            )

    def _validate_history_grid(self, driver, payload: list[dict[str, str]]) -> None:
        snapshot = driver.execute_script(
            """
            const payload = arguments[0];
            return {
              count: document.querySelectorAll("[id^='formulario:listagemMC:'][id$=':valor']").length,
              values: payload.map((item) => {
                const input = document.getElementById(item.id);
                return { id: item.id, expected: item.value, current: input ? (input.value || '') : null };
              }),
            };
            """,
            payload,
        )
        if int(snapshot.get("count") or 0) != len(payload):
            raise WorkflowExecutionError("HISTORICO_VALIDACAO", "A grade do historico mudou durante o preenchimento.")
        invalid = [item for item in snapshot.get("values", []) if (item.get("current") or "").strip() != item.get("expected")]
        if invalid:
            raise WorkflowExecutionError("HISTORICO_VALIDACAO", "O PJe nao manteve todos os valores do historico salarial.")

    def _element_timeout_seconds(self) -> int:
        return int(self.browser_manager.config["pje_calc"].get("element_timeout_seconds", 30))

    def _history_delay_ms(self) -> int:
        return int(self.browser_manager.config.get("history_paste", {}).get("delay_ms", 25))

    def _history_validation_enabled(self) -> bool:
        return bool(self.browser_manager.config.get("history_paste", {}).get("validate_first_last_and_count", True))

    def _pace(self) -> None:
        self._ensure_not_cancelled()
        delay_ms = int(self.browser_manager.config.get("execution", {}).get("step_delay_ms", 0))
        if delay_ms > 0:
            sleep(delay_ms / 1000)

    def _ensure_not_cancelled(self) -> None:
        if callable(self.should_cancel) and self.should_cancel():
            raise AutomationCancelledError("AUTOMATION_CANCELLED", "Execucao cancelada pelo usuario.")
