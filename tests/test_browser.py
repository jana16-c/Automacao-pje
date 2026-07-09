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
