# Relatório Técnico: Catálogo de Nutrição Canina

Este documento detalha a arquitetura do projeto, as funcionalidades de cada componente e o histórico completo de correções aplicadas para garantir a integridade dos dados nutricionais e financeiros.

---

## 1. Visão Geral do Projeto

O projeto é um pipeline automatizado de extração, normalização e armazenamento de dados nutricionais de rações caninas. Ele utiliza APIs e crawlers para coletar informações brutas, aplica inteligência semântica para categorização e normaliza valores nutricionais para padrões biológicos aceitáveis, exportando os resultados em um formato otimizado para análise no Power BI.

---

## 2. Estrutura do Repositório e Funcionalidades

### 📂 Raiz do Projeto
*   **`executar_pipeline.py`**: Orquestrador principal. Coordena a coleta (API/Crawler), o processamento (Normalização/Semântica) e a exportação final, aplicando regras de formatação de moeda e escala.
*   **`README.md`**: Instruções gerais de uso e instalação.
*   **`RELATORIO_TECNICO.md`**: Este documento de referência técnica.

### 📂 `app/collectors` (Módulos de Coleta)
*   **`cobasi_api.py`**: Integração com a API VTEX da Cobasi. Busca produtos por categoria e metadados de estoque/preço.
*   **`crawler.py`**: Realiza o *scraping* das páginas de produto para extrair a seção de "Níveis de Garantia".
*   **`http_client.py`**: Centraliza requisições HTTP com lógica de retentativas e tratamento de erros.
*   **`models.py`**: Dataclasses que definem o contrato de dados da coleta inicial.

### 📂 `app/parsers` (Extração de Informação)
*   **`aliases.py`**: Mapeia sinônimos de nutrientes (ex: "EM" = "Energia Metabolizável") para chaves canônicas.
*   **`regex_patterns.py`**: Define padrões complexos para capturar números (com milhar/decimal) e unidades (%, g/kg, kcal/kg).
*   **`nutrition_parser.py`**: Converte blocos de texto em dados estruturados (valor, unidade, alias).
*   **`html_parser.py`**: Identifica e isola a tabela nutricional dentro do HTML bruto.

### 📂 `app/normalization` (Motor de Integridade)
*   **`engine.py`**: Aplica a normalização campo a campo, gerenciando o lookup de unidades originais.
*   **`resolver.py`**: "Cérebro" do sistema; resolve ambiguidades e aplica fatores de correção baseados em regras.
*   **`rules.py`**: Define limites biológicos (ranges) e fatores de escala para cada nutriente.
*   **`models.py`**: Modelos de dados para o log e resultado da normalização.
*   **`validator.py`**: Verifica se os valores resultantes são plausíveis.
*   **`transforms.py`**: Implementa as transformações matemáticas (overscale, decimal shift).

### 📂 `app/semantic` (Enriquecimento de Dados)
*   **`classifier.py`**: Classificador por palavras-chave com normalização de texto.
*   **`engine.py`**: Atribui atributos como Porte, Idade, Tier e Fonte de Proteína.
*   **`rules.py`**: Regras de negócio para a classificação semântica.
*   **`categories.py`**: Definição dos Enums de categorias.

### 📂 `app/warehouse` (Armazenamento Otimizado)
*   **`models.py`**: Define o schema final das tabelas `dim_product`, `fact_nutrient` e `fact_price_snapshot`.
*   **`dim_product.py`**: Constrói o cadastro único de produtos, remapeando URLs e metadados.
*   **`fact_nutrient.py`**: Gera a tabela fato de nutrientes em formato longo.
*   **`fact_price_snapshot.py`**: Registra o histórico de preços e disponibilidade.
*   **`exporter.py`**: Gerencia a escrita dos CSVs com suporte a sobrescrita controlada.
*   **`pipeline.py`**: Encadeia a construção de todas as tabelas do warehouse.

---

## 3. Histórico de Correções e Melhorias

| Categoria | Problema | Solução Aplicada |
| :--- | :--- | :--- |
| **Escalabilidade** | Limite fixo de 50 produtos. | Removido o truncamento `df.head(50)` em `executar_pipeline.py`. |
| **Nutrientes** | Valores 10x maiores que o real. | Corrigida a escala em `executar_pipeline.py` e ajustado `overscale_factor` em `rules.py`. |
| **Financeiro** | Erro de milhar no Power BI (57,27 -> 5.727). | Adotado formato decimal brasileiro (vírgula) sem separador de milhar no CSV. |
| **Integridade** | Duplicatas e somas impossíveis no relatório. | Implementada limpeza de diretório (`overwrite=True`) no `PipelineOrchestrator`. |
| **Otimização** | Colunas 100% vazias no Warehouse. | Schema otimizado em `models.py` e remapeamento de `url` para `product_url`. |
| **Captura** | Ausência de Cálcio e Energia Metabolizável. | Expandidos aliases, regex de milhar e lookup de unidades especiais (`engine.py`). |

---

## 4. Nota de Projeto: Escala 10x e Milhar
O sistema foi projetado para ser robusto contra variações de digitação nos rótulos:
1.  **Escala 10x**: Internamente, o parser pode capturar valores multiplicados por 10 para preservar decimais em inteiros. A camada de normalização reverte isso automaticamente.
2.  **Milhar**: O parser agora identifica pontos como separadores de milhar (ex: `3.500 kcal/kg`), evitando que sejam lidos erroneamente como decimais (`3.5`).

---
**Status Atual:** Estável / Otimizado para Power BI.
**Última Atualização:** 07 de Julho de 2026.
