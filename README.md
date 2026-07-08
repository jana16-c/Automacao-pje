# Automação PJe

Automação local do PJe-Calc com Python e Selenium.

O fluxo atual do MVP:

- importa um modelo `.pjc`
- preenche `Nome` e `CPF`
- abre `Parâmetros do Cálculo`
- ajusta `Data de Demissão` e `Data Final`
- regera `Verbas`, `FGTS` e `Contribuição Social`
- preenche `Histórico Salarial`
- liquida
- gera `PDF`
- exporta `PJC`

O caso real validado foi o de `ATHOS HENRIQUE MENDES SILVA`, com geração correta de `PDF` e `PJC`.

## Estrutura

- `src/pje_automation/`: aplicação
- `resources/`: configuração e seletores
- `tests/`: testes automatizados
- `docs/`: plano e documentação de apoio
- `scripts/build_exe.ps1`: build do executável
- `AutomacaoPJE.spec`: empacotamento PyInstaller

## Requisitos

- Windows
- Google Chrome instalado
- PJe-Calc local disponível em `http://localhost:9257/pjecalc`

## Uso no código-fonte

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
pytest
python -m pje_automation --probe
python -m pje_automation
```

Observação:

- `python -m pje_automation` abre a interface gráfica.

## Entradas da interface

- `Modelo do PJe-Calc`: `.pjc` ou `.zip` com um único `.pjc`
- `Excel de cadastro`: planilha principal
- `Excel de histórico (opcional)`: planilha com competências e valores do histórico salarial
- `Pasta de saída`: diretório onde serão gravados os resultados

## Saídas

Dentro da pasta de saída a aplicação gera:

- `PDF/`
- `PJC/`
- `logs/execucao.log`
- `evidencias/`
- `controle/execucao.sqlite3`

## Build do EXE

```powershell
.\scripts\build_exe.ps1 -Clean
```

Saída esperada:

- `dist\AutomacaoPJE.exe`

O executável abre a mesma interface gráfica da versão em Python.

## Configuração

Os ajustes principais ficam em `resources/app_config.default.json`:

- `pje_calc.base_url`
- `pje_calc.element_timeout_seconds`
- `pje_calc.operation_timeout_seconds`
- `execution.max_retries_per_step`
- `execution.step_delay_ms`
- `execution.retry_backoff_seconds`
- `history_paste.delay_ms`

## Testes

```powershell
.venv\Scripts\python.exe -m pytest
```

## Observações práticas

- O PJe pode devolver `Erro Interno no Servidor`; a aplicação já tenta reiniciar o fluxo.
- O fluxo foi desacelerado para reduzir falhas por velocidade.
- O histórico salarial preenche `0,00` nas competências existentes no PJe e ausentes na planilha.
