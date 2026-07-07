# Relatório Técnico de Auditoria Ocorrida em Gravação de Tela
## Mapeamento Operacional Detalhado — Fluxo de Trabalho PJe-Calc Cidadão & Microsoft Excel

---

### 1. Resumo Executivo do Processo
Este relatório documenta a análise técnica detalhada extraída a partir da gravação de tela operacional do sistema **PJe-Calc Cidadão** (Versão 2.14.0, rodando em ambiente local) integrada com planilhas analíticas do **Microsoft Excel**. O objetivo do fluxo auditado consiste na importação de um cálculo trabalhista padrão, substituição e parametrização dos dados cadastrais do novo reclamante, atualização cronológica de verbas/FGTS/INSS, injeção em lote de histórico de valores monetários e exportação dos relatórios oficiais.

**Metadados Identificados Principais:**
* **Nome do Reclamante:** RENATO APARECIDO DIAS (Substituído a partir da linha 1376 da planilha)
* **Identificação do Processo:** 0010953-19.2017.5.03.0034
* **CPF do Reclamante:** 233.441.986-96 (Extraído da aba de CPFs da planilha)
* **Data de Admissão:** 08/09/2010
* **Data de Demissão (Limite do Cálculo):** 20/04/2020

---

### 2. Tabela Geral de Ações Estruturadas (Mapeamento JSON Sintético)

| Ordem | Timestamp | Aba/Módulo Utilizado | Botão Clicado | Campo Preenchido | Origem do Dado (Excel) | Tempo de Espera |
| :---: | :---: | :--- | :--- | :--- | :--- | :---: |
| **1** | 00:00 - 00:10 | Gravador de Tela Online | Nenhum (Início) | Nenhum | N/A | 10s |
| **2** | 00:11 - 00:12 | PJe-Calc (Início) | Importar Cálculo | Nenhum | N/A | < 1s |
| **3** | 00:13 - 00:14 | Geral > Importar > Importação | Escolher Arquivo... | Nenhum | N/A | < 1s |
| **4** | 00:15 - 00:17 | Janela OS (File Upload) | 'modelo.pjc' / Abrir | Nome do arquivo | Sistema Local | 2s |
| **5** | 00:18 - 00:19 | Geral > Importar > Importação | Confirmar | Nenhum | N/A | 1s |
| **6** | 00:20 - 00:23 | Cálculo > Dados do Cálculo | Nenhum | Campos do Cálculo | Metadados .pjc | 3s |
| **7** | 00:24 - 00:29 | Planilha Excel | Barra de Rolagem | Nenhum | Aba 'ANEXO I' | 5s |
| **8** | 00:30 - 00:31 | Planilha Excel | Seleção Célula C1376 | Nenhum | Célula C1376 (Nome) | < 1s |
| **9** | 00:32 - 00:37 | Cálculo > Dados do Cálculo | Campo Nome (Reclamante) | Nome do Reclamante | Área de Transf. | 5s |
| **10** | 00:38 - 00:41 | Planilha Excel | Troca de Aba (C277) | Nenhum | Aba 'lista_1200_cpf' | 3s |
| **11** | 00:41 - 00:42 | Cálculo > Dados do Cálculo | Campo Número (CPF) | CPF do Reclamante | Área de Transf. | 1s |
| **12** | 00:43 - 00:54 | Cálculo > Parâmetros Cálculo | Sub-aba Parâmetros | Nenhum | N/A (Conferência) | 11s |
| **13** | 00:55 - 00:57 | Cálculo > Parâmetros Cálculo | Campo Data Final | Data Final (20/04/2020) | Coluna E (Demissão) | 2s |
| **14** | 00:58 - 01:00 | Cálculo > Parâmetros Cálculo | Salvar (Rodapé) | Nenhum | N/A | 2s |
| **15** | 01:01 - 01:04 | Menu Lateral Esquerdo | Opção 'Verbas' | Nenhum | N/A | 3s |
| **16** | 01:04 - 01:06 | Cálculo > Verbas > Listar | Regerar > Confirmar OK | Nenhum | N/A | 2s |
| **17** | 01:07 - 01:10 | Menu Lateral Esquerdo | Opção 'FGTS' | Nenhum | N/A | 3s |
| **18** | 01:10 - 01:16 | Cálculo > FGTS | Regerar (Topo) | Nenhum | N/A (Scroll) | 6s |
| **19** | 01:17 - 01:20 | Cálculo > FGTS > Regerar | Confirmar | Nenhum | Parâmetros de Data | 3s |
| **20** | 01:20 - 01:22 | Menu Lateral Esquerdo | Opção 'Contribuição Social' | Nenhum | N/A | 2s |
| **21** | 01:22 - 01:26 | Cálculo > Contribuição Social | Regerar | Nenhum | N/A (Scroll) | 4s |
| **22** | 01:27 - 01:31 | Cálculo > Contribuição Previd. | Confirmar | Nenhum | Parâmetros de Data | 4s |
| **23** | 01:31 - 01:33 | Menu Lateral Esquerdo | Opção 'Histórico Salarial' | Nenhum | N/A | 2s |
| **24** | 01:33 - 01:36 | Cálculo > Histórico Salarial | Ícone Amarelo (Editar) | Nenhum | N/A | 3s |
| **25** | 01:37 - 01:54 | Planilha Excel | Seleção de Bloco | Nenhum | Coluna G/H (Valores) | 17s |
| **26** | 01:55 - 01:59 | Utilitário Copiar/Colar PJe | Seleção de Célula inicial | Inicialização | Área de Transf. | 4s |
| **27** | 02:00 - 02:14 | Cálculo > Histórico Salarial | Automação Ativa | Valores Mensais Base | Vetor de Células | 14s |
| **28** | 02:15 - 02:17 | Cálculo > Histórico Salarial | Salvar (Rodapé) | Nenhum | N/A | 2s |
| **29** | 02:18 - 02:23 | Menu Lateral > Operações | Opção 'Liquidar' | Nenhum | N/A | 5s |
| **30** | 02:24 - 02:27 | Operações > Liquidar | Liquidar (Botão) | Nenhum | Consolidação Geral | 3s |
| **31** | 02:28 - 02:30 | Menu Lateral > Operações | Opção 'Imprimir' | Checkboxes marcados | N/A | 2s |
| **32** | 02:31 - 02:39 | Operações > Imprimir | Imprimir (Botão) | Nenhum | Compilação PDF | 8s |
| **33** | 02:40 - 02:47 | Janela OS (Salvar Como) | Salvar | Nome do PDF | Nome do Reclamante | 7s |
| **34** | 02:48 - 02:51 | Menu Lateral > Operações | Opção 'Exportar' | Nenhum | N/A | 3s |
| **35** | 02:52 - 03:05 | Operações > Exportar / Janela OS | Exportar / Salvar | Nome do ZIP | Nome do Reclamante | 13s |
| **36** | 03:06 - 03:08 | Gravador de Tela Online | Parâmetros de Parada | Nenhum | N/A | 2s |

