from __future__ import annotations

from pathlib import Path
from time import monotonic, sleep

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

WAIT_POLL_FREQUENCY = 0.1


def wait_for_element(driver: WebDriver, locator: tuple[str, str], timeout: int = 30) -> WebElement:
    return WebDriverWait(driver, timeout, poll_frequency=WAIT_POLL_FREQUENCY).until(EC.visibility_of_element_located(locator))


def wait_for_present_element(driver: WebDriver, locator: tuple[str, str], timeout: int = 30) -> WebElement:
    return WebDriverWait(driver, timeout, poll_frequency=WAIT_POLL_FREQUENCY).until(EC.presence_of_element_located(locator))


def wait_for_condition(driver: WebDriver, predicate, timeout: int = 30):
    return WebDriverWait(driver, timeout, poll_frequency=WAIT_POLL_FREQUENCY).until(predicate)


def wait_for_page_ready(driver: WebDriver, timeout: int = 30) -> None:
    def _ready(current_driver: WebDriver) -> bool:
        try:
            return bool(
                current_driver.execute_script(
                    """
                    const readyState = document.readyState;
                    const ready = readyState === 'complete' || readyState === 'interactive';
                    const jqueryIdle = !window.jQuery || window.jQuery.active === 0;
                    return ready && jqueryIdle;
                    """
                )
            )
        except Exception:
            return False

    wait_for_condition(driver, _ready, timeout=timeout)


def wait_for_download(directory: Path, suffix: str, timeout: int = 180) -> Path:
    end = monotonic() + timeout
    while monotonic() < end:
        for item in directory.iterdir():
            if item.suffix.lower() == suffix.lower() and item.stat().st_size > 0:
                return wait_for_file_stable(item)
        sleep(1)
    raise TimeoutError(f"Download {suffix} nao apareceu em {directory}")


def wait_for_file_stable(path: Path, stable_seconds: int = 2, timeout: int = 30) -> Path:
    end = monotonic() + timeout
    previous_size = -1
    stable_since = None
    while monotonic() < end:
        size = path.stat().st_size
        if size == previous_size:
            stable_since = stable_since or monotonic()
            if monotonic() - stable_since >= stable_seconds:
                return path
        else:
            stable_since = None
            previous_size = size
        sleep(0.5)
    raise TimeoutError(f"Arquivo nao estabilizou: {path}")
