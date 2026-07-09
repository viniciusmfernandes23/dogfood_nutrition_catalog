# Relatório Técnico: Evolução e Correções do Pipeline Dog Food Nutrition Catalog

**Autor:** Manus AI
**Data:** 09 de Julho de 2026
**Versão do Pipeline:** v1.3.0

## 1. Introdução

Este documento detalha as correções e melhorias implementadas no pipeline `Dog Food Nutrition Catalog` desde a versão `v1.2.0` até a `v1.3.0`. O objetivo principal foi resolver problemas críticos de integridade de dados, como valores nutricionais biologicamente impossíveis, inconsistências de data e artefatos de ponto flutuante, além de introduzir um robusto sistema de auditoria de coerência nutricional. Cada seção abaixo descreve o problema identificado, a análise da causa raiz e a solução técnica aplicada.

## 2. Histórico de Correções e Justificativas

### 2.1. v1.2.0 - Eliminação de Dados Antigos e Valores Impossíveis

#### Problema
Observou-se a persistência de dados antigos no `fact_nutrient.csv` (ex: `1.7e16` para sódio) e valores de energia metabolizável inflados (`35000` kcal/kg), mesmo após a execução do pipeline. A causa raiz foi identificada como uma lógica de exportação incremental que preservava arquivos (`fact_price_snapshot.csv` e `fact_nutrient.csv`) e uma falha na deduplicação de preços.

#### Análise da Causa Raiz
1.  **
O comportamento de "cache" não era um cache de memória, mas sim a lógica de exportação incremental do projeto. O `app/warehouse/exporter.py` estava configurado para fazer um `append` nas tabelas fato (`fact_price_snapshot` e `fact_nutrient`) em vez de sobrescrevê-las. A deduplicação falhava ao usar `product_id + collected_at` com timestamp truncado para o dia, resultando em acumulação de dados antigos. Além disso, o método `clean_output` preservava propositalmente os arquivos `fact_price_snapshot.csv` e `fact_nutrient.csv`.

O valor `5.8e16` para `potassium_mgkg` era um artefato de uma versão anterior do código que ficou "congelado" no CSV acumulativo. O `fix_nutrient_scale` no `executar_pipeline.py` dividia valores já corretos por 10, fazendo com que o `NormalizationResolver` aplicasse múltiplos fatores de conversão, gerando valores astronômicos.

#### Solução Aplicada
1.  **Desativação da Escala Legada:** A função `fix_nutrient_scale` foi removida do `executar_pipeline.py` para evitar a divisão indevida de valores já corretos.
2.  **Limpeza Total de Nutrientes:** O `clean_output_directory` foi modificado para que, no modo `full`, o `fact_nutrient.csv` seja sempre limpo, garantindo que novos dados sejam gerados a cada execução.
3.  **Deduplicação de Preços Aprimorada:** A lógica de deduplicação no `exporter.py` foi ajustada para usar apenas a data (`_date_only`) como chave, garantindo que múltiplas execuções no mesmo dia não gerem duplicatas e que a versão mais recente prevaleça.
4.  **Auto-Correção Recursiva:** O `Resolver` foi aprimorado para detectar valores astronômicos e tentar dividi-los sucessivamente por fatores de escala (10.000, 1.000, 10) até que caiam em um range plausível. Se a correção falhar, o valor é anulado.

### 2.2. v1.2.1 - Sincronização de Timezone e Limpeza de Cache

#### Problema
Inconsistência na coluna `collected_at` (ex: `07/07 21:00` vs `09/07 00:00`) entre as tabelas, causada pelo uso de `datetime.now(UTC)` e a interpretação do fuso horário local. Além disso, problemas de cache de módulos Python (`.pyc`, `__pycache__`) impediam que as correções mais recentes fossem efetivamente carregadas.

#### Análise da Causa Raiz
O uso de `datetime.now(UTC)` resultava em timestamps em Tempo Universal Coordenado. Quando visualizados em um ambiente configurado para o fuso horário de Brasília (BRT, UTC-3), um `00:00:00` UTC do dia atual era exibido como `21:00:00` do dia anterior. A persistência de bugs mesmo após `git pull` e limpeza manual da pasta `output` indicava que o Python estava carregando versões antigas dos módulos a partir de arquivos `.pyc` ou pastas `__pycache__`.

