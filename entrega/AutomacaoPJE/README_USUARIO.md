# Automação PJe

## Arquivos desta pasta

- `AutomacaoPJE.exe`: aplicativo principal
- `resources/app_config.default.json`: configuração do navegador, URL do PJe e tempos
- `resources/selectors.local.json`: seletores locais mapeados no seu ambiente

## Como usar

1. Abra o `PJe-Calc` local.
2. Execute `AutomacaoPJE.exe`.
3. Preencha:
   - modelo `.pjc`
   - Excel de cadastro
   - Excel de histórico, se houver
   - pasta de saída
4. Clique em `Validar`.
5. Clique em `Executar MVP`.

## Saídas geradas

Na pasta de saída o programa cria:

- `PDF`
- `PJC`
- `logs`
- `evidencias`
- `controle`

## Ajustes mais comuns

Edite `resources/app_config.default.json` se precisar mudar:

- `pje_calc.base_url`
- `browser.name`
- `browser.chrome_binary`
- `pje_calc.element_timeout_seconds`
- `pje_calc.operation_timeout_seconds`
- `execution.step_delay_ms`
- `execution.retry_backoff_seconds`

## Observações

- O fluxo foi validado no seu ambiente com o caso `ATHOS HENRIQUE MENDES SILVA`.
- Se o PJe devolver `Erro Interno no Servidor`, a automação tenta reiniciar o fluxo.
- Se o ambiente do PJe mudar, ajuste `resources/selectors.local.json`.
