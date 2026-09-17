"""
Validação ponta a ponta do pipeline de normalização.
Verifica que o bug de multiplicação ×10 está corrigido em todos os estágios.
"""
import sys
import os

# Ajusta path para permitir importação do pacote `app` a partir da raiz do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from app.parsers.nutrition_parser import parse_nutrition, parse_value, clean_numeric_value
from app.parsers.html_parser import extract_guarantee_section
from app.normalization.resolver import Resolver
from app.normalization.rules import get_rule
from app.normalization.engine import NormalizationEngine

PASS = "✅"
FAIL = "❌"
errors = []

def check(label, actual, expected, tolerance=0.01):
    ok = abs(actual - expected) <= tolerance if actual is not None else False
    status = PASS if ok else FAIL
    print(f"  {status} {label}: esperado={expected}, obtido={actual}")
    if not ok:
        errors.append(f"{label}: esperado={expected}, obtido={actual}")
    return ok


print("\n" + "="*60)
print("ETAPA 1: Parser — clean_numeric_value")
print("="*60)
cases = [
    ("7,5",     7.5),
    ("26,0",    26.0),
    ("0,6",     0.6),
    ("4.052",   4052.0),
    ("3.700",   3700.0),
    ("1.055,15", 1055.15),
    ("75",      75.0),
    ("7.5",     7.5),
]
for raw, expected in cases:
    result = clean_numeric_value(raw)
    check(f"clean_numeric_value('{raw}')", result, expected)


print("\n" + "="*60)
print("ETAPA 2: Parser — parse_value (função restaurada)")
print("="*60)
pv_cases = [
    ("Proteína Bruta 26%",   ["proteína bruta"],  26.0,  "%"),
    ("Extrato Etéreo 15%",   ["extrato etéreo"],  15.0,  "%"),
    ("Fibra Bruta 3,5%",     ["fibra bruta"],     3.5,   "%"),
    ("Energia 4.052 kcal/kg",["energia"],         4052.0,"kcal/kg"),
]
for text, aliases, exp_val, exp_unit in pv_cases:
    val, unit, alias = parse_value(text.lower(), aliases)
    check(f"parse_value('{text}')", val, exp_val)
    ok_unit = unit == exp_unit
    print(f"  {'✅' if ok_unit else '❌'} unidade: esperado='{exp_unit}', obtido='{unit}'")
    if not ok_unit:
        errors.append(f"parse_value unit '{text}': esperado='{exp_unit}', obtido='{unit}'")


print("\n" + "="*60)
print("ETAPA 3: Parser — HTML com decimais fragmentados")
print("="*60)
html_cases = [
    ("<p>Níveis de Garantia</p><table><tr><td>Proteína Bruta</td><td>7</td><td>,5%</td></tr></table>",
     "protein", 7.5, "%"),
    ("<p>Níveis de Garantia</p><table><tr><td>Energia Metabolizável</td><td>4</td><td>.052 kcal/kg</td></tr></table>",
     "metabolizable_energy", 4052.0, "kcal/kg"),
]
for html, nutrient_key, exp_val, exp_unit in html_cases:
    text = extract_guarantee_section(html)
    if text:
        result = parse_nutrition(text)
        found = next((v for v in result.values() if v["nutrient"] == nutrient_key), None)
        if found:
            check(f"HTML fragmentado '{nutrient_key}'", found["value"], exp_val)
        else:
            print(f"  {FAIL} HTML fragmentado '{nutrient_key}': nutriente não encontrado no texto='{text}'")
            errors.append(f"HTML fragmentado '{nutrient_key}': não encontrado")
    else:
        print(f"  ⚠️  HTML sem seção de garantia detectada para '{nutrient_key}'")


print("\n" + "="*60)
print("ETAPA 4: Resolver — Conversões de unidade (sem dupla normalização)")
print("="*60)
resolver = Resolver()
resolver_cases = [
    # (field, value, original_unit, expected_normalized)
    ("protein_gkg",                    7.5,    "%",        75.0),
    ("protein_gkg",                    26.0,   "%",        260.0),
    ("phosphorus_mgkg",                0.6,    "%",        6000.0),
    ("metabolizable_energy_kcalkg",    4052.0, "kcal/kg",  4052.0),
    ("metabolizable_energy_kcalkg",    350.0,  "kcal/100g",3500.0),
    ("calcium_min_mgkg",               1.2,    "%",        12000.0),
]
for field, value, unit, expected in resolver_cases:
    rule = get_rule(field)
    result = resolver.resolve_value(value=value, rule=rule, original_unit=unit)
    check(f"Resolver {field} ({value} {unit})", result.normalized_value, expected)


print("\n" + "="*60)
print("ETAPA 5: NormalizationEngine — Pipeline completo")
print("="*60)
engine = NormalizationEngine()
df = pd.DataFrame([{
    "product_id": 1,
    "product_name": "Ração Teste",
    "product_category": "ração seca",
    "protein_gkg": 26.0,
    "protein_gkg_unit": "%",
    "fat_gkg": 15.0,
    "fat_gkg_unit": "%",
    "fiber_gkg": 3.5,
    "fiber_gkg_unit": "%",
    "ash_gkg": 7.5,
    "ash_gkg_unit": "%",
    "moisture_gkg": 10.0,
    "moisture_gkg_unit": "%",
    "metabolizable_energy_kcalkg": 4052.0,
    "metabolizable_energy_kcalkg_unit": "kcal/kg",
    "phosphorus_mgkg": 0.6,
    "phosphorus_mgkg_unit": "%",
}])

normalized_df, report = engine.normalize_dataframe(df)

engine_cases = [
    ("protein_gkg",                  260.0),
    ("fat_gkg",                      150.0),
    ("fiber_gkg",                    35.0),
    ("ash_gkg",                      75.0),
    ("moisture_gkg",                 100.0),
    ("metabolizable_energy_kcalkg",  4052.0),
    ("phosphorus_mgkg",              6000.0),
]
for field, expected in engine_cases:
    actual = normalized_df.iloc[0][field]
    check(f"Engine {field}", actual, expected)


print("\n" + "="*60)
print("RESUMO")
print("="*60)
if errors:
    print(f"\n{FAIL} {len(errors)} falha(s) encontrada(s):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print(f"\n{PASS} Todas as verificações passaram! Pipeline sem fator ×10.")
    sys.exit(0)