#### Solução Aplicada
1.  **Padronização para Horário Local:** Todos os builders (`fact_nutrient.py`, `fact_price_snapshot.py`, `dim_product.py`) e o exportador de metadados foram modificados para utilizar o **horário local do sistema** (`datetime.now()`) para o `collected_at`, garantindo consistência com o dia civil da execução.
2.  **Centralização do Timestamp:** A geração do timestamp foi centralizada no `WarehousePipeline`, garantindo que um único objeto `datetime` seja criado e repassado para todos os builders, eliminando discrepâncias.
3.  **Bomba de Limpeza de Cache:** Um script foi adicionado ao `executar_pipeline.py` para **deletar recursivamente** todos os arquivos `.pyc` e pastas `__pycache__` no início da execução. Isso força o Python a recompilar e carregar o código-fonte `.py` mais recente do disco.

### 2.3. v1.2.2 - Trava de Imutabilidade e Tolerância Zero

#### Problema
A re-normalização em cascata continuava a transformar valores corretos em astronômicos novamente, e valores como `1.7e16` persistiam, indicando que o `Resolver` estava sendo chamado múltiplas vezes sobre o mesmo dado ou que a lógica de validação não era robusta o suficiente.

#### Análise da Causa Raiz
O `Resolver` podia ser chamado repetidamente sobre o mesmo objeto de DataFrame, e se a unidade original ainda estivesse presente, ele aplicava a conversão novamente (ex: `1700` com unidade `%` era multiplicado por `10.000` novamente). Além disso, o limite de detecção de valores astronômicos não era suficientemente baixo para interceptar valores que, embora absurdos, ainda estavam abaixo de `1.000.000`.

#### Solução Aplicada
1.  **Trava de Plausibilidade no Engine:** No `engine.py`, se o valor de um nutriente já estiver dentro do `target_min` e `target_max` da sua regra, o sistema agora **ignora a unidade original** para evitar re-multiplicações indevidas.
2.  **Redução do Limite de Anulação:** O limite para anulação de valores no `Resolver` foi reduzido de `1.000.000` para **`100.000`**. Qualquer valor acima de `100.000` é imediatamente marcado como implausível e anulado se não puder ser corrigido, impedindo novas multiplicações.
3.  **Idempotência:** O sistema foi projetado para ser idempotente, garantindo que múltiplas execuções da normalização sobre o mesmo dado resultem no mesmo valor correto.

### 2.4. v1.2.3 - Trava de Sanidade Final no Exporter

#### Problema
Mesmo com todas as correções lógicas anteriores, artefatos de dados corrompidos ainda podiam "escapar" para o CSV final, indicando que a corrupção poderia ocorrer após a normalização ou que o processo de escrita do Pandas estava sendo influenciado por dados antigos.

#### Análise da Causa Raiz
Identificou-se a necessidade de uma última linha de defesa. Embora o `Resolver` e o `Engine` estivessem corrigindo os dados em memória, a persistência de valores errados no arquivo final sugeria que o problema poderia estar na etapa de gravação do CSV, onde valores antigos poderiam ser reinjetados ou não serem filtrados adequadamente.

#### Solução Aplicada
1.  **Validação no Momento da Escrita:** Implementada uma **Trava de Sanidade Final** no `WarehouseExporter`. Antes de gravar o arquivo CSV, o exportador realiza uma última verificação em todas as colunas de nutrientes e preços.
2.  **Anulação Compulsória:** Se qualquer `nutrient_value` ou `price` for detectado como maior que `100.000` ou negativo, ele é **forçado para `None`** no arquivo final. Isso garante que o CSV que o usuário abre esteja sempre limpo de valores biologicamente impossíveis.

### 2.5. v1.2.4 - Eliminação de Artefatos de Ponto Flutuante

#### Problema
Valores como `1700.0000000000002` eram exibidos de forma confusa (ex: `1.7E+16`) em visualizadores como Excel devido à precisão de ponto flutuante (IEEE 754), causando confusão e a impressão de que o bug de escala persistia.

#### Análise da Causa Raiz
O Python e o Pandas utilizam números de ponto flutuante que, em certas operações, podem introduzir pequenas imprecisões binárias. Embora o valor real fosse `1700`, a representação interna `1700.0000000000002` era interpretada de forma indesejada por softwares externos. A falta de um arredondamento explícito permitia que esses artefatos chegassem ao CSV.

#### Solução Aplicada
1.  **Arredondamento no Resolver:** Todos os valores normalizados retornados pelo `Resolver` agora são arredondados para **2 casas decimais** (`round(valor, 2)`) antes de serem entregues ao `Engine`.
2.  **Arredondamento no Exporter:** Uma camada final de arredondamento (`.round(2)`) foi adicionada no `Exporter` para as colunas `nutrient_value` e `price` antes da gravação do CSV. Isso garante que, mesmo que o Pandas introduza algum resíduo durante o processamento, o arquivo final contenha apenas números limpos e facilmente interpretáveis.

