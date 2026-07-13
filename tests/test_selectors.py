import json
from pathlib import Path


def test_default_selectors_include_stable_fallbacks_for_internal_calc_menus() -> None:
    selectors_path = Path("resources/selectors.default.json")
    data = json.loads(selectors_path.read_text(encoding="utf-8"))
    selectors = data["selectors"]

    assert selectors["menu.historico_salarial"][-1] == {
        "by": "xpath",
        "value": "//li[@id='li_calculo_historico_salarial']//a[contains(normalize-space(.), 'Histórico Salarial')]",
    }
    assert selectors["menu.verbas"][-1] == {
        "by": "xpath",
        "value": "//li[@id='li_calculo_verbas']//a[contains(normalize-space(.), 'Verbas')]",
    }
    assert selectors["menu.fgts"][-1] == {
        "by": "xpath",
        "value": "//li[@id='li_calculo_fgts']//a[contains(normalize-space(.), 'FGTS')]",
    }
    assert selectors["menu.contribuicao_social"][-1] == {
        "by": "xpath",
        "value": "//li[@id='li_calculo_inss']//a[contains(normalize-space(.), 'Contribuição Social')]",
    }
