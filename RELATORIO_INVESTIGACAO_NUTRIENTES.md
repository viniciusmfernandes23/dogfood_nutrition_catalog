# Relatório de Investigação: Baixa Cobertura de Fibra e Cálcio

Este documento detalha a investigação e as correções aplicadas para resolver a baixa cobertura dos nutrientes **Fibra** e **Cálcio** no pipeline do Dogfood Nutrition Catalog.

## 1. Diagnóstico dos Problemas Identificados

A investigação confirmou que a perda de dados ocorria em três frentes principais:

| Componente | Problema Identificado | Impacto |
| :--- | :--- | :--- |
| **Mapeamento (aliases.py)** | Ausência de variações comuns como "Fibra", "Cálcio" e "Cálcio (mín)" nos dicionários de busca. | O parser falhava em extrair os valores mesmo quando presentes no texto bruto. |
| **Resolução (resolver.py)** | A regra `decimal_shift_factor` definida em `rules.py` não estava sendo aplicada pelo motor de resolução. | Valores como "Cálcio 1.5" (que deveria ser 1500mg/kg) eram classificados como implausíveis. |
| **Auditoria (engine.py)** | A lógica de auditoria biológica causava `KeyError` quando colunas de minerais estavam ausentes e possuía uma falha na lógica de Razão Ca:P. | O pipeline quebrava ou anulava nutrientes indevidamente por erros de referência. |

## 2. Correções Aplicadas

### 2.1. Expansão de Aliases
Foram adicionados novos termos de busca para garantir que o parser capture variações frequentes em rótulos brasileiros:
- **Fibra:** Adicionado "fibra".
- **Cálcio:** Adicionados "cálcio", "calcio", "cálcio (mín)", "calcio (min)", "cálcio (máx)" e "calcio (max)".

### 2.2. Ativação do Decimal Shift
O `NormalizationResolver` foi atualizado para incluir o `decimal_shift` como um candidato válido de normalização. Isso permite converter automaticamente valores em escalas decimais (ex: 1.5 -> 1500) com base nos fatores configurados em `rules.py`.

### 2.3. Robustez na Auditoria Biológica
- **Prevenção de KeyError:** A engine agora garante a existência das colunas canônicas antes de iniciar a auditoria.
- **Correção da Razão Ca:P:** Ajustada a lógica de seleção do valor de cálcio (`min` ou `max`) para o cálculo da razão, evitando falhas quando apenas um dos campos está preenchido.
- **Ajuste de Tolerância:** Aumentada a tolerância da soma de macronutrientes para 1100 g/kg (10%), acomodando imprecisões comuns em rótulos comerciais.

## 3. Resultados dos Testes de Reprodução

Após as correções, os casos de teste demonstraram a recuperação dos dados:

- **Fibra:** Agora extraída corretamente de termos simples como "Fibra 3.5%".
- **Cálcio:** Recuperado com sucesso tanto de "Cálcio 1.5%" (via `unit_direct`) quanto de variações com parênteses.
- **Estabilidade:** O pipeline não apresenta mais erros de execução por colunas ausentes.

## 4. Recomendações
Recomenda-se uma execução completa do pipeline (`full mode`) para validar o aumento da cobertura no dataset real, que deve agora refletir a realidade do mercado de forma muito mais precisa.
