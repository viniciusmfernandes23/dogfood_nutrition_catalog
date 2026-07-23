# Relatório Técnico: Regras de Normalização e Auditoria Nutricional (v1.4.0)

Este documento detalha a lógica aplicada pelo pipeline de dados para garantir a integridade e a qualidade das informações nutricionais do catálogo de rações.

---

## 1. Fluxo de Normalização de Unidades
O sistema utiliza um motor de resolução (`Resolver`) que processa cada nutriente individualmente, seguindo esta hierarquia:

### Energia Metabolizável (`kcal/kg`)
*   **Unidades Aceitas**: `kcal/kg`, `kcal/100g`, `MJ/kg`, `kcal/sache`.
*   **Conversões**:
    *   `kcal/100g` → Multiplicado por 10.
    *   `MJ/kg` → Multiplicado por 239.006.
    *   `kcal/sache` → Convertido com base em **85g** por sachê (Fórmula: `(valor / 85) * 1000`).
*   **Barreira Sanitária**: Valores finais menores que **500** ou maiores que **9000 kcal/kg** são anulados por implausibilidade biológica.

### Macronutrientes (`g/kg`)
*   **Nutrientes**: Proteína, Gordura, Fibra, Cinzas e Umidade.
*   **Unidades Aceitas**: `%`, `g/kg`, `mg/kg`.
*   **Conversões**:
    *   `%` → Multiplicado por 10.
    *   `mg/kg` → Dividido por 1000.

### Minerais e Aminoácidos (`mg/kg`)
*   **Unidades Aceitas**: `%`, `g/kg`, `mg/kg`, `mcg`, `ppm`.
*   **Conversões**:
    *   `%` → Multiplicado por 10.000.
    *   `g/kg` → Multiplicado por 1000.
    *   `mcg` → Multiplicado por 0.001.

---

## 2. Auditorias Biológicas e Balanços (Cross-Validation)
Após a normalização individual, o sistema realiza validações cruzadas para detectar erros de coleta ou rotulagem.

### Balanço de Massa (Prioridade Crítica)
A soma dos macronutrientes principais (**Proteína + Gordura + Fibra + Cinzas + Umidade**) é validada para garantir que o produto seja nutricionalmente plausível.
*   **Intervalo Alvo**: **850 a 1050 g/kg**.
*   **Ações**:
    *   **< 850 g/kg**: O produto é marcado para **Auditoria (`REVIEW`)**. Indica possível falta de dados ou erro de escala.
    *   **> 1050 g/kg**: O produto é marcado como **Falha Crítica (`FAILED`)** e os valores são anulados. É fisicamente impossível ter mais de 1000g de nutrientes em 1kg de produto.
*   **Impacto na Energia**: Se o balanço de massa falha criticamente, a **Energia Metabolizável também é anulada**, pois o cálculo calórico depende da precisão dos macros.

### Razão Cálcio : Fósforo (Ca:P)
*   **Regra**: A relação entre Cálcio e Fósforo deve estar entre **1:1 e 2:1**.
*   **Ação**: Razões fora deste intervalo (ex: 0.5:1 ou 3:1) resultam na anulação de ambos os minerais e marcação para auditoria.

### Limites de Microminerais
O sistema verifica se minerais como Sódio, Potássio, Magnésio, Zinco, etc., estão dentro de faixas seguras definidas por órgãos reguladores (como AAFCO/FEDIAF).
*   **Petiscos/Suplementos**: Os limites são flexibilizados em **3x**, pois estes produtos possuem densidade nutricional específica.

---

## 3. Heurísticas de Correção Automática (`Auto-Correction`)
Quando um valor falha na validação inicial, o sistema tenta corrigi-lo através de:
1.  **Deslocamento Decimal (10x, 100x)**: Corrige erros comuns de digitação ou leitura (ex: 168 g/kg em vez de 16,8 g/kg).
2.  **Troca de Unidade Implícita**: Tenta converter o valor assumindo que a unidade coletada estava errada (ex: um valor de 2500 em "Proteína %" é tentado como "Proteína mg/kg").
3.  **Auditoria de "Already Normalized"**: Mesmo que o dado pareça correto na origem, ele é forçado a passar por todas as barreiras biológicas acima para garantir que não haja "falsos positivos".

---

## 4. Classificação e Ficha Técnica
*   **Prioridade**: Dados da **Ficha Técnica (VTEX)** têm precedência absoluta sobre a classificação semântica.
*   **Atributos**: Porte, Idade, Tipo de Ração, etc., são mapeados diretamente para evitar os "buracos" de 90% de dados vazios observados anteriormente.
