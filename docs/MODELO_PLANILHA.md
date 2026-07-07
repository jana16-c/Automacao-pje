# Modelo de Planilha

Use a planilha em `.xlsx` ou `.xlsm`.

## Estrutura recomendada

Crie uma aba principal chamada `Dados` com uma linha por pessoa.

Cabeçalhos recomendados:

- `Nome`
- `CPF`
- `Data Admissao`
- `Data Demissao`
- `Processo`
- `Observacoes`

## Colunas obrigatorias no MVP atual

O sistema hoje exige estas 3 colunas para processar um registro:

- `Nome`
- `CPF`
- `Data Demissao`

Sem isso, a linha nao entra no fluxo.

## Formato esperado

- `Nome`: texto livre
- `CPF`: pode estar com ou sem mascara
- `Data Admissao`: opcional, preferencialmente `dd/mm/aaaa`
- `Data Demissao`: obrigatoria, preferencialmente `dd/mm/aaaa`
- `Processo`: opcional
- `Observacoes`: opcional, apenas controle humano

## Regras praticas

- Cada linha representa uma pessoa.
- A primeira linha deve conter os cabecalhos.
- Evite celulas mescladas.
- Evite linhas em branco no meio da tabela.
- Prefira uma unica aba de dados para o processamento.
- Se houver mais de uma aba, a automacao procura uma aba com cabecalhos compativeis.

## Exemplo

| Nome | CPF | Data Admissao | Data Demissao | Processo | Observacoes |
| --- | --- | --- | --- | --- | --- |
| Maria Helena Souza | 123.456.789-01 | 01/02/2015 | 31/12/2025 | 0012345-67.2020.5.03.0001 | Exemplo ficticio |

## Aliases aceitos pelo parser

Se quiser, o sistema tambem reconhece variacoes simples:

- `Nome`: `Reclamante`, `Empregado`, `Nome Reclamante`
- `CPF`: `CPF Reclamante`, `Documento`, `Documento Fiscal`
- `Data Admissao`: `Admissao`, `Data Admissao`, `Dt Admissao`
- `Data Demissao`: `Demissao`, `Data Demissao`, `Dt Demissao`, `Data Final`
- `Processo`: `Numero Processo`, `Numero do Processo`

Mesmo assim, mantenha os nomes recomendados para evitar ambiguidade.

## Aba opcional para fase futura

O arquivo modelo tambem pode ter uma aba `Historico_Salarial`.

Ela serve como rascunho para a proxima fase, mas o MVP atual ainda nao consome essa aba automaticamente.

Estrutura sugerida:

- `CPF`
- `Nome`
- `Rubrica`
- `Competencia`
- `Valor`

Exemplo:

| CPF | Nome | Rubrica | Competencia | Valor |
| --- | --- | --- | --- | --- |
| 12345678901 | Maria Helena Souza | Salario Base | 01/2025 | 3200,00 |
