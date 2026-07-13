from pathlib import Path

from pje_automation.pje.browser import BrowserManager


def test_build_chrome_prefs_enables_automatic_downloads(tmp_path: Path) -> None:
    manager = BrowserManager()

    prefs = manager._build_chrome_prefs(tmp_path)

    assert prefs["download.default_directory"] == str(tmp_path)
    assert prefs["download.prompt_for_download"] is False
    assert prefs["download.directory_upgrade"] is True
    assert prefs["profile.default_content_setting_values.automatic_downloads"] == 1
    assert prefs["plugins.always_open_pdf_externally"] is True


def test_configure_chrome_download_behavior_tries_browser_and_page_commands(tmp_path: Path) -> None:
    manager = BrowserManager()
    calls: list[tuple[str, dict]] = []

    class DriverStub:
        def execute_cdp_cmd(self, command, params):
            calls.append((command, params))
            if command == "Browser.setDownloadBehavior":
                raise RuntimeError("unsupported")
            return {}

    manager._configure_chrome_download_behavior(DriverStub(), tmp_path)

    assert calls[0][0] == "Browser.setDownloadBehavior"
    assert calls[1][0] == "Page.setDownloadBehavior"
    assert calls[1][1]["downloadPath"] == str(tmp_path)


def test_apply_runtime_window_state_minimizes_when_enabled() -> None:
    manager = BrowserManager()
    called = []

    class DriverStub:
        def execute_cdp_cmd(self, command, params):
            raise RuntimeError("cdp indisponivel")

        def minimize_window(self):
            called.append(True)

    manager._apply_runtime_window_state(DriverStub())

    assert called == [True]


def test_apply_runtime_window_state_prefers_chrome_cdp_minimize() -> None:
    manager = BrowserManager()
    calls: list[tuple[str, dict]] = []

    class DriverStub:
        def execute_cdp_cmd(self, command, params):
            calls.append((command, params))
            if command == "Browser.getWindowForTarget":
                return {"windowId": 7}
            return {}

        def minimize_window(self):
            raise AssertionError("nao deveria usar fallback quando o CDP funciona")

    manager._apply_runtime_window_state(DriverStub())

    assert calls == [
        ("Browser.getWindowForTarget", {}),
        ("Browser.setWindowBounds", {"windowId": 7, "bounds": {"windowState": "minimized"}}),
    ]


def test_apply_startup_window_state_adds_start_minimized_for_chrome() -> None:
    manager = BrowserManager()

    class OptionsStub:
        def __init__(self):
            self.arguments = []

        def add_argument(self, argument):
            self.arguments.append(argument)

    options = OptionsStub()

    manager._apply_startup_window_state("chrome", options)

    assert "--start-minimized" in options.arguments
    assert "--window-size=1280,900" in options.arguments


def test_apply_startup_window_state_skips_when_minimization_disabled() -> None:
    manager = BrowserManager()
    manager.config["execution"]["minimize_browser_window"] = False

    class OptionsStub:
        def __init__(self):
            self.arguments = []

        def add_argument(self, argument):
            self.arguments.append(argument)

    options = OptionsStub()

    manager._apply_startup_window_state("chrome", options)

    assert options.arguments == []
