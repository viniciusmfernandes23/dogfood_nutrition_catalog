# Esquema de Dados e Convenções Nutricionais (v1.4.0)

Este documento define formalmente as unidades de armazenamento, tipos de dados e regras de integridade biológica aplicadas no `Dogfood Nutrition Catalog`.

## 1. Unidades de Armazenamento (Target Units)

Para garantir a comparabilidade entre produtos, todos os nutrientes são normalizados para as seguintes unidades padrão:

| Categoria | Unidade | Descrição |
|---|---|---|
| **Macronutrientes** | `g/kg` | Gramas por Quilograma (ex: 26% vira 260 g/kg) |
| **Minerais** | `mg/kg` | Miligramas por Quilograma (ex: 0.17% vira 1700 mg/kg) |
| **Energia** | `kcal/kg` | Quilocalorias por Quilograma (ex: 3.5 kcal/g vira 3500 kcal/kg) |
| **Preços** | `BRL` | Reais Brasileiros (arredondado para 2 casas decimais) |

## 2. Dicionário de Colunas (`fact_nutrient.csv`)

| Coluna | Unidade | Range Biológico Esperado |
|---|---|---|
| `moisture_gkg` | g/kg | 50 - 950 |
| `protein_gkg` | g/kg | 150 - 600 |
| `fat_gkg` | g/kg | 50 - 300 |
| `fiber_gkg` | g/kg | 10 - 150 |
| `ash_gkg` | g/kg | 30 - 150 |
| `calcium_min_mgkg` | mg/kg | 5000 - 30000 |
| `calcium_max_mgkg` | mg/kg | 8000 - 45000 |
| `phosphorus_mgkg` | mg/kg | 4000 - 25000 |
| `sodium_mgkg` | mg/kg | 1000 - 30000 |
| `potassium_mgkg` | mg/kg | 3000 - 20000 |
| `metabolizable_energy_kcalkg` | kcal/kg | 700 - 6000 |

## 3. Regras de Integridade Biológica (Barreira de Sanidade)

O pipeline aplica as seguintes validações cruzadas antes da exportação final. Valores que violam estas regras são **ANULADOS** para garantir a confiabilidade do catálogo.

1.  **Limite Superior para Nutrientes:** Nenhum nutriente individual pode exceder 1000 g/kg (100% da matéria seca).
2.  **Soma de Macros:** `Umidade + Proteína + Gordura + Fibra + Cinzas` deve ser ≤ `1050 g/kg` (tolerância de 5% para erros de arredondamento de rótulos).
3.  **Âncora de Umidade:** Se `Umidade > 700 g/kg`, a `Energia` deve ser ≤ `1500 kcal/kg`.
4.  **Limite Físico de Energia:** Nenhum valor de energia pode exceder `9000 kcal/kg` (densidade energética da gordura pura).
5.  **Coerência Cinzas vs. Minerais:** A soma dos minerais (em g/kg) não deve exceder o teor de cinzas (em g/kg).
6.  **Razão Ca:P:** A proporção entre Cálcio e Fósforo deve situar-se entre `1:1` e `2:1` (com tolerância técnica para anulação de 0.4:1 a 5.0:1).
7.  **Trava de Toxicidade:** Minerais (Sódio/Potássio) acima de `60.000 mg/kg` (6%) são considerados erros de escala e anulados.

## 4. Rastreabilidade e Auditoria

Todas as transformações são logadas no terminal com as seguintes tags:
*   `[AUDIT]`: Indica uma correção de escala ou normalização bem-sucedida.
*   `[BIOLOGICAL AUDIT]`: Indica uma inconsistência detectada entre nutrientes.
*   `[FINAL SANITY BARRIER]`: Indica a anulação de um valor impossível no momento da exportação.

## 5. NormalizationLog Dataclass

O `NormalizationLog` registra cada alteração aplicada aos dados. A partir da v1.4.0, inclui um `confidence_score`:

```python
@dataclass(slots=True)
class NormalizationLog:
    product_id: int
    field: str
    original_value: float | None
    normalized_value: float | None
    rule_applied: str | None
    status: ValidationStatus
    confidence_score: float = 1.0
```

## 6. Próximos Passos (v1.4.0)

*   **Verificação do problema "Phosphorus 300,000":** Garantir que `overscale_factor` ou `decimal_shift` no `resolver.py` ou a barreira de sanidade no `exporter.py` anulem ou corrijam valores de fósforo excessivamente altos.
*   **Arredondamento:** Todos os valores numéricos são arredondados para 2 casas decimais para mitigar artefatos de ponto flutuante.
*   **Timestamps Consistentes:** Todos os timestamps são armazenados em horário local (sem UTC).
