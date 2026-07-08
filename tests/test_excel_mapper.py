from openpyxl import Workbook

from pje_automation.excel.mapper import build_preview


def test_build_preview_attaches_history_rows_by_cpf() -> None:
    workbook = Workbook()
    dados = workbook.active
    dados.title = "Dados"
    dados.append(["Nome", "CPF", "Data Demissao"])
    dados.append(["Maria Souza", "12345678901", "30/06/2026"])

    historico = workbook.create_sheet("Historico_Salarial")
    historico.append(["CPF", "Historico Nome", "Competencia", "Valor"])
    historico.append(["12345678901", "DIFERENCA", "07/2012", "10,50"])
    historico.append(["12345678901", "DIFERENCA", "08/2012", "11,75"])

    preview = build_preview(workbook)

    assert len(preview.valid_records) == 1
    record = preview.valid_records[0]
    assert len(record.historicos) == 1
    assert record.historicos[0].nome == "DIFERENCA"
    assert [item.competencia for item in record.historicos[0].valores] == ["07/2012", "08/2012"]


def test_build_preview_filters_history_by_requested_name() -> None:
    workbook = Workbook()
    dados = workbook.active
    dados.title = "Dados"
    dados.append(["Nome", "CPF", "Data Demissao", "Historico Nome"])
    dados.append(["Maria Souza", "12345678901", "30/06/2026", "BASE INFORMADA"])

    historico = workbook.create_sheet("Historico_Salarial")
    historico.append(["CPF", "Historico Nome", "Competencia", "Valor"])
    historico.append(["12345678901", "BASE INFORMADA", "07/2012", "10,50"])
    historico.append(["12345678901", "OUTRA SERIE", "07/2012", "99,99"])

    preview = build_preview(workbook)

    record = preview.valid_records[0]
    assert [serie.nome for serie in record.historicos] == ["BASE INFORMADA"]


def test_build_preview_returns_placeholder_when_requested_history_is_missing() -> None:
    workbook = Workbook()
    dados = workbook.active
    dados.title = "Dados"
    dados.append(["Nome", "CPF", "Data Demissao", "Historico Nome"])
    dados.append(["Maria Souza", "12345678901", "30/06/2026", "BASE INFORMADA"])

    preview = build_preview(workbook)

    record = preview.valid_records[0]
    assert len(record.historicos) == 1
    assert record.historicos[0].nome == "BASE INFORMADA"
    assert record.historicos[0].valores == []


def test_build_preview_supports_companion_history_workbook_and_name_fallback() -> None:
    cadastro = Workbook()
    controle = cadastro.active
    controle.title = "Controle"
    controle.append(["Matricula", "Nome", "CPF", "Admissao", "Demissao"])
    controle.append(["1006133", "ATHOS HENRIQUE MENDES SILVA", "081.367.163-90", "06/08/2015", "24/03/2016"])

    historico = Workbook()
    aba = historico.active
    aba.title = "ATHOS HENRIQUE MENDES SILVA"
    aba.append(["Matricula", "Funcionário", "Dt.Admissão", "Dt.Demissão", "Período", "dif ad.not+ \nReflexos"])
    aba.append(["1007592", "ATHOS HENRIQUE MENDES SILVA", "06/08/2015", "24/03/16", "06/2015", "18,54"])
    aba.append(["1007592", "ATHOS HENRIQUE MENDES SILVA", "06/08/2015", "24/03/16", "07/2015", "37,18"])
    aba.append(["1007592", "ATHOS HENRIQUE MENDES SILVA", "06/08/2015", "24/03/16", "08/2015", "-"])

    preview = build_preview(cadastro, history_workbook=historico)

    assert len(preview.valid_records) == 1
    record = preview.valid_records[0]
    assert record.nome == "ATHOS HENRIQUE MENDES SILVA"
    assert record.cpf == "08136716390"
    assert len(record.historicos) == 1
    assert record.historicos[0].nome == "dif ad.not+ Reflexos"
    assert [item.competencia for item in record.historicos[0].valores] == ["06/2015", "07/2015"]
