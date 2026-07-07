# Prompt inicial para o Codex

Leia integralmente `README_CODEX.md` e os arquivos de `spec/` antes de editar código.

Implemente uma aplicação Windows local em Python, empacotável como EXE único, que:

1. peça ao usuário um modelo PJe-Calc (`.pjc` ou `.zip` contendo `.pjc`), um Excel (`.xlsx`/`.xlsm`) e uma pasta de saída;
2. nunca altere o Excel original;
3. valide os dados antes de abrir o lote;
4. controle o PJe-Calc local em `localhost:9257` preferencialmente via Selenium/DOM, sem coordenadas fixas;
5. execute inicialmente apenas um registro em modo de teste;
6. gere PDF e ZIP oficial, valide que o ZIP contém `.pjc` e registre estado em SQLite;
7. tire captura e salve HTML quando houver erro;
8. permita retomar uma execução interrompida;
9. não use IA, API paga ou internet durante a execução;
10. não registre CPF completo nos logs.

Não tente implementar o lote inteiro sem antes criar e executar um `dom_probe` para identificar seletores reais. Faça as entregas em fases, mantendo código modular, tipado e testável. Use a extensão em `references/` como referência de comportamento, não como justificativa para automação por coordenadas.

Primeira entrega esperada:

- estrutura do projeto;
- GUI de seleção dos três caminhos;
- validação de arquivos;
- leitura/normalização do Excel;
- SQLite de controle;
- verificação de disponibilidade do PJe-Calc;
- ferramenta de inspeção de DOM e arquivo `selectors.local.json`;
- testes unitários das normalizações e validação ZIP/PDF.
