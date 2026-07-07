# Dog Food Nutrition Catalog & Price Tracker 🐕🥗💰

Este projeto é um pipeline automatizado de Engenharia de Dados focado na extração, normalização e análise de produtos de alimentação canina. Ele coleta dados da API da Cobasi, extrai informações nutricionais via web crawling e gera um Data Warehouse local em formato CSV, otimizado para visualização em ferramentas de BI como Power BI.

## 🚀 Funcionalidades Principais

- **Extração Híbrida:** Combina requisições de API VTEX para metadados de produtos com Web Crawling para extração de Níveis de Garantia.
- **Motor de Normalização Inteligente:** Converte automaticamente unidades disparates (%, g/kg, mg/kg) para unidades canônicas, resolvendo ambiguidades biológicas.
- **Rastreamento de Preços Histórico:** Armazenamento incremental que permite acompanhar a variação de preços ao longo das semanas sem sobreposição de dados.
- **Power BI Ready:** Exportação de dados formatados em moeda (R$) e tabelas fato/dimensão prontas para modelagem estrela (Star Schema).
- **Inteligência Semântica:** Classificação automática de categorias de produtos e análise de densidade nutricional.

## 📁 Estrutura do Projeto

```text
├── app/
│   ├── collectors/    # Módulos de extração (API e Crawler)
│   ├── core/          # Configurações globais e logging
│   ├── normalization/ # Motor de conversão e validação nutricional
│   ├── parsers/       # Extração de dados via Regex e HTML
│   ├── pipeline/      # Orquestração do fluxo de dados
│   ├── semantic/      # Classificação e enriquecimento semântico
│   └── warehouse/     # Lógica de persistência e exportação incremental
├── output/            # Pasta dedicada para arquivos CSV finais
└── executar_pipeline.py # Ponto de entrada do projeto
```

## 🛠️ Como Executar

1. **Instale as dependências:**
   ```bash
   pip install -r app/requirements.txt
   ```

2. **Execute o pipeline:**
   ```bash
   python executar_pipeline.py
   ```

3. **Verifique os resultados:**
   Os arquivos serão gerados na pasta `/output`:
   - `dim_product.csv`: Cadastro de produtos.
   - `fact_nutrient.csv`: Histórico de níveis nutricionais.
   - `fact_price_snapshot.csv`: Histórico de preços semanal.

## 📊 Modelagem de Dados

O projeto segue os princípios de Data Warehousing:
- **Dimensões:** Mantêm o estado atual dos produtos.
- **Fatos:** Registram eventos no tempo (coletas de preços e nutrientes), permitindo análises de séries temporais.

## 🔧 Tecnologias Utilizadas

- **Python 3.11+**
- **Pandas:** Manipulação e análise de dados.
- **Httpx:** Requisições assíncronas e robustas.
- **BeautifulSoup4:** Parsing de HTML para crawling.
- **Regex:** Extração precisa de padrões nutricionais.

---
Desenvolvido para fins de consultoria e análise de mercado pet.
