# Plano de Teste Completo do MVP

Este plano foi montado a partir da análise do vídeo `Gravação de ecrã 2 (online-video-cutter.com).mp4`.

Objetivo: definir um teste único, completo e confiável que, ao passar, deixe o MVP praticamente pronto para uso real.

## 1. Fluxo observado no vídeo

Sequência inferida pelos frames extraídos:

1. `00s a 15s`
   - Abre o PJe-Calc.
   - Escolhe `Importar Cálculo`.
   - Seleciona um arquivo `.pjc`.

2. `25s a 38s`
   - Modelo já importado.
   - Tela `Dados do Cálculo`.
   - Consulta a planilha ao lado.
   - Preenche `Nome` e `CPF`.

3. `50s a 63s`
   - Aba `Parâmetros do Cálculo`.
   - Ajusta `Demissão` e `Data Final`.
   - Salva.
   - PJe mostra processamento e mensagem de sucesso.

4. `75s`
   - Fluxo passa por uma tela de ocorrências com botão `Regerar`.
   - Isso indica que a mudança de período dispara regeneração antes da liquidação.

5. `88s a 92s`
   - Em `Contribuição Social > Ocorrências > Regerar`.
   - Surge confirmação com opção de manter ou sobrescrever alterações.
   - Depois há sucesso e retorno.

6. `98s a 138s`
   - Entra em `Histórico Salarial`.
   - Usa um item já existente no modelo.
   - Copia valores mensais da planilha.
   - Cola esses valores na grade mensal do PJe.
   - Salva e recebe mensagem de sucesso.

7. `145s a 148s`
   - Entra em `Operações > Liquidar`.
   - Clica `Liquidar`.
   - Recebe sucesso.

8. `151s a 164s`
   - Entra em `Operações > Imprimir`.
   - Mantém `PDF`.
   - Imprime o relatório.
   - Salva o arquivo `.pdf`.

9. `176s`
   - Exporta o cálculo em `.pjc`.
   - Salva o arquivo final.

## 2. O que o vídeo prova sobre o fluxo correto

Para o MVP ficar aderente ao vídeo, a ordem correta do teste deve ser:

1. Importar modelo
2. Preencher identificação
3. Alterar data de demissão e data final
4. Salvar
5. Regerar `Verbas`
6. Regerar `FGTS`
7. Regerar `Contribuição Social`
8. Preencher `Histórico Salarial`
9. Liquidar
10. Imprimir PDF
11. Exportar PJC

Ponto importante:

- O histórico salarial vem depois das regenerações e antes da liquidação.
- O teste só deve ser considerado fiel ao vídeo se essa ordem for respeitada.

## 3. Diferença entre o vídeo e o estado atual do projeto

Hoje o projeto já consegue:

- importar o `.pjc`
- preencher `Nome`, `CPF` e `Data Final`
- salvar
- navegar entre módulos
- liquidar
- gerar `PDF`
- exportar `PJC`

Mas ainda faltam estes comportamentos para o teste ficar fiel ao vídeo:

- `Verbas` precisa usar regeneração real, não só navegação
- `FGTS` precisa entrar em `Ocorrências` e usar `Regerar`
- `Contribuição Social` precisa entrar em `Ocorrências` e usar `Regerar` com confirmação
- `Histórico Salarial` precisa ler a planilha e preencher a grade mensal do item correto

## 4. Estrutura da planilha para o teste completo

Para esse teste, a planilha precisa ter duas abas operacionais.

### Aba `Dados`

Uma linha por pessoa.

Colunas:

- `Nome`
- `CPF`
- `Data Admissao`
- `Data Demissao`
- `Processo`
- `Historico Nome`

Uso:

- `Nome`, `CPF` e `Data Demissao` abastecem `Dados do Cálculo`
- `Historico Nome` identifica qual item do `Histórico Salarial` deve ser aberto

### Aba `Historico_Salarial`

Uma linha por competência.

Colunas:

- `CPF`
- `Historico Nome`
- `Competencia`
- `Valor`

Exemplo:

| CPF | Historico Nome | Competencia | Valor |
| --- | --- | --- | --- |
| 23344198696 | DIFERENÇA DE ADI NOT + REFLE (CÁLCULO HOMOLOGADO) | 07/2012 | 64,79 |
| 23344198696 | DIFERENÇA DE ADI NOT + REFLE (CÁLCULO HOMOLOGADO) | 08/2012 | 78,32 |

## 5. Caso de teste único recomendado

O melhor teste completo é com um único empregado e um intervalo histórico suficiente para validar colagem em lote.

### Dados do registro

- 1 empregado
- CPF válido
- Data de demissão diferente da data original do modelo
- Entre 24 e 100 competências no histórico
- Nome do histórico idêntico ao item existente no modelo

### Pré-condições

- `PJe-Calc` local disponível em `http://localhost:9257/pjecalc`
- modelo `.pjc` já validado no ambiente
- planilha preenchida com um único caso de teste limpo
- diretório de saída vazio
- automação configurada para Chrome

## 6. Roteiro detalhado do teste

### Fase A. Importação

1. Abrir o PJe-Calc.
2. Clicar em `Importar Cálculo`.
3. Enviar o arquivo `.pjc`.
4. Confirmar importação, se o botão aparecer.

