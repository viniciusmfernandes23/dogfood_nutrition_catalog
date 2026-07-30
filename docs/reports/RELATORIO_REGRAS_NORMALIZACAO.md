# Relatório Técnico: Regras de Normalização e Auditoria Nutricional (v2.1.0)

Este documento descreve a implementação atual do motor de normalização do projeto, baseada nos módulos de [app/normalization](app/normalization), com foco em conversão de unidades, validação biológica e rastreabilidade dos resultados.

---

## 1. Objetivo do motor de normalização

O motor de normalização transforma valores brutos coletados de marketplaces em valores padronizados, plausíveis e auditáveis. O fluxo atual é composto por três camadas principais:

1. **Resolver**: aplica conversão de unidade, heurísticas de escala e barreiras sanitárias iniciais.
2. **Validator**: verifica se o valor normalizado está dentro das faixas biológicas esperadas.
3. **NormalizationEngine**: orquestra a normalização por campo e aplica auditorias cruzadas entre nutrientes.

O pipeline preserva o valor original, o valor normalizado, a unidade, o status de validação e o motivo associado a cada campo.

---

## 2. Fluxo atual de normalização

O fluxo atual segue esta ordem:

1. Identifica a unidade original a partir da coluna correspondente do DataFrame.
2. Aplica conversão determinística quando a unidade é explícita.
3. Valida o valor resultante contra o intervalo biológico da regra.
4. Se o valor não for plausível, tenta heurísticas conservadoras de escala (como deslocamento decimal) apenas quando existe um único candidato plausível.
5. Se a informação permanecer ambígua ou implausível, o valor é marcado e, em muitos casos, anulado para preservar a qualidade do dado.
6. Em seguida, o motor aplica auditorias cruzadas de consistência biológica.

> Ponto importante: a implementação atual evita aplicar correção de escala sobre um valor já convertido por unidade. Isso evita dupla normalização e preserva rastreabilidade.

---

## 3. Regras por família de nutriente

### 3.1. Macronutrientes (alvo: g/kg)

| Nutriente | Faixa plausível | Observações |
| :--- | :--- | :--- |
| Proteína | 0,1 a 600 g/kg | Conversão de % para g/kg via fator 10 |
| Gordura | 0,01 a 1000 g/kg | Conversão de % para g/kg via fator 10 |
| Fibra | 5 a 1000 g/kg | Conversão de % para g/kg via fator 10 |
| Cinzas | 10 a 150 g/kg | Conversão de % para g/kg via fator 10 |
| Umidade | 60 a 1000 g/kg | Conversão de % para g/kg via fator 10 |

**Conversões aplicadas**:
- `%` → multiplicado por 10.
- `mg/kg` → dividido por 1000.

### 3.2. Minerais e elementos (alvo: mg/kg)

| Nutriente | Faixa plausível | Observações |
| :--- | :--- | :--- |
| Cálcio (mín/máx) | 100 a 100.000 mg/kg | Conversão de % e g/kg para mg/kg |
| Fósforo | 100 a 80.000 mg/kg | Conversão de % e g/kg para mg/kg |
| Sódio | 100 a 30.000 mg/kg | Conversão de % e g/kg para mg/kg |
| Potássio | 100 a 50.000 mg/kg | Conversão de % e g/kg para mg/kg |
| Magnésio | 10 a 5.000 mg/kg | Intervalo mais flexível para acomodar produtos de baixa densidade |
| Cloro | 500 a 20.000 mg/kg | Regras específicas aplicadas |
| Ferro | 10 a 1000 mg/kg | Regras específicas aplicadas |
| Zinco | 50 a 500 mg/kg | Regras específicas aplicadas |
| Cobre | 0,1 a 150 mg/kg | Regras específicas aplicadas |
| Selênio | 0,01 a 10 mg/kg | Regras específicas aplicadas |
| Iodo | 0,001 a 30 mg/kg | Regras específicas aplicadas |

**Conversões aplicadas**:
- `%` → multiplicado por 10.000.
- `g/kg` → multiplicado por 1000.
- `mcg` → multiplicado por 0,001.

### 3.3. Energia metabolizável (alvo: kcal/kg)

