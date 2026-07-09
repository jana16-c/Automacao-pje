from __future__ import annotations

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


PASTE_SCRIPT = """
const values = arguments[0];
const startElement = arguments[1];
const delayMs = arguments[2];
const done = arguments[arguments.length - 1];

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

(async () => {
  let current = startElement;
  const written = [];

  for (const value of values) {
    current.focus();
    current.value = value;
    current.dispatchEvent(new Event('input', { bubbles: true }));
    current.dispatchEvent(new Event('change', { bubbles: true }));
    current.dispatchEvent(new Event('blur', { bubbles: true }));
    written.push({ id: current.id, value: current.value });
    current.dispatchEvent(new KeyboardEvent('keydown', {
      key: 'ArrowDown', code: 'ArrowDown', keyCode: 40, which: 40, bubbles: true
    }));
    await sleep(delayMs);
    current = document.activeElement;
  }

  done({ ok: true, count: written.length, written });
})().catch(error => done({ ok: false, error: String(error) }));
"""


def paste_history_values(driver: WebDriver, start_element: WebElement, values: list[str], delay_ms: int = 25) -> dict:
    return driver.execute_async_script(PASTE_SCRIPT, values, start_element, delay_ms)