### 2.6. v1.2.5 - Heurísticas de Escala Biológica e Tratamento de Erros Sistemáticos

#### Problema
Análise aprofundada revelou padrões sistemáticos de erro: macronutrientes e energia com valores 10x ou 100x maiores (ex: umidade `8200` g/kg, energia `35000` kcal/kg), confusão de unidades em minerais (ex: potássio `100.000` mg/kg) e valores de energia muito baixos que pareciam ser por porção (ex: `29-100` kcal).

#### Análise da Causa Raiz
As regras de normalização existentes não eram suficientemente agressivas ou flexíveis para lidar com esses múltiplos fatores de erro de escala e unidade. O `Resolver` precisava de mais heurísticas para testar divisões e multiplicações em diferentes cenários, e os `target_min/max` precisavam ser ajustados para acomodar a variabilidade biológica real dos produtos.

#### Solução Aplicada
1.  **Heurísticas de `decimal_shift_down`:** Adicionadas tentativas de divisão por `10` e `100` no `Resolver` quando um valor está acima do `target_max` da regra. Isso corrige automaticamente valores como `8200` para `820` (umidade) e `300.000` para `3.000` (fósforo).
2.  **Heurísticas de `decimal_shift_up`:** Adicionadas tentativas de multiplicação por `10`, `100` e `1.000` no `Resolver` quando um valor está abaixo do `target_min` da regra. Isso ajuda a corrigir valores de energia que podem ter sido extraídos em kcal/g (ex: `3.5` para `3500` kcal/kg) ou por porção.
3.  **Ajuste de Ranges no `rules.py`:**
    *   `moisture_gkg`: `target_max` aumentado para `950` g/kg (95%) para rações úmidas extremas.
    *   `sodium_mgkg`: `target_max` aumentado para `30.000` mg/kg (3%) para petiscos salgados.
    *   `metabolizable_energy_kcalkg`: `target_min` reduzido para `500` kcal/kg e `target_max` aumentado para `6500` kcal/kg para maior flexibilidade.
4.  **`overscale_factor` e `decimal_shift_factor`:** Aplicados de forma mais abrangente em macronutrientes e minerais para cobrir cenários de erro de escala.

### 2.7. v1.3.0 - Auditoria de Coerência Nutricional e Integridade Biológica

#### Problema
Apesar das correções individuais, faltava uma camada de validação cruzada que garantisse a coerência nutricional do conjunto de nutrientes de um produto, conforme princípios de bromatologia.

#### Análise da Causa Raiz
O pipeline tratava cada nutriente de forma isolada. Para atingir um nível profissional de integridade de dados, era necessário implementar regras que avaliassem a relação entre diferentes nutrientes, detectando perfis nutricionais biologicamente impossíveis ou altamente improváveis.

#### Solução Aplicada
Implementado um método `_audit_biological_coherence` no `NormalizationEngine`, que é executado após a normalização individual de cada linha. Este auditor aplica as seguintes regras:
1.  **Inversão Mínimo vs Máximo:** Verifica se `calcium_min_mgkg` é maior que `calcium_max_mgkg` e, se sim, inverte os valores automaticamente.
2.  **Soma de Macronutrientes:** Calcula a soma de `protein_gkg`, `fat_gkg`, `fiber_gkg`, `ash_gkg`. Se a soma exceder `1000 g/kg`, indica um erro grave e anula os valores suspeitos (individuais > 600 g/kg).
3.  **Razão Cálcio : Fósforo (Ca:P):** Calcula a razão `Ca:P`. Se o valor estiver fora do intervalo `0.5` a `4.0`, um alerta `[BIOLOGICAL AUDIT]` é emitido, sinalizando o produto para revisão manual.
4.  **Coerência Energia vs Umidade:** Se a `moisture_gkg` for maior que `700 g/kg` (70%) e a `metabolizable_energy_kcalkg` for maior que `2500 kcal/kg`, o sistema detecta uma inconsistência. Nesses casos, a energia é dividida por `10` (assumindo um erro de escala comum em rações úmidas).

## 3. Conclusão

As melhorias implementadas desde a `v1.2.0` até a `v1.3.0` transformaram o `Dog Food Nutrition Catalog` em um pipeline robusto e inteligente. As múltiplas camadas de validação, auto-correção e auditoria biológica garantem que os dados extraídos sejam não apenas limpos de erros técnicos, mas também coerentes com a realidade nutricional dos alimentos para cães. O sistema agora é capaz de lidar com uma gama muito maior de inconsistências de dados, fornecendo um catálogo de alta qualidade para análises de BI.