---

### 3. Detalhamento dos Processos com Capturas de Tela

#### Passo A: Importação de Arquivo Base do Cálculo (.pjc)
* **Descrição:** O operador acessa o módulo de importação para trazer uma estrutura de cálculo pré-existente (arquivo `modelo.pjc`), servindo como base configurada para agilizar o novo processo de liquidação.
* **Ações Realizadas:** Clique em 'Importar Cálculo' -> 'Escolher Arquivo...' -> Seleção local do arquivo -> Confirmação.
* **Tempo de espera total observado:** 8 segundos.

![Importação do Cálculo](screenshots/01_importar_calculo.png)
*Figura 1: Acionamento da rotina inicial de importação de arquivo externo no PJe-Calc.*

![Confirmação dos Dados Importados](screenshots/02_dados_carregados.png)
*Figura 2: Tela com dados do processo carregados automaticamente após leitura bem-sucedida.*

---

#### Passo B: Higienização e Cadastramento dos Dados do Novo Reclamante
* **Descrição:** Utilizando o Microsoft Excel no formato lado a lado, o usuário navega pela planilha de empregados até localizar os dados do funcionário *Renato Aparecido Dias*. Ele extrai e transfere o nome exato e o CPF específico.
* **Ações Realizadas:** Rolagem no Excel -> Cópia do nome (Ctrl+C) -> Colagem no campo Reclamante (Ctrl+V) -> Troca de aba no Excel -> Cópia do CPF -> Colagem no campo Documento Fiscal.
* **Teclas pressionadas:** `Ctrl + C`, `Ctrl + V`, rolagens e cliques de mouse.

![Busca de Registro no Excel](screenshots/03_excel_copia_nome.png)
*Figura 3: Navegação na planilha Excel para localização e cópia dos dados identificadores do reclamante.*

![Injeção de Identificação e CPF](screenshots/04_preenchimento_nome_cpf.png)
*Figura 4: Dados preenchidos e validados nos campos estruturados do PJe-Calc.*

---

#### Passo C: Parametrização Cronológica do Período do Cálculo
* **Descrição:** Ajuste fino das limitações do cálculo. Com base na data de demissão fornecida na planilha (20/04/2020), a data final padrão do cálculo foi editada, garantindo que nenhuma verba sofra apuração indevida fora do pacto laboral.
* **Ações Realizadas:** Alteração do campo 'Data Final' de 30/06/2026 para 20/04/2020 -> Clique em 'Salvar' -> Confirmação de modal.

