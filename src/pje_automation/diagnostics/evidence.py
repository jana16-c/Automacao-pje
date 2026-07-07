from __future__ import annotations

from pathlib import Path

from selenium.webdriver.remote.webdriver import WebDriver


def save_evidence(driver: WebDriver, output_dir: Path, prefix: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    screenshot = output_dir / f"{prefix}.png"
    html = output_dir / f"{prefix}.html"
    driver.save_screenshot(str(screenshot))
    html.write_text(driver.page_source, encoding="utf-8")
    return screenshot, html
