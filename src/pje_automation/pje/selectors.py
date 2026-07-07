from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from selenium.webdriver.common.by import By

from pje_automation.domain.errors import SelectorNotFoundError
from pje_automation.utils.resources import resource_path


SELECTOR_MAP = {
    "css": By.CSS_SELECTOR,
    "xpath": By.XPATH,
    "id": By.ID,
    "name": By.NAME,
    "link_text": By.LINK_TEXT,
    "partial_link_text": By.PARTIAL_LINK_TEXT,
    "tag_name": By.TAG_NAME,
}


class SelectorRepository:
    def __init__(self, default_file: Path | None = None, local_file: Path | None = None) -> None:
        self.default_file = default_file or resource_path("resources/selectors.default.json")
        self.local_file = local_file or resource_path("resources/selectors.local.json")
        self._selectors = self._load()

    def get(self, key: str) -> list[tuple[str, str]]:
        values = self._selectors.get("selectors", {}).get(key, [])
        if not values:
            raise SelectorNotFoundError("SELECTOR_NOT_FOUND", f"Seletor nao configurado para {key}")
        pairs: list[tuple[str, str]] = []
        for item in values:
            by = item["by"]
            pairs.append((SELECTOR_MAP[by], item["value"]))
        return pairs

    def save_local(self, data: dict[str, Any]) -> Path:
        self.local_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        self._selectors = self._load()
        return self.local_file

    def _load(self) -> dict[str, Any]:
        base = json.loads(self.default_file.read_text(encoding="utf-8"))
        if self.local_file.exists():
            local = json.loads(self.local_file.read_text(encoding="utf-8"))
            base["selectors"].update(local.get("selectors", {}))
        return base
