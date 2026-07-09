from pathlib import Path

from pje_automation.domain.errors import AutomationCancelledError, OutputValidationError, WorkflowExecutionError
from pje_automation.pje.workflow import Workflow


def build_workflow() -> Workflow:
    workflow = Workflow.__new__(Workflow)
    workflow.browser_manager = type("BrowserManagerStub", (), {"config": {"pje_calc": {"operation_timeout_seconds": 180}}})()
    return workflow


def test_raise_if_known_business_error_maps_verbas_selection_error() -> None:
    workflow = build_workflow()
    driver = type("DriverStub", (), {"execute_script": lambda self, script: "E NECESSARIO SELECIONAR PELO MENOS UMA VERBA PRINCIPAL OU REFLEXO"})()

    try:
        workflow._raise_if_known_business_error(driver)
    except WorkflowExecutionError as exc:
        assert exc.code == "VERBAS_SEM_SELECAO"
    else:
        raise AssertionError("Era esperado erro de selecao de verbas.")


def test_raise_if_known_business_error_maps_fgts_pending_error() -> None:
    workflow = build_workflow()
    driver = type("DriverStub", (), {"execute_script": lambda self, script: "E NECESSARIO REGERAR AS OCORRENCIAS DO FGTS"})()

    try:
        workflow._raise_if_known_business_error(driver)
    except WorkflowExecutionError as exc:
        assert exc.code == "FGTS_REGERAR_PENDENTE"
    else:
        raise AssertionError("Era esperado erro de FGTS pendente.")


def test_raise_if_known_business_error_maps_contribuicao_pending_error() -> None:
    workflow = build_workflow()
    driver = type("DriverStub", (), {"execute_script": lambda self, script: "E NECESSARIO REGERAR AS OCORRENCIAS DA CONTRIBUICAO SOCIAL"})()

    try:
        workflow._raise_if_known_business_error(driver)
    except WorkflowExecutionError as exc:
        assert exc.code == "CONTRIBUICAO_REGERAR_PENDENTE"
    else:
        raise AssertionError("Era esperado erro de contribuicao social pendente.")


def test_history_name_tokens_match_adicional_noturno_series() -> None:
    workflow = build_workflow()

    assert workflow._history_name_tokens("dif ad.not+ Reflexos") == {"ADICIONAL", "NOTURNO"}


def test_sync_calendar_hidden_value_updates_current_month_year() -> None:
    workflow = build_workflow()

    class FieldStub:
        def get_attribute(self, name):
            if name == "id":
                return "formulario:dataDemissaoInputDate"
            return None

    calls = []

    class DriverStub:
        def execute_script(self, script, hidden_id, month_year):
            calls.append((hidden_id, month_year))

    workflow._sync_calendar_hidden_value(DriverStub(), FieldStub(), "24/03/2016")

    assert calls == [("formulario:dataDemissaoInputCurrentDate", "03/2016")]


def test_wait_for_field_value_accepts_matching_value() -> None:
    workflow = build_workflow()
    workflow.selectors = type(
        "SelectorsStub",
        (),
        {"get": lambda self, key: [("id", "campo")]},
    )()

    class FieldStub:
        def get_attribute(self, name):
            if name == "value":
                return "24/03/2016"
            return None

    class DriverStub:
        pass

    original = __import__("pje_automation.pje.workflow", fromlist=["wait_for_present_element", "wait_for_condition"])
    saved_present = original.wait_for_present_element
    saved_condition = original.wait_for_condition
    try:
        original.wait_for_present_element = lambda driver, locator, timeout=30: FieldStub()
        original.wait_for_condition = lambda driver, predicate, timeout=30: predicate(driver)
        workflow._wait_for_field_value(DriverStub(), "calculo.data_demissao", "24/03/2016")
    finally:
        original.wait_for_present_element = saved_present
        original.wait_for_condition = saved_condition


def test_wait_for_field_match_accepts_masked_cpf_digits() -> None:
    workflow = build_workflow()
    workflow.selectors = type(
        "SelectorsStub",
        (),
        {"get": lambda self, key: [("id", "campo")]},
    )()

    class FieldStub:
        def get_attribute(self, name):
            if name == "value":
                return "081.367.163-90"
            return None

    class DriverStub:
        pass

    original = __import__("pje_automation.pje.workflow", fromlist=["wait_for_present_element", "wait_for_condition"])
    saved_present = original.wait_for_present_element
    saved_condition = original.wait_for_condition
    try:
        original.wait_for_present_element = lambda driver, locator, timeout=30: FieldStub()
        original.wait_for_condition = lambda driver, predicate, timeout=30: predicate(driver)
        workflow._wait_for_field_match(DriverStub(), "calculo.cpf", lambda current: "".join(ch for ch in current if ch.isdigit()) == "08136716390")
    finally:
        original.wait_for_present_element = saved_present
        original.wait_for_condition = saved_condition


