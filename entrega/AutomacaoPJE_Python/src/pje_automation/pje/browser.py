from __future__ import annotations

import json
from pathlib import Path
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

    def open_driver(self, download_dir: Path | None = None) -> WebDriver:
        browser_name = self.config["browser"].get("name", "firefox").lower()
        if browser_name == "chrome":
            driver = self._open_chrome(download_dir=download_dir)
        else:
            driver = self._open_firefox(download_dir=download_dir)
        if download_dir is not None:
            setattr(driver, "_pje_download_dir", str(download_dir))
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
        return webdriver.Firefox(options=options, service=service)

    def _open_chrome(self, download_dir: Path | None) -> WebDriver:
        options = ChromeOptions()
        if self.config["browser"].get("headless"):
            options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")

        binary = self.config["browser"].get("chrome_binary")
        if binary:
            options.binary_location = binary

        if download_dir:
            prefs = {
                "download.default_directory": str(download_dir),
                "download.prompt_for_download": False,
                "plugins.always_open_pdf_externally": True,
            }
            options.add_experimental_option("prefs", prefs)

        return webdriver.Chrome(service=ChromeService(), options=options)

    def open_base_page(self, driver: WebDriver) -> None:
        driver.get(self.base_url)
        if "logon.jsf" in driver.current_url:
            driver.get(f"{self.base_url.rstrip('/')}/logon.jsf")

    def find_visible_text(self, driver: WebDriver, text: str) -> bool:
        return bool(driver.find_elements(By.XPATH, f"//*[contains(normalize-space(.), {json.dumps(text)})]"))


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
