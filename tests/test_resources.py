import sys
from pathlib import Path

from pje_automation.utils.resources import resource_path


def test_resource_path_prefers_external_resource_next_to_exe_when_frozen(monkeypatch, tmp_path: Path) -> None:
    resources_dir = tmp_path / "resources"
    resources_dir.mkdir()
    external_file = resources_dir / "app_config.default.json"
    external_file.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "AutomacaoPJE.exe"), raising=False)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    resolved = resource_path("resources/app_config.default.json")

    assert resolved == external_file


def test_resource_path_falls_back_to_repo_resource_when_external_file_does_not_exist(monkeypatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(Path.cwd() / "dist" / "AutomacaoPJE.exe"), raising=False)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    resolved = resource_path("resources/selectors.default.json")

    assert resolved.name == "selectors.default.json"
    assert resolved.exists()
