# PJe Calc Automation

Projeto Python para automatizar o PJe-Calc local com foco em execucao offline, validacao de entradas, inspeção de DOM e MVP de um registro.

## Desenvolvimento

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
pytest
python -m pje_automation --probe
python -m pje_automation --gui
```

## Entradas

- modelo `.pjc` ou `.zip` contendo exatamente um `.pjc`
- planilha `.xlsx` ou `.xlsm`
- pasta de saida

## Saidas

- `output/PDF`
- `output/PJC`
- `output/logs`
- `output/evidencias`
- `output/controle`

## Fluxo MVP atual

- importa um modelo `.pjc` no PJe-Calc local
- preenche nome, CPF e data final do calculo
- navega por verbas, FGTS, contribuicao social e historico salarial
- liquida, imprime PDF e exporta o pacote `.pjc`
