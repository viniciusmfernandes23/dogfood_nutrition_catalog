# Dog Food Nutrition Catalog & Price Tracker 🐕🥗💰

Este projeto é um pipeline automatizado de Engenharia de Dados focado na extração, normalização e análise de produtos de alimentação canina. Ele coleta dados da API da Cobasi, extrai informações nutricionais via web crawling e gera um Data Warehouse local em formato CSV, otimizado para visualização em ferramentas de BI como Power BI.

## 🚀 Funcionalidades Principais

- **Extração Híbrida:** Combina requisições de API VTEX para metadados de produtos com Web Crawling para extração de Níveis de Garantia.
- **Motor de Normalização Inteligente:** Converte automaticamente unidades disparates (%, g/kg, mg/kg) para unidades canônicas, resolvendo ambiguidades biológicas e corrigindo erros de escala comuns (10x, 100x).
- **Auditoria Biológica Avançada (v1.4.x):** Implementa validações cruzadas rigorosas para garantir a integridade dos dados:
    - **Soma de Macronutrientes:** Validação de densidade nutricional total.
    - **Razão Cálcio:Fósforo (Ca:P):** Faixa biológica ajustada (0.9 a 4.5).
    - **Âncora de Umidade:** Correção automática de energia em dietas úmidas.
    - **Densidade de Sódio:** Detecção de erros de escala via correlação com proteína.
- **Robustez de Coleta:** Mecanismo de **Retry Inteligente** com backoff exponencial para lidar com instabilidades de API.
- **Power BI Ready:** Exportação em formato regional brasileiro (R$) e modelagem Star Schema.
- **Inteligência Semântica:** Classificação automática de Porte, Idade, Tier e Fonte de Proteína.

## 📁 Estrutura do Projeto

```text
├── app/
│   ├── collectors/    # Módulos de extração (API e Crawler)
│   ├── normalization/ # Motor de conversão e validação nutricional
│   ├── parsers/       # Extração de dados via Regex e HTML
│   ├── semantic/      # Classificação e enriquecimento semântico
│   └── warehouse/     # Lógica de persistência e exportação incremental
├── data/
│   └── output/        # Pasta dedicada para arquivos CSV finais (Warehouse)
├── docs/              # Documentação técnica e relatórios consolidados
└── executar_pipeline.py # Ponto de entrada do projeto
```

## 📖 Documentação Técnica

Para detalhes aprofundados sobre a arquitetura, histórico de correções e esquema de dados, consulte o relatório consolidado:
- [**Relatório Técnico Consolidado**](docs/RELATORIO_TECNICO_CONSOLIDADO.md)


## 🛠️ Como Executar

1.  **Instale as dependências:**
    ```bash
    pip install -r app/requirements.txt
    ```

2.  **Execute o pipeline:**
    ```bash
    python executar_pipeline.py --mode full
    ```
    *Use `--mode full` para garantir a limpeza completa e reprocessamento de todos os dados, ativando todas as novas validações e correções.*

3.  **Verifique os resultados:**
    Os arquivos serão gerados na pasta `/output`:
    - `dim_product.csv`: Cadastro de produtos.
    - `fact_nutrient.csv`: Histórico de níveis nutricionais.
    - `fact_price_snapshot.csv`: Histórico de preços semanal.

## 📊 Modelagem de Dados

O projeto segue os princípios de Data Warehousing:
- **Dimensões:** Mantêm o estado atual dos produtos.
- **Fatos:** Registram eventos no tempo (coletas de preços e nutrientes), permitindo análises de séries temporais.

## 🐛 Histórico de Versões Recentes

-   **v1.4.4:** Correção da regressão do Potássio via word boundaries (\b).
-   **v1.4.3:** Correção global de escalas de exportação e priorização de agregação.
-   **v1.4.2:** Mecanismo de Retry Inteligente na API Cobasi.
-   **v1.4.1:** Auditoria Biológica Avançada e travas de minerais essenciais.
-   **v1.4.0:** Padronização de Schema e Sincronização de Timezone.
-   **v1.3.x:** Introdução da Auditoria de Coerência Nutricional.
-   **v1.2.x:** Implementação da Barreira de Sanidade Final e eliminação de artefatos de ponto flutuante.

## 🔧 Tecnologias Utilizadas

- **Python 3.11+**
- **Pandas:** Manipulação e análise de dados.
- **Httpx:** Requisições assíncronas e robustas.
- **BeautifulSoup4:** Parsing de HTML para crawling.
- **Regex:** Extração precisa de padrões nutricionais.

---
Desenvolvido para fins de consultoria e análise de mercado pet.
