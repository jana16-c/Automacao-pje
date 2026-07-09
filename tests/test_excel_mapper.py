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


def test_build_preview_without_limit_keeps_rows_after_the_default_sample() -> None:
    cadastro = Workbook()
    controle = cadastro.active
    controle.title = "Controle"
    controle.append(["Matricula", "Nome", "CPF", "Admissao", "Demissao"])
    for idx in range(1, 26):
        controle.append([f"{1000 + idx}", f"Pessoa {idx}", f"{idx:011d}", "01/01/2020", "02/01/2020"])

    historico = Workbook()
    aba = historico.active
    aba.title = "Pessoa 25"
    aba.append(["Matricula", "Funcionário", "Dt.Admissão", "Dt.Demissão", "Período", "Base"])
    aba.append(["1025", "Pessoa 25", "01/01/2020", "02/01/2020", "01/2020", "10,00"])

    preview = build_preview(cadastro, history_workbook=historico, limit=None)

    assert len(preview.valid_records) == 25
    assert preview.valid_records[-1].nome == "Pessoa 25"
    assert preview.valid_records[-1].historicos[0].valores[0].competencia == "01/2020"


def test_build_preview_normalizes_sparse_single_decimal_history_values() -> None:
    cadastro = Workbook()
    controle = cadastro.active
    controle.title = "Controle"
    controle.append(["Matricula", "Nome", "CPF", "Admissao", "Demissao"])
    controle.append(["1004664", "FILIPE", "279.892.794-36", "02/09/2004", "11/10/2019"])

    historico = Workbook()
    aba = historico.active
    aba.title = "FILIPE"
    aba.append(["Matricula", "Funcionário", "Dt.Admissão", "Dt.Demissão", "Período", "Base"])
    aba.append(["1004664", "FILIPE", "02/09/2004", "11/10/2019", "09/2014", 0.24])
    aba.append(["1004664", "FILIPE", "02/09/2004", "11/10/2019", "10/2014", 0.1])
    aba.append(["1004664", "FILIPE", "02/09/2004", "11/10/2019", "11/2014", 0.18])
    aba.append(["1004664", "FILIPE", "02/09/2004", "11/10/2019", "01/2015", 1.3])
    aba.append(["1004664", "FILIPE", "02/09/2004", "11/10/2019", "02/2015", 0.22])
    aba.append(["1004664", "FILIPE", "02/09/2004", "11/10/2019", "12/2017", 0.1])
    aba.append(["1004664", "FILIPE", "02/09/2004", "11/10/2019", "01/2018", 0.11])

    preview = build_preview(cadastro, history_workbook=historico, limit=None)

    valores = {item.competencia: str(item.valor) for serie in preview.valid_records[0].historicos for item in serie.valores}
    assert valores["10/2014"] == "0.01"
    assert valores["01/2015"] == "0.13"
    assert valores["12/2017"] == "0.01"


def test_build_preview_keeps_dense_single_decimal_history_values() -> None:
    cadastro = Workbook()
    controle = cadastro.active
    controle.title = "Controle"
    controle.append(["Matricula", "Nome", "CPF", "Admissao", "Demissao"])
    controle.append(["1001", "Maria", "12345678901", "01/01/2020", "02/01/2020"])

    historico = Workbook()
    aba = historico.active
    aba.title = "Maria"
    aba.append(["Matricula", "Funcionário", "Dt.Admissão", "Dt.Demissão", "Período", "Base"])
    aba.append(["1001", "Maria", "01/01/2020", "02/01/2020", "01/2020", 1.2])
    aba.append(["1001", "Maria", "01/01/2020", "02/01/2020", "02/2020", 2.3])
    aba.append(["1001", "Maria", "01/01/2020", "02/01/2020", "03/2020", 3.4])

    preview = build_preview(cadastro, history_workbook=historico, limit=None)

    valores = {item.competencia: str(item.valor) for serie in preview.valid_records[0].historicos for item in serie.valores}
    assert valores["01/2020"] == "1.20"
    assert valores["02/2020"] == "2.30"
    assert valores["03/2020"] == "3.40"
