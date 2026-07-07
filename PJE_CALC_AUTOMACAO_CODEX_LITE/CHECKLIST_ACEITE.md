# Checklist de aceite

## Interface e entrada
- [ ] O EXE abre sem exigir instalação do Python.
- [ ] Solicita modelo, Excel e pasta de saída.
- [ ] Aceita `.pjc`; aceita `.zip` somente quando contém exatamente um `.pjc` utilizável.
- [ ] Bloqueia início quando o Excel ou o modelo não passam na validação.
- [ ] O Excel original permanece byte a byte inalterado.

## Processamento de um registro
- [ ] Importa o modelo.
- [ ] Preenche nome, CPF e data final.
- [ ] Salva e confirma sucesso.
- [ ] Regera Verbas, FGTS e Contribuição Social.
- [ ] Preenche Histórico Salarial e confere quantidade, primeiro e último valores.
- [ ] Liquida e confirma sucesso.
- [ ] Gera PDF válido.
- [ ] Exporta ZIP válido contendo `.pjc`.

## Robustez
- [ ] Não usa coordenadas fixas como caminho principal.
- [ ] Aguarda condições reais, não apenas tempos fixos.
- [ ] Tem timeout e tentativa limitada por etapa.
- [ ] Salva captura, HTML e erro estruturado em falhas.
- [ ] Retoma lote sem refazer registros concluídos.
- [ ] Não sobrescreve saída válida silenciosamente.
- [ ] Mascara CPF em logs.

## Lote
- [ ] Teste de 1 registro aprovado.
- [ ] Teste de 5 registros aprovado.
- [ ] Teste de 50 registros aprovado.
- [ ] Taxa de conclusão e erros exportável em CSV/JSON.
