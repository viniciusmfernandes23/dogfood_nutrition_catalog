# Dog Food Nutrition Catalog & Price Tracker 🐕🥗💰

Este projeto é um pipeline automatizado de Engenharia de Dados focado na extração, normalização e análise de produtos de alimentação canina. Ele coleta dados da API da Cobasi, extrai informações nutricionais via web crawling e gera um Data Warehouse local em formato CSV, otimizado para visualização em ferramentas de BI como Power BI.

## 🚀 Funcionalidades Principais

- **Extração Híbrida:** Combina requisições de API VTEX para metadados de produtos com Web Crawling para extração de Níveis de Garantia.
- **Motor de Normalização Inteligente:** Converte automaticamente unidades disparates (%, g/kg, mg/kg) para unidades canônicas, resolvendo ambiguidades biológicas e corrigindo erros de escala comuns (10x, 100x).
- **Auditoria de Coerência Nutricional (v1.3.0):** Implementa validações biológicas avançadas para garantir a integridade dos dados, verificando:
    - **Soma de Macronutrientes:** Proteína + Gordura + Fibra + Cinzas <= 1000 g/kg.
    - **Razão Cálcio:Fósforo (Ca:P):** Valida proporções biológicas (ideal 1:1 a 2:1).
    - **Coerência Energia vs Umidade:** Detecta e corrige erros de escala em rações úmidas (ex: umidade > 70% e energia > 2500 kcal/kg).
    - **Mínimo vs Máximo:** Corrige inversões de valores (ex: Cálcio Mínimo > Cálcio Máximo).
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

## 🐛 Histórico de Correções Recentes (v1.2.0 - v1.3.0)

Este projeto passou por uma série de refinamentos para garantir a máxima integridade e precisão dos dados:

-   **v1.2.0 - Eliminação de Dados Antigos e Valores Impossíveis:**
    -   **Problema:** Persistência de dados antigos (`1.7e16` para sódio) devido a lógica de `append` e `clean_output` que preservava arquivos. Valores de energia metabolizável inflados (`35000`).
    -   **Solução:** Desativação da escala legada, limpeza total de `fact_nutrient.csv` no modo `full`, e melhoria na lógica de deduplicação de preços. Implementação de auto-correção recursiva no `Resolver` para valores astronômicos.

-   **v1.2.1 - Sincronização de Timezone e Limpeza de Cache:**
    -   **Problema:** Inconsistência de `collected_at` (ex: `07/07 21:00` vs `09/07 00:00`) devido a uso de UTC e problemas de cache de módulos Python.
    -   **Solução:** Padronização do `collected_at` para horário local em todo o pipeline, e implementação de uma "Bomba de Limpeza" para remover arquivos `.pyc` e `__pycache__` no início da execução, forçando o carregamento do código mais recente.

-   **v1.2.2 - Trava de Imutabilidade e Tolerância Zero:**
    -   **Problema:** Re-normalização em cascata que transformava valores corretos em astronômicos novamente, e persistência de valores como `1.7e16`.
    -   **Solução:** Trava de plausibilidade no `Engine` para ignorar unidades originais se o valor já estiver no range. Redução do limite de "valor astronômico" para `100.000` no `Resolver`, com anulação imediata de qualquer valor acima disso.

-   **v1.2.3 - Trava de Sanidade Final no Exporter:**
    -   **Problema:** Mesmo com todas as correções, artefatos de dados corrompidos ainda podiam "escapar" para o CSV final.
    -   **Solução:** Implementação de uma validação final no `Exporter` que anula qualquer `nutrient_value` ou `price` que seja maior que `100.000` ou negativo, garantindo que o arquivo final esteja limpo.

-   **v1.2.4 - Eliminação de Artefatos de Ponto Flutuante:**
    -   **Problema:** Valores como `1700.0000000000002` eram exibidos de forma confusa (ex: `1.7E+16`) em visualizadores devido à precisão de ponto flutuante.
    -   **Solução:** Arredondamento global para 2 casas decimais no `Resolver` e no `Exporter`, garantindo que os valores numéricos sejam limpos e facilmente interpretáveis.

-   **v1.2.5 - Heurísticas de Escala Biológica e Tratamento de Erros Sistemáticos:**
    -   **Problema:** Erros sistemáticos de escala (10x, 100x), confusão de unidades (g vs mg) e valores por porção (energia baixa) que não eram totalmente corrigidos.
    -   **Solução:** Implementação de heurísticas de `decimal_shift_down` (divisão por 10/100) e `decimal_shift_up` (multiplicação por 10/100/1000) no `Resolver`. Ajuste dos `target_min/max` e `overscale_factors` no `rules.py` para macronutrientes, minerais e energia, permitindo a correção de valores como `8200` para `820` e `35000` para `3500`.

-   **v1.3.0 - Auditoria de Coerência Nutricional e Integridade Biológica:**
    -   **Problema:** Falta de validações cruzadas que garantissem a coerência biológica do conjunto de nutrientes de um produto.
    -   **Solução:** Implementação de um `_audit_biological_coherence` no `NormalizationEngine` com as seguintes regras:
        -   **Soma de Macronutrientes:** `Proteína + Gordura + Fibra + Cinzas <= 1000 g/kg`.
        -   **Razão Cálcio:Fósforo (Ca:P):** Validação de proporção biológica (ideal 1:1 a 2:1).
        -   **Coerência Energia vs Umidade:** Detecção e correção de erros em rações úmidas (ex: umidade > 70% e energia > 2500 kcal/kg).
        -   **Mínimo vs Máximo:** Correção de inversões de valores (ex: `calcium_min > calcium_max`).

## 🔧 Tecnologias Utilizadas

- **Python 3.11+**
- **Pandas:** Manipulação e análise de dados.
- **Httpx:** Requisições assíncronas e robustas.
- **BeautifulSoup4:** Parsing de HTML para crawling.
- **Regex:** Extração precisa de padrões nutricionais.

---
Desenvolvido para fins de consultoria e análise de mercado pet.
