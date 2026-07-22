# Relatório Técnico Consolidado: Dogfood Nutrition Catalog
**Versão Atual do Pipeline:** v2.0.0
**Data da Última Atualização:** 22 de Julho de 2026

---

## 1. Visão Geral do Projeto

O **Dogfood Nutrition Catalog** é um ecossistema automatizado para extração, normalização e armazenamento de dados nutricionais e comerciais de alimentos para cães. O projeto visa transformar informações brutas e inconsistentes de e-commerces em um Data Warehouse estruturado, confiável e pronto para análise em ferramentas de Business Intelligence (BI).

### Objetivos Alcançados
- **Integridade Biológica:** Garantir que todos os valores nutricionais reflitam a realidade biológica animal através de auditorias cruzadas.
- **Normalização Universal:** Conversão de diversas unidades (%, mg/kg, kcal/g, UI/kg) para padrões canônicos de mercado.
- **Prontidão para BI:** Exportação de dados limpos, modelados em Star Schema e com camada semântica amigável para o Power BI.
- **Auditoria Forense:** Rastreabilidade completa do motivo de cada correção ou anulação de dado.

---

## 2. Arquitetura Técnica e Regras de Negócio

### 2.1. Motor de Normalização (`app/normalization`)
O coração do sistema é o motor de normalização, que opera em três camadas de defesa:

1.  **Resolver (Resolução Lógica):**
    - Identifica unidades originais e aplica conversões determinísticas.
    - Resolve erros de escala (10x, 100x) via heurísticas de plausibilidade.
    - **Proteção Anti-Erro:** Rejeita unidades impossíveis (ex: Magnésio em `kcal/kg`).
2.  **Engine (Auditoria Biológica Cruzada):**
    - **Balanço de Massa:** Verifica se a soma de Proteína, Gordura, Fibra, Cinzas e Umidade está entre **800 e 1050 g/kg** (aplicado quando >= 4 macronutrientes estão presentes).
    - **Razão Ca:P:** Valida se a relação Cálcio/Fósforo está entre **1.0 e 2.0**.
    - **Diferenciação por Categoria:** Petiscos e Suplementos possuem limites de micronutrientes flexibilizados em até **3x** e são isentos do balanço de massa proximal.
3.  **Barreira de Sanidade Final (`exporter.py`):**
    - Último filtro antes da escrita do arquivo físico.
    - Anula valores que excedem limites físicos absolutos (ex: Proteína > 1000g/kg ou Energia > 4500kcal/kg).

### 2.2. Modelagem de Dados (Star Schema)
O Data Warehouse é exportado em formato CSV seguindo uma estrutura de dimensões e fatos:

- **`dim_product`**: Cadastro de produtos. 
    - *Nota:* Colunas de Score foram removidas para serem calculadas dinamicamente no Power BI, garantindo uma dimensão limpa.
- **`fact_nutrient`**: Tabela fato no formato LONG.
    - Contém: `product_id`, `nutrient_key`, `nutrient_value`, `status`, `reason`.
    - Preserva o `reason` (motivo) para justificar anulações biológicas.
- **`fact_price_snapshot`**: Histórico temporal de preços por SKU/Marketplace.

---

## 3. Convenções de Unidades e Limites

| Nutriente | Unidade Alvo | Faixa Plausível (Ração) |
| :--- | :--- | :--- |
| **Proteína** | `g/kg` | 0.1 - 600 |
| **Gordura** | `g/kg` | 0.01 - 1000 |
| **Cinzas** | `g/kg` | 10 - 150 |
| **Cálcio (Min/Max)** | `mg/kg` | 100 - 60,000 |
| **Energia** | `kcal/kg` | 500 - 4500 |
| **Selênio** | `mg/kg` | 0.01 - 5 |

---

## 4. Histórico de Melhorias Recentes (Sprint de Estabilização)

### v2.0.0 - Estabilização e Auditoria Biológica
- **Recuperação de Dados Plausíveis:** Ajuste na regra de `invalid_conversion` para preservar valores reais (ex: Selênio 0.04 mg/kg) mesmo em casos de ambiguidade de unidade.
- **Refinamento do Balanço de Massa:** Implementação de lógica condicional que exige 4 ou 5 macronutrientes para validar a soma, evitando anulações indevidas por dados parciais.
- **Correção de Mapeamento:** Eliminação de bugs que atribuíam unidades de vitaminas a minerais.
- **Remoção de Lógica de BI no ETL:** Exclusão das colunas de score da `dim_product`, delegando o cálculo para a camada de visualização.
- **Rastreabilidade:** Inclusão do campo `reason` no CSV final para auditoria direta no Power BI.

---

## 5. Próximos Passos Recomendados
1.  **Integração de Novos Marketplaces:** Expandir a coleta para Petz e outros varejistas utilizando a mesma base de normalização.
2.  **Machine Learning para Classificação:** Utilizar modelos de NLP para refinar a classificação de `protein_source` e `clinical_category` com base na lista de ingredientes.
3.  **Dashboard de Qualidade de Dados:** Criar uma visão no Power BI focada nos `sanity_audit_logs.csv` para monitorar a qualidade dos rótulos dos fabricantes.

---
**Relatório gerado automaticamente pelo pipeline de documentação.**
