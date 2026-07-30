# Análise das causas de impacto na coleta de preços da Petlove e Petz

## Resumo executivo

A interrupção na coleta de preços não está no warehouse nem na exportação. O gargalo principal está na fase de ingestão de dados, onde as fontes Petlove e Petz dependem de mecanismos mais frágeis do que a Cobasi.

## Conclusões verificadas com testes diretos

Após executar os coletores de forma isolada, os resultados foram os seguintes:

- Petlove: a busca da Petlove para o termo "ração cachorro premium" retornou HTTP 403 Forbidden no primeiro acesso à URL de busca. O coletor registrou bloqueio e não retornou nenhum produto, portanto não há preço disponível para extração nesta execução.
- Petz: a busca da Petz retornou HTTP 200 OK, mas o conteúdo da página foi identificado como bloqueio/captcha/bot pelo parser. Como não foram encontrados produtos no HTML/JSON, também não houve preço disponível para extração.
- Ponto exato de bloqueio:
  - Petlove: na camada de acesso à URL de busca, antes do parsing.
  - Petz: na camada de conteúdo/HTML retornado, após a requisição inicial, antes da extração de produtos.

Essas conclusões são compatíveis com a análise de código e com os logs observados durante a execução do pipeline.

## Lista de prioridade das causas raiz

### Prioridade 1 — Petlove depende de scraping frágil e é sensível a bloqueios externos

**Causa raiz**
- O coletor da Petlove usa scraping sobre páginas públicas e extração de dados a partir de HTML/JSON embutido.
- O código identifica explicitamente falhas como `403` e bloqueios de anti-bot.

**Por que isso impacta**
- Se a página não responde como esperado, o fluxo não encontra os produtos e, consequentemente, não gera variações de SKU com preço.
- A lógica de extração depende da estrutura do HTML/JSON (`__NEXT_DATA__` e estrutura de `products`). Qualquer mudança nessa estrutura reduz a coleta.

**Evidência no código**
- [app/collectors/petlove_crawler.py](app/collectors/petlove_crawler.py)
- [app/services/collector_factory.py](app/services/collector_factory.py)

**Impacto**
- Alto. Essa é a causa mais relevante para a Petlove.

### Prioridade 2 — Petz não está realmente operacional no fluxo principal

**Causa raiz**
- O coletor da Petz está implementado como uma tentativa experimental, não como uma integração madura ao pipeline.
- O fluxo principal registra um aviso e retorna lista vazia para esse marketplace.

**Por que isso impacta**
- Sem produtos coletados, não há como gerar preços, EAN, SKU e snapshots para a Petz.

**Evidência no código**
- [app/services/collector_factory.py](app/services/collector_factory.py)
- [config/config.yaml](config/config.yaml)

**Impacto**
- Alto para Petz. É a causa principal do problema nessa fonte.

### Prioridade 3 — A configuração atual da Petz não fornece uma fonte operacional de busca

**Causa raiz**
- No arquivo de configuração, o endpoint da Petz está vazio e as queries padrão também estão vazias.

**Por que isso impacta**
- Sem endpoint e sem queries, o coletor não tem como localizar produtos para extração de preço.

**Evidência no código**
- [config/config.yaml](config/config.yaml)

**Impacto**
- Médio/alto, porque bloqueia o coletor antes mesmo de ele tentar extrair dados.

### Prioridade 4 — O enriquecimento do produto depende de variações válidas de SKU para montar preço

**Causa raiz**
- O serviço de enriquecimento só gera os campos de preço se o coletor conseguir retornar variações de SKU válidas.

**Por que isso impacta**
- Mesmo que o produto seja encontrado, se o payload não contiver as estruturas esperadas, o preço não é materializado no DataFrame e, depois, não chega ao warehouse.

**Evidência no código**
- [app/services/product_enrichment.py](app/services/product_enrichment.py)

**Impacto**
- Médio. É um efeito colateral da falha de ingestão anterior.

## Ordem de prioridade recomendada

1. Petlove — fragilidade de scraping e bloqueios externos.
2. Petz — integração incompleta e fluxo principal não alimentando essa fonte.
3. Configuração da Petz — endpoint/queries ausentes.
4. Enriquecimento de preços — depende diretamente da estrutura retornada pelos coletores.

## Sugestões para ativar a coleta de preços da Petz e Petlove

### Para a Petlove

1. Melhorar a fonte de entrada
- Usar um canal de dados mais estável do que scraping direto de HTML, como API pública, feed parceiro ou uma porta de acesso autorizada.
- Se o scraping continuar sendo necessário, validar o endpoint de busca e a estrutura do JSON antes de cada execução.

2. Reduzir o impacto de bloqueios
- Rodar o pipeline a partir de um ambiente com IP residencial ou com rede menos restritiva.
- Adotar rotação de User-Agent e backoff para tentativas repetidas.
- Fazer coleta em horários menos sensíveis a filtros anti-bot.

3. Fortalecer a robustez do parser
- Garantir que o parser reconheça múltiplas estruturas de resposta da Petlove, não apenas uma única versão do `__NEXT_DATA__`.
- Incluir fallback para diferentes caminhos de JSON quando a estrutura principal não estiver disponível.

### Para a Petz

1. Ativar uma fonte operacional de busca
- Definir endpoint e queries válidos no arquivo de configuração para permitir que o coletor encontre produtos.
- Priorizar categorias de interesse, como ração para cachorro, para aumentar a cobertura.

2. Completar a integração no fluxo principal
- Garantir que a Petz seja tratada como marketplace ativo e não apenas como coleta experimental.
- Validar se o coletor consegue entregar produtos e preços no mesmo formato esperado pelos demais módulos.

3. Criar uma estratégia de fallback
- Se a busca por páginas não funcionar, usar uma lista curada de URLs ou produtos conhecidos como entrada para o fluxo.
- Aumentar a chance de sucesso com páginas de categoria específicas, em vez de depender apenas de buscas gerais.

### Ações de curto prazo

- Priorizar a Petlove para estabilizar a ingestão de preços por scraping robusto.
- Definir uma configuração mínima válida para a Petz, mesmo que seja um fluxo inicial e limitado.
- Validar a disponibilidade de produtos e preços com amostras pequenas antes de expandir para todo o catálogo.

### Ações de médio prazo

- Avaliar se a Petz pode ser integrada via feed, API ou parceria comercial.
- Criar uma camada de normalização de resposta para padronizar os dados de diferentes marketplaces.
- Adotar uma estratégia de observabilidade para registrar quando a coleta falha por bloqueio, estrutura inesperada ou ausência de dados.

## Conclusão

Para reativar a coleta de preços da Petlove e da Petz, as principais alavancas são:
- reduzir a dependência de scraping frágil na Petlove;
- tornar a Petz uma fonte ativa e configurada no pipeline;
- garantir fallback e validação de estrutura para não depender de uma única forma de resposta.
