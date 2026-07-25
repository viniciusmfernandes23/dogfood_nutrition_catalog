
import pandas as pd
from app.warehouse.dim_product import ProductDimensionBuilder
from app.normalization.resolver import Resolver
from app.normalization.rules import get_rule

def test_line_break_sanitization():
    builder = ProductDimensionBuilder()
    
    # Caso: Indicação com quebra de linha
    data = [
        {
            "product_id": "3965340",
            "product_name": "Ração Teste",
            "indication": "Linha 1\nLinha 2\rLinha 3\tTab",
            "protein_gkg": 250.0
        }
    ]
    df = pd.DataFrame(data)
    dim_df = builder.build(df)
    
    # A indicação deve estar em uma única linha
    cleaned_indication = dim_df.loc[0, "indication"]
    assert "\n" not in cleaned_indication
    assert "\r" not in cleaned_indication
    assert "\t" not in cleaned_indication
    assert "Linha 1 Linha 2 Linha 3 Tab" in cleaned_indication

def test_energy_scale_correction_100x():
    resolver = Resolver()
    rule = get_rule("metabolizable_energy_kcalkg")
    
    # CORREÇÃO DO BUG: fix_energy_scale_100x era uma dupla normalização.
    # 105515 kcal/kg com unidade explícita kcal/kg -> 105515 > 9000 -> IMPLAUSIBLE.
    # Não deve ser dividido por 100 pois a unidade já foi convertida deterministicamente.
    from app.normalization.models import NormalizedNutrient
    nutrient = NormalizedNutrient(
        name="metabolizable_energy_kcalkg",
        value=105515.0,
        unit="kcal/kg",
        original_unit="kcal/kg"
    )
    
    resolved = resolver.resolve(nutrient, rule)
    assert resolved.value is None
    assert resolved.status == "biologically_implausible_energy"

def test_mineral_zero_implausibility():
    resolver = Resolver()
    rule = get_rule("chlorine_mgkg")
    
    # Caso: Cloro = 0 mg/kg -> deve ser implausível (anulado)
    from app.normalization.models import NormalizedNutrient
    nutrient = NormalizedNutrient(
        name="chlorine_mgkg",
        value=0.0,
        unit="mg/kg",
        original_unit="mg/kg"
    )
    
    resolved = resolver.resolve(nutrient, rule)
    assert resolved.value is None
    assert resolved.status == "implausible"
    assert resolved.rule_applied == "nullified_zero_value"

if __name__ == "__main__":
    print("Iniciando testes de refinamento v1.5.4...")
    test_line_break_sanitization()
    print("  - Sanitização de quebras de linha: OK")
    test_energy_scale_correction_100x()
    print("  - Correção de escala de energia (100x): OK")
    test_mineral_zero_implausibility()
    print("  - Anulação de minerais zero: OK")
    print("\nTodos os testes de refinamento v1.5.4 passaram!")
