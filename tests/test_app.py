from pje_automation.app import Application
from pje_automation.domain.errors import WorkflowExecutionError


def build_application() -> Application:
    app = Application.__new__(Application)
    app.browser_manager = type("BrowserManagerStub", (), {"config": {"execution": {"retry_backoff_seconds": 4}}})()
    return app


def test_should_retry_workflow_accepts_field_persistence_errors() -> None:
    app = build_application()

    should_retry = app._should_retry_workflow(
        WorkflowExecutionError("FIELD_NOT_PERSISTED", "falhou"),
        attempt=1,
        max_attempts=2,
    )

    assert should_retry is True


def test_retry_backoff_seconds_reads_execution_config() -> None:
    app = build_application()

    assert app._retry_backoff_seconds() == 4