| Campo | Faixa plausível | Observações |
| :--- | :--- | :--- |
| Energia metabolizável | 500 a 9000 kcal/kg | Faixa conservadora para ração e alimentos completos |

**Conversões aplicadas**:
- `kcal/100g` → multiplicado por 10.
- `MJ/kg` → multiplicado por 239,006.
- `kcal/sache` → convertido com base em 85 g por sachê, conforme fórmula `(valor / 85) * 1000`.

---

## 4. Auditorias cruzadas e validações biológicas

### 4.1. Balanço de massa

A soma de macronutrientes principais é avaliada para verificar se o produto é biologicamente plausível.

Os campos considerados são:
- Proteína
- Gordura
- Fibra
- Cinzas
- Umidade

**Limites atuais**:
- **NORMALIZED**: entre 600 e 1050 g/kg.
- **REVIEW**: entre 500 e 600 g/kg ou entre 1050 e 1100 g/kg.
- **PRODUCT_MASS_BALANCE_FAILED**: abaixo de 500 g/kg ou acima de 1100 g/kg.

Quando o balanço de massa falha de forma crítica:
- os campos de macro envolvidos recebem status de falha;
- o valor de energia metabolizável também é anulado, pois a consistência calórica depende da precisão dos macros.

### 4.2. Razão Cálcio:Fósforo

A relação entre cálcio e fósforo é validada para produtos com ambos os campos presentes.

**Regra atual**:
- a razão ideal deve estar entre 1,0 e 2,0.

Se a razão estiver fora deste intervalo:
- os campos de cálcio e fósforo são marcados como inválidos;
- os valores são anulados para evitar propagação de informação inconsistente.

### 4.3. Limites para microminerais

Minerais como sódio, potássio, magnésio, zinco, cobre, selênio, iodo e manganês são avaliados contra faixas plausíveis.

**Flexibilização para petiscos e suplementos**:
- os limites máximos são multiplicados por 3,0 para acomodar produtos com composição nutricional específica.

---

## 5. Statuses e sinais de saída

A implementação atual registra os seguintes indicadores por campo:

- `*_original`: valor bruto coletado.
- `*_status`: status após validação e auditoria.
- `*_reason`: motivo da avaliação, quando aplicável.
- `*_rule`: regra aplicada na transformação.

### Statuses principais

- `NORMALIZED`: valor convertido e considerado plausível.
- `AUTO_CORRECTED`: valor ajustado por heurística conservadora.
- `REVIEW`: valor fora da faixa ideal, mas ainda passível de revisão humana.
- `AMBIGUOUS`: múltiplas hipóteses plausíveis foram encontradas e o sistema evita decidir.
- `IMPLAUSIBLE`: valor descartado por inconsistência ou implausibilidade.
- `PRODUCT_MASS_BALANCE_FAILED`: falha crítica no balanço de massa.

---

## 6. Heurísticas de correção automática

A implementação atual tenta corrigir valores inconsistentes apenas com critérios rigorosos:

1. **Deslocamento decimal**: tenta ajustar escalas como 10x ou 100x quando há uma única solução plausível.
2. **Troca implícita de unidade**: tenta converter o valor assumindo um erro de unidade quando a hipótese é única e plausível.
3. **Proteção contra dupla normalização**: não aplica correção de escala após uma conversão já realizada, evitando erros de interpretação.

Se não houver uma única hipótese plausível, o valor é marcado como ambíguo ou descartado.

---

## 7. Observações operacionais

- O motor de normalização é independente da fonte de coleta, mas depende de que os dados cheguem com estrutura mínima suficiente.
- A qualidade da normalização é diretamente afetada pela qualidade do dado bruto coletado.
- Os problemas atuais de coleta de Petlove/Petz afetam a cobertura do catálogo, mas não alteram a lógica de normalização já implementada.

---

## 8. Conclusão

A normalização atual do projeto é robusta para convergência de unidades, validação biológica, regras de plausibilidade e rastreabilidade. O motor foi desenhado para preservar integridade em vez de forçar correções indevidas, priorizando dado confiável e auditável em vez de preenchimento automático agressivo.

