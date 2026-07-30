# Relatório técnico atualizado: regras de normalização e auditoria nutricional

## Observação inicial

O relatório anterior estava parcialmente alinhado com o domínio do projeto, mas não refletia de forma fiel a estrutura atual do motor de normalização implementado em [app/normalization/engine.py](app/normalization/engine.py), [app/normalization/resolver.py](app/normalization/resolver.py), [app/normalization/rules.py](app/normalization/rules.py), [app/normalization/validator.py](app/normalization/validator.py) e [app/normalization/models.py](app/normalization/models.py).

Este documento apresenta uma versão revisada, coerente com a implementação vigente.

---

## 1. Estrutura atual do módulo de normalização

A camada de normalização está organizada em módulos distintos:

- [app/normalization/engine.py](app/normalization/engine.py): orquestra a normalização de todo o DataFrame e executa auditorias biológicas cruzadas.
- [app/normalization/resolver.py](app/normalization/resolver.py): aplica conversões de unidade, validação inicial e heurísticas de correção quando necessário.
- [app/normalization/validator.py](app/normalization/validator.py): valida plausibilidade dos valores contra faixas biológicas definidas.
- [app/normalization/rules.py](app/normalization/rules.py): concentra as regras por nutriente, incluindo faixas alvo e fatores de conversão.
- [app/normalization/models.py](app/normalization/models.py): define os status, regras e resultados usados durante o processamento.
- [app/normalization/semantic.py](app/normalization/semantic.py): é uma camada semântica de saída, não o ponto central da normalização.

---

## 2. Fluxo real de normalização

O fluxo atual funciona da seguinte forma:

1. O motor principal lê cada coluna nutricional presente no DataFrame.
2. Para cada campo, o resolver identifica a unidade original a partir das colunas de unidade associadas.
3. A conversão é aplicada para a unidade alvo canônica do nutriente.
4. A validação verifica se o valor está dentro da faixa biológica esperada.
5. Se o valor não for plausível, o sistema pode aplicar heurísticas de correção ou anular o valor.
6. Após a normalização individual, o motor executa auditorias cruzadas de coerência biológica.

---

## 3. Regras ativas atualmente implementadas

### 3.1 Energia metabolizável

- Unidade alvo: `kcal/kg`
- Faixa biológica aceita: `500` a `9000`
- Conversões implementadas:
  - `kcal/100g` → `kcal/kg` multiplicando por `10`
  - `MJ/kg` → `kcal/kg` multiplicando por `239.006`
  - `kcal/sache` → `kcal/kg` usando a base de `85g` por sachê
- Se o valor convertido estiver fora da faixa biológica, ele é considerado implausível e é anulado.

### 3.2 Macronutrientes

- Unidades alvo: `g/kg`
- Campos principais: `protein_gkg`, `fat_gkg`, `fiber_gkg`, `ash_gkg`, `moisture_gkg`
- Conversões implementadas:
  - `%` → `g/kg` multiplicando por `10`
  - `mg/kg` → `g/kg` dividindo por `1000`
- Faixas alvo definidas por regra, com valores que variam por nutriente.

### 3.3 Minerais e elementos semelhantes

- Unidade alvo: `mg/kg`
- Conversões implementadas:
  - `%` → `mg/kg` multiplicando por `10000`
  - `g/kg` → `mg/kg` multiplicando por `1000`
  - `mcg` → `mg/kg` multiplicando por `0.001`
  - `ppm` → `mg/kg` diretamente

### 3.4 Vitaminas e micronutrientes

- Alguns micronutrientes usam unidade alvo `mg/kg` e outros `UI/kg`.
- A regra é definida individualmente por nutriente em [app/normalization/rules.py](app/normalization/rules.py).

---

## 4. Auditorias biológicas cruzadas atuais

### 4.1 Balanço de massa

A validação de balanço de massa é feita no motor de normalização após os campos individuais serem processados.

- Se a soma dos macronutrientes principais estiver entre `600` e `1050 g/kg`, o status é considerado `normalized`.
- Se estiver entre `500` e `600` ou entre `1050` e `1100`, o registro entra em revisão (`review`).
- Se estiver abaixo de `500` ou acima de `1100`, o sistema marca falha de balanço e anula os campos afetados.

### 4.2 Razão cálcio:fósforo

- A relação entre `calcium_min_mgkg`/`calcium_max_mgkg` e `phosphorus_mgkg` é avaliada.
- Se a razão ficar fora do intervalo `1.0` a `2.0`, os valores são anulados e o registro recebe status específico de invalidade.

### 4.3 Limites biológicos para microminerais

- O motor aplica limites específicos para minerais como sódio, potássio, magnésio, zinco, cobre, selênio, iodo e manganês.
- Para petiscos e suplementos, a regra aplica um multiplicador de `3.0` sobre o limite superior, conforme a lógica implementada no motor.

---

## 5. Heurísticas de correção automática

A correção automática continua existindo, mas hoje ela é aplicada com critérios mais restritos do que o texto antigo sugere.

- A lógica não tenta “corrigir” valores já convertidos duas vezes.
- O sistema gera candidatos de correção apenas quando o valor bruto está fora do intervalo plausível.
- Se houver um único candidato válido, ele é aceito como `auto_corrected`.
- Se houver múltiplos candidatos, o valor é marcado como `ambiguous`.
- Se nenhum candidato for plausível, o valor é anulado como `implausible`.

---

## 6. Diferenças importantes em relação ao relatório anterior

As principais divergências observadas foram:

1. O relatório anterior citava uma versão `v1.4.0`, enquanto o código atual já traz ajustes e comentários associados a versões posteriores, como `v1.5.4` e `v1.5.6`.
2. O texto antigo tratava a camada semântica como parte direta da normalização; na estrutura atual, a semântica de saída é tratada por [app/normalization/semantic.py](app/normalization/semantic.py), que é complementar, não o núcleo do processo.
3. O fluxo atual enfatiza a separação entre:
   - resolução de unidade;
   - validação de plausibilidade;
   - auditoria biológica cruzada.
4. A precedência da ficha técnica VTEX não aparece como regra central no código atual. O módulo de enriquecimento extrai especificações, mas a normalização não depende diretamente dessa precedência para decidir os valores finais.

---

## 7. Conclusão

O projeto atual possui um motor de normalização bem mais estruturado do que o texto anterior sugeria. O processo principal está concentrado em:

- conversão de unidade;
- validação por faixa biológica;
- auditoria cruzada de coerência;
- marcação de status explícitos para valores corrigidos, revisados ou anulados.

Por isso, a versão atualizada acima é a forma mais coerente de descrever o comportamento do pipeline em relação ao código efetivamente implementado.
