from __future__ import annotations

import json
from pathlib import Path
from time import monotonic, sleep
from typing import Any

import requests
from selenium import webdriver
from selenium.webdriver import ChromeOptions, FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.remote.webdriver import WebDriver

from pje_automation.domain.errors import PjeUnavailableError
from pje_automation.utils.resources import resource_path


DEFAULT_CONFIG = resource_path("resources/app_config.default.json")


class BrowserManager:
    def __init__(self, base_url_override: str | None = None) -> None:
        self.config = load_config(DEFAULT_CONFIG)
        if base_url_override:
            self.config["pje_calc"]["base_url"] = base_url_override

    @property
    def base_url(self) -> str:
        return self.config["pje_calc"]["base_url"]

    def ensure_pje_available(self) -> None:
        try:
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            raise PjeUnavailableError(
                "PJE_UNAVAILABLE",
                "O PJe-Calc local nao respondeu em localhost.",
                details=str(exc),
            ) from exc

    def wait_until_pje_available(self, timeout_seconds: int | None = None) -> None:
        timeout = int(timeout_seconds or self.config["pje_calc"].get("startup_timeout_seconds", 120))
        deadline = monotonic() + max(timeout, 1)
        last_error: Exception | None = None
        while monotonic() < deadline:
            try:
                self.ensure_pje_available()
                return
            except PjeUnavailableError as exc:
                last_error = exc
                sleep(2)
        if last_error is not None:
            raise last_error
        self.ensure_pje_available()

    def open_driver(self, download_dir: Path | None = None) -> WebDriver:
        browser_name = self.config["browser"].get("name", "firefox").lower()
        if browser_name == "chrome":
            driver = self._open_chrome(download_dir=download_dir)
        else:
            driver = self._open_firefox(download_dir=download_dir)
        if download_dir is not None:
            setattr(driver, "_pje_download_dir", str(download_dir))
        self._apply_runtime_window_state(driver)
        return driver

    def _open_firefox(self, download_dir: Path | None) -> WebDriver:
        options = FirefoxOptions()
        if self.config["browser"].get("headless"):
            options.add_argument("-headless")

        binary = self.config["browser"].get("firefox_binary")
        if binary:
            options.binary_location = binary

        if download_dir:
            options.set_preference("browser.download.folderList", 2)
            options.set_preference("browser.download.dir", str(download_dir))
            options.set_preference("browser.download.useDownloadDir", True)
            options.set_preference(
                "browser.helperApps.neverAsk.saveToDisk",
                "application/pdf,application/zip,application/octet-stream,application/x-zip-compressed",
            )
            options.set_preference("pdfjs.disabled", True)

        driver_path = self.config["browser"].get("geckodriver_path")
        service = FirefoxService(executable_path=driver_path) if driver_path else FirefoxService()
        driver = webdriver.Firefox(options=options, service=service)
        driver.set_page_load_timeout(int(self.config["pje_calc"].get("operation_timeout_seconds", 180)))
        driver.set_script_timeout(int(self.config["pje_calc"].get("operation_timeout_seconds", 180)))
        driver.implicitly_wait(0)
        return driver

    def _open_chrome(self, download_dir: Path | None) -> WebDriver:
        options = ChromeOptions()
        options.page_load_strategy = "eager"
        if self.config["browser"].get("headless"):
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-popup-blocking")

        binary = self.config["browser"].get("chrome_binary")
        if binary:
            options.binary_location = binary

        prefs = self._build_chrome_prefs(download_dir)
        if prefs:
            options.add_experimental_option("prefs", prefs)

        driver = webdriver.Chrome(service=ChromeService(), options=options)
        self._configure_chrome_download_behavior(driver, download_dir)
        driver.set_page_load_timeout(int(self.config["pje_calc"].get("operation_timeout_seconds", 180)))
        driver.set_script_timeout(int(self.config["pje_calc"].get("operation_timeout_seconds", 180)))
        driver.implicitly_wait(0)
        return driver

    def _build_chrome_prefs(self, download_dir: Path | None) -> dict[str, Any]:
        if not download_dir:
            return {}
        return {
            "download.default_directory": str(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "profile.default_content_settings.popups": 0,
            "plugins.always_open_pdf_externally": True,
            "safebrowsing.enabled": True,
        }

    def _configure_chrome_download_behavior(self, driver: WebDriver, download_dir: Path | None) -> None:
        if not download_dir or not hasattr(driver, "execute_cdp_cmd"):
            return
        params = {
            "behavior": "allow",
            "downloadPath": str(download_dir),
            "eventsEnabled": False,
        }
        for command in ("Browser.setDownloadBehavior", "Page.setDownloadBehavior"):
            try:
                driver.execute_cdp_cmd(command, params)
            except Exception:
                continue

    def open_base_page(self, driver: WebDriver) -> None:
        driver.get(self.base_url)
        if "logon.jsf" in driver.current_url:
            driver.get(f"{self.base_url.rstrip('/')}/logon.jsf")

    def find_visible_text(self, driver: WebDriver, text: str) -> bool:
        return bool(driver.find_elements(By.XPATH, f"//*[contains(normalize-space(.), {json.dumps(text)})]"))

    def _apply_runtime_window_state(self, driver: WebDriver) -> None:
        if not self.config.get("execution", {}).get("minimize_browser_window", True):
            return
        try:
            driver.minimize_window()
        except Exception:
            return


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
