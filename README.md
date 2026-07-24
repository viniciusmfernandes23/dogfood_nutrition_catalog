# Dog Food Nutrition Catalog & Price Tracker 🐕🥗💰

Este projeto é um pipeline automatizado de Engenharia de Dados focado na extração, normalização e análise de produtos de alimentação canina. Ele coleta dados de múltiplos marketplaces (Cobasi, Petlove), extrai informações nutricionais via web crawling e gera um Data Warehouse local em formato CSV, otimizado para visualização em ferramentas de BI como Power BI.

## 🚀 Fluxo de Dados

O pipeline opera em um ciclo de vida refinado, garantindo que o dado bruto seja transformado em informação de negócio confiável:

```mermaid
flowchart TD
    subgraph Ingestion["1. Camada de Ingestão (Collectors)"]
        A1[API VTEX - Cobasi] -->|JSON Payload| B1[API Collector]
        A2[Web Scraping] -->|HTML/Text| B2[Cobasi Crawler]
    end

    subgraph Processing["2. Motor de Processamento (Core)"]
        B1 & B2 --> C1{Nutrition Parser}
        C1 -->|Regex & Aliases| D1[Normalization Resolver]
        D1 -->|Escala 10x/100x & Unidades| E1[Biological Engine]
        E1 -->|Balanço de Massa 600-1050| F1[Semantic Engine]
        F1 -->|Tier, Age & Category| G1[Data Integrity Guard]
    end

    subgraph Storage["3. Camada de Armazenamento (Warehouse)"]
        G1 -->|Star Schema| H1[(dim_product.csv)]
        G1 -->|Nutrientes Long| H2[(fact_nutrient.csv)]
        G1 -->|Preços Snapshot| H3[(fact_price_snapshot.csv)]
        G1 -->|Audit Trail| H4[(sanity_audit_logs.csv)]
    end

    subgraph BI["4. Camada de Visualização"]
        H1 & H2 & H3 --> I1[Power BI Dashboard]
        H4 --> I2[Auditoria & Qualidade]
    end

    %% Estilização
    classDef ingestion fill:#f9f,stroke:#333,stroke-width:2px;
    classDef processing fill:#bbf,stroke:#333,stroke-width:2px;
    classDef storage fill:#dfd,stroke:#333,stroke-width:2px;
    classDef bi fill:#fdd,stroke:#333,stroke-width:2px;

    class A1,A2,B1,B2 ingestion;
    class C1,D1,E1,F1,G1 processing;
    class H1,H2,H3,H4 storage;
    class I1,I2 bi;
```

## 🌟 Funcionalidades Principais

- **Extração Híbrida Multi-Fonte:** Coleta metadados e preços via API VTEX (Cobasi) e Web Crawling (Petlove).
- **Motor de Normalização Avançado:** 
    - Resolve automaticamente disparidades de unidades (%, g/kg, mg/kg, UI/kg, kcal/kg).
    - Corrige erros sistemáticos de escala (10x, 100x) através de heurísticas de plausibilidade.
    - Mantém rastreabilidade completa (`original_value` vs `normalized_value`).
- **Auditoria Biológica de Precisão:**
    - **Balanço de Massa (v1.5.6):** Verifica se a soma de macronutrientes (Proteína, Gordura, Fibra, Cinzas e Umidade) está na faixa biológica (**600-1050 g/kg**), acomodando Carboidratos (NFE) não declarados.
    - **Razão Ca:P:** Valida a relação essencial entre Cálcio e Fósforo (1:1 a 2:1).
    - **Contexto de Categoria:** Flexibiliza automaticamente limites para Petiscos e Suplementos (até 3x o teto padrão).
    - **Energia Metabolizável:** Validação determinística com correção automática de escala (10x, 100x) e suporte a múltiplas unidades (kcal/kg, MJ/kg, kcal/sachê).
- **Data Warehouse Star Schema:**
    - **`dim_product`**: Cadastro limpo de produtos com atributos de Porte, Idade, Tier, Linha e Imagem (Tooltip Ready).
    - **`fact_nutrient`**: Perfil nutricional detalhado no formato LONG para análises granulares.
    - **`fact_price_snapshot`**: Histórico temporal de preços por SKU/Embalagem.
- **Power BI Ready:** Dados exportados com Camada Semântica (nomes amigáveis) e codificação UTF-8-SIG para compatibilidade imediata.

## 📁 Estrutura do Projeto

```text
├── app/
│   ├── collectors/    # Ingestão de dados (Cobasi, Petlove)
│   ├── normalization/ # Motor de normalização e auditoria biológica
│   ├── parsers/       # Extração de dados via Regex e HTML
│   ├── semantic/      # Classificação e enriquecimento semântico
│   └── warehouse/     # Modelagem Star Schema e exportação
├── data/
│   └── output/        # Arquivos CSV finais (Warehouse)
├── docs/              # Relatórios técnicos e documentação
└── executar_pipeline.py # Ponto de entrada principal
```

## 🛠️ Como Executar

1.  **Instale as dependências:**
    ```bash
    pip install -r app/requirements.txt
    ```

2.  **Execute o pipeline completo:**
    ```bash
    python executar_pipeline.py --mode full
    ```

3.  **Execute apenas atualização de preços:**
    ```bash
    python executar_pipeline.py --mode price
    ```

## 📖 Documentação Adicional

Para detalhes sobre as regras de negócio e histórico de melhorias:
- [**Relatório Técnico Consolidado**](docs/RELATORIO_TECNICO_CONSOLIDADO.md)

---
Desenvolvido para análise técnica e estratégica do mercado pet.
