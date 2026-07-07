# Relatório Técnico: Dog Food Nutrition Pipeline

Este documento detalha a arquitetura, as funcionalidades dos componentes e as melhorias implementadas no projeto de catálogo nutricional.

## 1. Arquitetura do Sistema

O projeto é estruturado como um pipeline de dados modular, seguindo o fluxo: **Extração -> Parsing -> Normalização -> Enriquecimento -> Warehouse**.

### 1.1. Módulos de Extração (`app/collectors/`)
- **`cobasi_api.py`**: Utiliza a API VTEX da Cobasi. Foi corrigido para usar o formato de navegação por *path* (`cachorro/racao/...`) e parâmetros de `map`, garantindo a coleta de subcategorias que antes retornavam vazio.
- **`crawler.py`**: Realiza o *scraping* das páginas de produto para extrair a seção de "Níveis de Garantia", que não está disponível via API.
- **`http_client.py`**: Centraliza as requisições com lógica de *retry* e *timeout* (ajustado para 60s) para garantir resiliência.

### 1.2. Motor de Processamento (`app/parsers/` & `app/normalization/`)
- **`nutrition_parser.py`**: Extrai valores e unidades usando Regex. Foi aprimorado para detectar e propagar a unidade original (%, g/kg, mg/kg), resolvendo falhas de tipos nulos (`NaN`).
- **`resolver.py`**: O "cérebro" da normalização. Implementa heurísticas para resolver ambiguidades (ex: Sódio 2.0 g/kg vs 2.0 mg/kg), garantindo que todos os dados fato estejam em unidades canônicas biologicamente plausíveis.

### 1.3. Data Warehouse (`app/warehouse/`)
- **`exporter.py`**: Gerencia a gravação dos CSVs. Implementa a lógica de **Append Incremental** para tabelas fato, permitindo o armazenamento histórico sem sobrescrever coletas anteriores.
- **`fact_price_snapshot.py`**: Constrói o registro temporal de preços, capturando preço padrão, preço de assinante e disponibilidade.

## 2. Melhorias e Correções Implementadas

| Categoria | Descrição da Melhoria | Impacto |
| :--- | :--- | :--- |
| **Correção de Erro** | Resolução do `AttributeError` no parser ao encontrar valores `NaN`. | Estabilidade total do pipeline. |
| **Correção de Coleta** | Troca de IDs estáticos por Paths de navegação na API Cobasi. | Aumento de 0 para centenas de produtos coletados. |
| **Normalização** | Implementação de detecção de unidade e heurística de minerais. | Dados biologicamente corretos (Sódio/Potássio corrigidos). |
| **Arquitetura** | Criação de pasta `output/` dedicada e exportação incremental. | Organização do projeto e suporte a histórico semanal. |
| **BI Integration** | Formatação de campos monetários para padrão `R$`. | Facilidade de importação e leitura no Power BI. |

## 3. Funcionalidade dos Arquivos Principais

- **`executar_pipeline.py`**: Orquestrador principal. Coordena o fluxo, aplica formatações finais de moeda e organiza os arquivos na pasta de saída.
- **`app/core/config.py`**: Centraliza parâmetros como timeouts, retentativas e tamanhos de página.
- **`app/normalization/rules.py`**: Define os limites biológicos (mín/máx) para cada nutriente, usados na validação dos dados.

---
**Data do Relatório:** 07 de Julho de 2026
**Status do Sistema:** Operacional / Estável
