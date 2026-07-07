from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pje_automation.domain.models import ProbeResult
from pje_automation.excel.normalization import normalize_header
from pje_automation.pje.browser import BrowserManager
from pje_automation.pje.selectors import SelectorRepository


ELEMENTS_SCRIPT = """
return Array.from(document.querySelectorAll('input, button, a, select, textarea')).map((element, index) => ({
  index,
  tag: element.tagName.toLowerCase(),
  id: element.id || null,
  name: element.getAttribute('name'),
  type: element.getAttribute('type'),
  text: (element.innerText || element.textContent || '').trim(),
  value: element.value || null,
  title: element.getAttribute('title'),
  href: element.getAttribute('href'),
  classes: element.className || null,
  visible: !!(element.offsetWidth || element.offsetHeight || element.getClientRects().length),
}));
"""


class DomProbe:
    def __init__(self, browser_manager: BrowserManager, selectors: SelectorRepository) -> None:
        self.browser_manager = browser_manager
        self.selectors = selectors

    def run(self, output_dir: Path) -> ProbeResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        with TemporaryDirectory(prefix="pje_probe_download_") as temp_download_dir:
            driver = self.browser_manager.open_driver(download_dir=Path(temp_download_dir))
            try:
                self.browser_manager.open_base_page(driver)
                screenshot_file = output_dir / "principal.png"
                html_file = output_dir / "principal.html"
                elements_file = output_dir / "principal.elements.json"
                selectors_file = output_dir / "selectors.local.json"

                principal_elements = self._capture_stage(driver, screenshot_file, html_file, elements_file)
                import_elements = self._capture_import_stage(driver, output_dir)

                local_selectors = {
                    "version": "0.1.0",
                    "base_url": self.browser_manager.base_url,
                    "generated_from_probe": driver.current_url,
                    "selectors": infer_selectors(principal_elements, import_elements),
                }
                self.selectors.save_local(local_selectors)
                selectors_file.write_text(json.dumps(local_selectors, indent=2, ensure_ascii=False), encoding="utf-8")

                return ProbeResult(
                    output_dir=output_dir,
                    screenshot_file=screenshot_file,
                    html_file=html_file,
                    elements_file=elements_file,
                    selectors_file=selectors_file,
                    url=driver.current_url,
                    generated_at=datetime.now(),
                )
            finally:
                driver.quit()

    def _capture_stage(self, driver, screenshot_file: Path, html_file: Path, elements_file: Path) -> list[dict]:
        driver.save_screenshot(str(screenshot_file))
        html_file.write_text(driver.page_source, encoding="utf-8")
        elements = driver.execute_script(ELEMENTS_SCRIPT)
        elements_file.write_text(json.dumps(elements, indent=2, ensure_ascii=False), encoding="utf-8")
        return elements

    def _capture_import_stage(self, driver, output_dir: Path) -> list[dict]:
        import_links = [
            element
            for element in driver.find_elements(By.TAG_NAME, "a")
            if (element.get_attribute("title") or "").startswith("Importar")
        ]
        if not import_links:
            return []

        driver.execute_script("arguments[0].click();", import_links[0])
        WebDriverWait(driver, 10).until(lambda active: "importacao" in active.current_url.lower())
        return self._capture_stage(
            driver,
            output_dir / "importacao.png",
            output_dir / "importacao.html",
            output_dir / "importacao.elements.json",
        )


def infer_selectors(principal_elements: list[dict], import_elements: list[dict]) -> dict[str, list[dict[str, str]]]:
    selectors: dict[str, list[dict[str, str]]] = {}
    for element in principal_elements:
        text = (element.get("text") or "").strip()
        title = (element.get("title") or "").strip()
        element_id = element.get("id")
        normalized_text = normalize_header(text)
        normalized_title = normalize_header(title)
        if element_id:
            selectors.setdefault(f"probe.id.{element_id}", []).append({"by": "id", "value": element_id})
        if normalized_title == "importar calculo":
            selector_values = [{"by": "xpath", "value": "//*[@title='Importar Cálculo']"}]
            if element_id:
                selector_values.insert(0, {"by": "id", "value": element_id})
            selectors["home.importar_calculo"] = selector_values
        if normalized_text == "importar" and element_id:
            selectors["home.importar_calculo"] = [{"by": "id", "value": element_id}]
        if normalized_text in {"verbas", "contribuicao social", "tela inicial", "buscar", "importar"} and element_id:
            selectors[f"probe.menu.{normalized_text.replace(' ', '_')}"] = [{"by": "id", "value": element_id}]

    for element in import_elements:
        element_id = element.get("id")
        element_type = normalize_header(element.get("type") or "")
        if element_type == "file" and element_id:
            selectors["import.file_input"] = [{"by": "id", "value": element_id}]
            selectors[f"probe.id.{element_id}"] = [{"by": "id", "value": element_id}]
        if element_type == "submit" and element_id:
            selectors["import.confirmar"] = [{"by": "id", "value": element_id}]
            selectors[f"probe.id.{element_id}"] = [{"by": "id", "value": element_id}]
    return selectors
