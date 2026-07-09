from __future__ import annotations


class AutomationError(Exception):
    def __init__(self, code: str, user_message: str, details: str | None = None) -> None:
        super().__init__(user_message)
        self.code = code
        self.user_message = user_message
        self.details = details


class InputValidationError(AutomationError):
    pass


class OutputValidationError(AutomationError):
    pass


class PjeUnavailableError(AutomationError):
    pass


class SelectorNotFoundError(AutomationError):
    pass


class WorkflowExecutionError(AutomationError):
    pass


class AutomationCancelledError(AutomationError):
    pass