Critério de sucesso:

- URL muda para a tela do cálculo.
- Campos de identificação ficam acessíveis.

### Fase B. Identificação e período

1. Preencher `Nome`.
2. Preencher `CPF`.
3. Ir para `Parâmetros do Cálculo`.
4. Alterar `Data Demissão`.
5. Alterar `Data Final`, se necessário.
6. Salvar.

Critério de sucesso:

- mensagem de sucesso
- processamento concluído
- valor persistido no campo após recarga

### Fase C. Regeneração de Verbas

1. Abrir `Verbas`.
2. Executar a regeneração real da tela, se houver botão ou grade de ocorrências.
3. Confirmar qualquer diálogo de regeneração.

Critério de sucesso:

- sucesso visual
- retorno estável para a tela de `Verbas`

### Fase D. Regeneração de FGTS

1. Abrir `FGTS`.
2. Entrar em `Ocorrências`.
3. Clicar em `Regerar`.
4. Confirmar a regeneração.
5. Aguardar sucesso.

Critério de sucesso:

- tela de ocorrências atualizada
- sucesso visual

### Fase E. Regeneração de Contribuição Social

1. Abrir `Contribuição Social`.
2. Entrar em `Ocorrências`.
3. Clicar em `Regerar`.
4. No diálogo, confirmar a opção correta.

Regra do teste:

- se o objetivo for preservar ajustes já existentes no modelo, escolher `Manter alterações realizadas nas ocorrências`
- se o objetivo for recalcular tudo do zero, escolher `Sobrescrever alterações realizadas nas ocorrências`

Critério de sucesso:

- mensagem de sucesso
- retorno sem erro para a tela de ocorrências

### Fase F. Preenchimento do Histórico Salarial

1. Abrir `Histórico Salarial`.
2. Localizar o item cujo nome bate com `Historico Nome` da planilha.
3. Abrir o item para edição.
4. Mapear as linhas da grade pelo campo `Mês/Ano`.
5. Para cada competência da planilha:
   - localizar a linha correspondente
   - preencher o campo `Valor`
6. Salvar.

Critério de sucesso:

- todos os meses previstos receberam valor
- nenhum mês fora da planilha foi alterado
- mensagem de sucesso ao salvar

Observação:

- Para automação robusta, o preenchimento deve ser por mapeamento `Competencia -> input da linha`, não por posição visual fixa.

### Fase G. Liquidação

1. Abrir `Operações > Liquidar`.
2. Validar se não há pendências impeditivas.
3. Clicar `Liquidar`.

Critério de sucesso:

- mensagem de sucesso
- nenhuma pendência crítica em tela

### Fase H. Impressão

1. Abrir `Operações > Imprimir`.
2. Garantir que o formato é `PDF`.
3. Confirmar as seções exigidas do relatório.
4. Executar `Imprimir`.

Critério de sucesso:

- arquivo PDF salvo no diretório de saída
- arquivo maior que 1 KB
- assinatura `%PDF-`

### Fase I. Exportação

1. Abrir `Operações > Exportar`.
2. Executar a exportação.

Critério de sucesso:

- arquivo `.pjc` salvo no diretório de saída
- pacote interno válido
- contém um `.pjc` interno

## 7. Evidências obrigatórias do teste

Ao rodar esse teste no futuro, a automação deve guardar evidências por etapa:

- screenshot após importação
- screenshot após salvar datas
- screenshot após cada regeneração
- screenshot após salvar histórico
- screenshot após liquidação
- nomes finais dos arquivos gerados
- log da execução
- estado final no banco de controle

## 8. Critérios de aprovação do MVP

O MVP pode ser considerado quase pronto para uso quando este teste passar com todos os itens abaixo:

- sem intervenção manual durante o fluxo
- ordem igual à do vídeo
- alteração de data persistida
- `Verbas`, `FGTS` e `Contribuição Social` realmente regenerados
- histórico salarial preenchido a partir da planilha
- liquidação concluída sem pendência impeditiva
- PDF gerado corretamente
- PJC gerado corretamente
- job final marcado como `CONCLUIDO`

## 9. O que precisa ser implementado antes de executar esse teste

Lista objetiva:

1. Descobrir e mapear o caminho real de regeneração em `Verbas`.
2. Implementar `FGTS > Ocorrências > Regerar`.
3. Implementar `Contribuição Social > Ocorrências > Regerar > Confirmar`.
4. Evoluir o parser da planilha para ler a aba `Historico_Salarial`.
5. Implementar a escolha do item correto em `Histórico Salarial` por nome.
6. Implementar o preenchimento da grade por competência.
7. Salvar o histórico e validar sucesso antes de liquidar.

## 10. Resultado esperado após aprovação desse teste

Se esse teste passar, faltará pouco para uso real:

- ampliar de 1 registro para lote
- tratar variações de modelos com histórico diferente
- endurecer logs e mensagens de erro
- refinar estratégia de retomada em caso de falha por registro

Em resumo:

- passando esse teste, o MVP deixa de ser apenas um fluxo técnico de prova
- e passa a reproduzir o procedimento operacional principal mostrado no vídeo
