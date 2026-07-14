# Relatório Técnico Consolidado: Dogfood Nutrition Catalog
**Versão Atual do Pipeline:** v1.4.4
**Data da Última Atualização:** 14 de Julho de 2026

---

## 1. Visão Geral do Projeto

O **Dogfood Nutrition Catalog** é um ecossistema automatizado para extração, normalização e armazenamento de dados nutricionais e comerciais de alimentos para cães. O projeto visa transformar informações brutas e muitas vezes inconsistentes de e-commerces em um Data Warehouse estruturado, confiável e pronto para análise em ferramentas de Business Intelligence (BI).

### Objetivos Principais
- **Integridade Biológica:** Garantir que todos os valores nutricionais reflitam a realidade biológica animal.
- **Normalização Universal:** Converter diversas unidades (%, mg/kg, kcal/g) para padrões canônicos.
- **Robustez de Coleta:** Lidar com instabilidades de APIs e falhas de rede de forma resiliente.
- **Prontidão para BI:** Exportar dados limpos, sem artefatos técnicos e com formatação regional adequada.

---

## 2. Arquitetura do Sistema

O pipeline é dividido em camadas modulares, cada uma com responsabilidades claras:

### 2.1. Camada de Coleta (`app/collectors`)
- **`cobasi_api.py`**: Integração com a API VTEX da Cobasi para metadados de estoque e preços.
- **`crawler.py`**: Scraping de páginas para extração da seção de "Níveis de Garantia".
- **`http_client.py`**: Cliente centralizado com **Backoff Exponencial** e **Jitter** para retentativas em erros 500.

### 2.2. Camada de Parsing (`app/parsers`)
- **`nutrition_parser.py`**: Motor de regex que extrai nutrientes. Utiliza **Word Boundaries (\b)** para evitar conflitos de nomes (ex: "P" vs "Potássio").
- **`aliases.py`**: Dicionário exaustivo de sinônimos nutricionais em português.
- **`regex_patterns.py`**: Padrões para captura de números complexos e unidades variadas.

### 2.3. Camada de Normalização (`app/normalization`)
- **`engine.py`**: Motor que aplica regras de validação biológica e auditoria cruzada.
- **`resolver.py`**: Resolve ambiguidades e aplica transformações como `overscale` e `decimal_shift`.
- **`rules.py`**: Define os ranges biológicos aceitáveis e fatores de escala técnica.

### 2.4. Camada de Warehouse (`app/warehouse`)
- **`dim_product.py`**: Cadastro único de produtos (Dimensão).
- **`fact_nutrient.py`**: Tabela fato de nutrientes em formato longo.
- **`fact_price_snapshot.py`**: Histórico diário de preços e disponibilidade.
- **`exporter.py`**: Gerencia a escrita dos CSVs com uma **Barreira de Sanidade Final** obrigatória.

---

## 3. Esquema de Dados e Convenções

### 3.1. Unidades Canônicas (Target Units)
| Categoria | Unidade | Descrição |
| :--- | :--- | :--- |
| **Macronutrientes** | `g/kg` | Gramas por Quilograma (ex: 26% -> 260 g/kg) |
| **Minerais** | `mg/kg` | Miligramas por Quilograma (ex: 0.17% -> 1700 mg/kg) |
| **Energia** | `kcal/kg` | Quilocalorias por Quilograma (ex: 3.5 kcal/g -> 3500 kcal/kg) |
| **Preços** | `BRL` | Reais Brasileiros (arredondado para 2 casas decimais) |

### 3.2. Limites Biológicos e Regras de Sanidade
O sistema aplica filtros rigorosos para anular ou corrigir dados impossíveis:
1.  **Limite de Matéria Orgânica:** Nenhum nutriente individual > 1000 g/kg.
2.  **Soma de Macros:** Umidade + Proteína + Gordura + Fibra + Cinzas ≤ 1050 g/kg.
3.  **Âncora de Umidade:** Rações com Umidade > 70% têm Energia limitada a 1500 kcal/kg.
4.  **Razão Ca:P:** Proporção Cálcio/Fósforo deve estar entre **0.9 e 4.5**.
5.  **Densidade de Sódio:** Sódio excessivo em relação à proteína é identificado como erro de escala e anulado.

---

## 4. Histórico de Evolução (Log de Versões)

### v1.4.4 (Atual) - Correção da Regressão do Potássio
- Implementação de word boundary (\b) seletivo para evitar conflitos entre aliases curtos ("P") e longos ("Potássio").
- Restauração da cobertura total de potássio (> 500 registros).

### v1.4.3 - Precisão de Escala e Agregação
- Fim da escala 10x indevida na exportação de minerais e energia.
- Implementação de lógica de prioridade na agregação (específico > genérico).
- Bloqueio de unidades "por sachê" na energia por kg.

### v1.4.2 - Robustez na Coleta
- Implementação de Retry Inteligente no `HttpClient`.
- Remoção do fallback silencioso para dados simulados em caso de erro na API.

### v1.4.1 - Auditoria Biológica Avançada
- Trava de minerais insignificantes (< 1 mg/kg).
- Validação de macronutrientes mínimos para integridade da linha.

### v1.4.0 - Arquitetura Consolidada
- Padronização definitiva de unidades e criação do esquema de governança.
- Sincronização de Timezone (Horário Local) em todo o pipeline.

---

## 5. Notas Técnicas Especiais

### Escala e Precisão
Internamente, o pipeline foi simplificado para operar diretamente nas unidades reais onde possível. Onde escalas técnicas (10x) são usadas para preservar precisão decimal em inteiros, a **Camada Semântica** garante a reversão automática antes da escrita no CSV.

### Rastreabilidade
Todas as anulações realizadas pela **Barreira de Sanidade Final** são logadas no terminal, permitindo auditoria rápida de quais produtos possuem rótulos inconsistentes na origem (fornecedor).