def test_wait_for_field_enabled_accepts_enabled_field() -> None:
    workflow = build_workflow()
    workflow.selectors = type(
        "SelectorsStub",
        (),
        {"get": lambda self, key: [("id", "campo")]},
    )()

    class FieldStub:
        def is_enabled(self):
            return True

        def get_attribute(self, name):
            return None

    class DriverStub:
        pass

    original = __import__("pje_automation.pje.workflow", fromlist=["wait_for_present_element", "wait_for_condition"])
    saved_present = original.wait_for_present_element
    saved_condition = original.wait_for_condition
    try:
        original.wait_for_present_element = lambda driver, locator, timeout=30: FieldStub()
        original.wait_for_condition = lambda driver, predicate, timeout=30: predicate(driver)
        workflow._wait_for_field_enabled(DriverStub(), "calculo.cpf")
    finally:
        original.wait_for_present_element = saved_present
        original.wait_for_condition = saved_condition


def test_wait_for_parameters_tab_ready_accepts_active_panel() -> None:
    workflow = build_workflow()
    calls = []

    class DriverStub:
        def execute_script(self, script):
            calls.append(script)
            return True

    original = __import__("pje_automation.pje.workflow", fromlist=["wait_for_condition"])
    saved_condition = original.wait_for_condition
    try:
        original.wait_for_condition = lambda driver, predicate, timeout=30: predicate(driver)
        workflow._wait_for_idle = lambda driver: None
        workflow._wait_for_parameters_tab_ready(DriverStub())
    finally:
        original.wait_for_condition = saved_condition

    assert len(calls) == 1


def test_ensure_cpf_selected_clicks_even_when_radio_is_already_selected() -> None:
    workflow = build_workflow()
    workflow.selectors = type(
        "SelectorsStub",
        (),
        {"get": lambda self, key: [("id", "cpf-radio")]},
    )()
    workflow._wait_for_idle = lambda driver: None

    class FieldStub:
        def is_selected(self):
            return True

    calls = []

    class DriverStub:
        def execute_script(self, script, element):
            calls.append((script, element))

    original = __import__("pje_automation.pje.workflow", fromlist=["wait_for_present_element"])
    saved_present = original.wait_for_present_element
    try:
        original.wait_for_present_element = lambda driver, locator, timeout=30: FieldStub()
        workflow._ensure_cpf_selected(DriverStub())
    finally:
        original.wait_for_present_element = saved_present

    assert len(calls) == 1


def test_accept_pending_alert_confirms_native_dialog() -> None:
    workflow = build_workflow()
    workflow._pace = lambda: None

    accepted = []

    class AlertStub:
        text = "Confirmar"

        def accept(self):
            accepted.append(True)

    class SwitchToStub:
        @property
        def alert(self):
            return AlertStub()

    class DriverStub:
        switch_to = SwitchToStub()

    assert workflow._accept_pending_alert(DriverStub(), timeout=0) is True
    assert accepted == [True]


def test_click_visible_confirmation_ok_clicks_html_modal_button() -> None:
    workflow = build_workflow()
    paced = []
    workflow._pace = lambda: paced.append(True)

    class DriverStub:
        def execute_script(self, script):
            return True

    assert workflow._click_visible_confirmation_ok(DriverStub()) is True
    assert paced == [True]


def test_workflow_ensure_not_cancelled_raises_when_requested() -> None:
    workflow = build_workflow()
    workflow.should_cancel = lambda: True

    try:
        workflow._ensure_not_cancelled()
    except AutomationCancelledError as exc:
        assert exc.code == "AUTOMATION_CANCELLED"
    else:
        raise AssertionError("Era esperado erro de cancelamento.")


def test_clear_download_artifacts_removes_partial_and_finished_output(tmp_path) -> None:
    workflow = build_workflow()
    pdf_file = tmp_path / "arquivo.pdf"
    partial_file = tmp_path / "arquivo.pdf.crdownload"
    other_file = tmp_path / "arquivo.txt"
    pdf_file.write_bytes(b"%PDF-test")
    partial_file.write_bytes(b"partial")
    other_file.write_text("keep")

    workflow._clear_download_artifacts(tmp_path, ".pdf")

    assert not pdf_file.exists()
    assert not partial_file.exists()
    assert other_file.exists()


def test_collect_download_with_retry_retries_after_validation_error(tmp_path) -> None:
    workflow = build_workflow()
    workflow._wait_for_idle = lambda driver: None
    workflow._ensure_not_cancelled = lambda: None

    attempts = []
    target = tmp_path / "arquivo.pdf"

    def trigger():
        attempts.append("trigger")
        target.write_bytes(b"%PDF-test")

    def collector(download_dir: Path) -> Path:
        return download_dir / "arquivo.pdf"

    validation_attempts = []

    def validator(path: Path) -> None:
        validation_attempts.append(path)
        if len(validation_attempts) == 1:
            raise OutputValidationError("PDF_INVALID", "falhou")

    result = workflow._collect_download_with_retry(
        driver=object(),
        download_dir=tmp_path,
        suffix=".pdf",
        output_name="PDF",
        trigger=trigger,
        collector=collector,
        validator=validator,
    )

    assert result == target
    assert len(attempts) == 2
    assert len(validation_attempts) == 2