![Alteração de Parâmetros de Data](screenshots/05_alteracao_data_final.png)
*Figura 5: Janela de alteração da Data Final limitadora do cálculo trabalhista.*

---

#### Passo D: Atualização e Regeração das Ocorrências em Lote
* **Descrição:** Devido à contração/ajuste do escopo temporal do cálculo, é obrigatória a regeração sequencial de todas as tabelas acessórias. O usuário passa pelos módulos de Verbas Principais, FGTS e Contribuições Previdenciárias para regerar as parcelas de cada competência.
* **Ações Realizadas:** Cliques sucessivos nos botões 'Regerar' e 'Confirmar' nas respectivas subpáginas do menu esquerdo.
* **Tempo de espera total observado:** 27 segundos divididos entre os módulos.

![Regeração das Verbas](screenshots/06_verbas_regerar.png)
*Figura 6: Acionamento da regeração das parcelas mensais das verbas trabalhistas não reflexas.*

![Regeração de FGTS](screenshots/07_fgts_regerar.png)
*Figura 7: Processamento de recálculo das competências devidas para o Fundo de Garantia.*

![Regeração de Contribuição Social Previdenciária](screenshots/08_contrib_social_regerar.png)
*Figura 8: Alinhamento das ocorrências da Contribuição Social Previdenciária (INSS).*

---

#### Passo E: Injeção Automatizada do Histórico Salarial (Carga Lote Excel)
* **Descrição:** Inserção da série histórica de diferenças mensais de adicional noturno acumuladas. O operador seleciona dezenas de células no Excel e utiliza a macro auxiliar externa 'Copiar e Colar do PJe-CALC' para simular a digitação automática e veloz linha por linha, evitando digitação humana suscetível a erros.
* **Ações Realizadas:** Seleção da coluna no Excel -> Ativação do pop-up assistente -> Clique na célula inicial do PJe-Calc -> Preenchimento automático por lote -> Clique em Salvar.
* **Tempo de espera observado:** 14 segundos de execução mecânica simulada.

![Abertura do Histórico Salarial](screenshots/09_historico_salarial_editar.png)
*Figura 9: Tela vazia de competências pronta para o recebimento do histórico de valores.*

![Seleção das Diferenças no Excel](screenshots/10_excel_copia_valores.png)
*Figura 10: Intervalo selecionado no Excel contendo os valores calculados que serão exportados.*

![Processo de Automação Ativo](screenshots/11_preenchimento_automatico.png)
*Figura 11: Script em execução preenchendo automaticamente a tabela do PJe-Calc com os dados copiados.*

![Salvamento da Série Histórica](screenshots/12_historico_salvo.png)
*Figura 12: Dados totalmente inseridos e gravados com sucesso na base de cálculo.*

---

#### Passo F: Liquidação, Emissão e Exportação de Arquivos Finais
* **Descrição:** Processamento matemático final unificando todas as variáveis inseridas. Após a liquidação, o relatório completo de auditoria é compilado em PDF, renomeado com o nome do trabalhador e o arquivo estruturado ZIP é exportado para fins de anexação oficial no sistema de peticionamento dos tribunais.
* **Ações Realizadas:** Clique em 'Liquidar' -> Execução -> Clique em 'Imprimir' -> Espera de 8 segundos -> Salvar Como 'RENATO APARECIDO DIAS.pdf' -> Clique em 'Exportar' -> Salvar Como 'RENATO APARECIDO DIAS.zip'.

![Execução da Liquidação Final](screenshots/13_liquidacao_execucao.png)
*Figura 13: Tela de consolidação e encerramento matemático definitivo do cálculo.*

![Geração de Relatório PDF](screenshots/14_relatorio_pdf.png)
*Figura 14: Seleção das partes constitutivas para renderização do relatório final impresso.*

![Exportação de Dados Estruturados ZIP](screenshots/15_exportacao_zip.png)
*Figura 15: Conclusão do fluxo operacional com a geração e download do arquivo compactado de metadados.*

---

### 4. Conclusões da Auditoria
O fluxo monitorado seguiu de forma estrita as boas práticas de manipulação de cálculos judiciais. A utilização de utilitários de automação em lote para preenchimento de históricos de verbas garantiu a integridade matemática dos dados contidos na planilha Excel de origem para o sistema oficial. Não foram identificadas falhas operacionais, inconsistências de datas ou erros de input de valores durante a janela observada de **03 minutos e 08 segundos**.
