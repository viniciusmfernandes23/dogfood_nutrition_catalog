
import pandas as pd
import numpy as np
from app.normalization.engine import NormalizationEngine
from app.normalization.models import ValidationStatus
from app.semantic.engine import SemanticEngine
from app.warehouse.dim_product import ProductDimensionBuilder

def test_metabolizable_energy_conversions():
    engine = NormalizationEngine()
    
    # CORREÇÃO DO BUG: fix_energy_scale era uma dupla normalização.
    # Após a correção, valores com unidade explícita que resultam em valores fora
    # do intervalo biológico são anulados, não "corrigidos" por heurística de escala.
    
    data = {
        "product_id": [1, 2, 3, 4],
        "metabolizable_energy_kcalkg": [13780.0, 105515.0, 3700.0, 477.0],
        "metabolizable_energy_unit": ["kcal/kg", "kcal/kg", "kcal/kg", "kcal/100g"]
    }
    df = pd.DataFrame(data)
    norm_df, _ = engine.normalize_dataframe(df)
    
    # 13780 kcal/kg -> 13780 > 9000 -> IMPLAUSIBLE (não mais fix_10x)
    assert pd.isna(norm_df.loc[0, "metabolizable_energy_kcalkg"])
    assert norm_df.loc[0, "metabolizable_energy_kcalkg_status"] == ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_ENERGY
    
    # 105515 kcal/kg -> 105515 > 9000 -> IMPLAUSIBLE (não mais fix_100x)
    assert pd.isna(norm_df.loc[1, "metabolizable_energy_kcalkg"])
    assert norm_df.loc[1, "metabolizable_energy_kcalkg_status"] == ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_ENERGY
    
    # 3700 kcal/kg -> 3700 (OK, dentro do intervalo 500-9000)
    assert norm_df.loc[2, "metabolizable_energy_kcalkg"] == 3700.0
    
    # 477 kcal/100g -> 4770 kcal/kg (conversão determinística, dentro do intervalo)
    assert norm_df.loc[3, "metabolizable_energy_kcalkg"] == 4770.0

def test_mass_balance_validation():
    engine = NormalizationEngine()
    
    # v2.0.0 (LIMITES RECALIBRADOS):
    # OK: 600–1050 g/kg (acomoda NFE/carboidratos não declarados)
    # REVIEW: 500–600 ou 1050–1100 g/kg
    # FAILED: < 500 ou > 1100 g/kg
    
    data = {
        "product_id": [1, 2, 3, 4, 5],
        "product_category": ["Ração Seca"] * 5,
        "protein_gkg": [300, 250, 400, 100, 500],
        "fat_gkg": [150, 100, 200, 100, 250],
        "fiber_gkg": [50, 50, 100, 50, 100],
        "ash_gkg": [100, 100, 100, 100, 100],
        "moisture_gkg": [300, 300, 300, 100, 300],
    }
    # Soma 1: 300+150+50+100+300 = 900 (OK: 600-1050)
    # Soma 2: 250+100+50+100+300 = 800 (OK: 600-1050)
    # Soma 3: 400+200+100+100+300 = 1100 (REVIEW: 1050-1100)
    # Soma 4: 100+100+50+100+100 = 450 (FAILED: < 500)
    # Soma 5: 500+250+100+100+300 = 1250 (FAILED: > 1100)
    
    df = pd.DataFrame(data)
    norm_df, _ = engine.normalize_dataframe(df)
    
    assert norm_df.loc[0, "protein_gkg_status"] == ValidationStatus.NORMALIZED
    assert norm_df.loc[1, "protein_gkg_status"] == ValidationStatus.NORMALIZED
    assert norm_df.loc[2, "protein_gkg_status"] == ValidationStatus.REVIEW
    assert norm_df.loc[3, "protein_gkg_status"] == ValidationStatus.PRODUCT_MASS_BALANCE_FAILED
    assert norm_df.loc[4, "protein_gkg_status"] == ValidationStatus.PRODUCT_MASS_BALANCE_FAILED

def test_scale_fix_and_ui():
    engine = NormalizationEngine()
    
    # v1.5.0: 
    # 1. Testar se UI/kg permanece UI/kg
    # 2. Testar correção de escala 10x não ambígua
    
    data = {
        "product_id": [1, 2],
        "vitamin_a_uikg": [10530.0, 50000.0],
        "vitamin_a_unit": ["ui/kg", "ui"],
        "ash_gkg": [1200.0, 50.0],
        "ash_unit": ["g/kg", "g/kg"]
    }
    df = pd.DataFrame(data)
    # Precisamos garantir que vitamin_a_uikg tenha uma regra
    from app.normalization.rules import NormalizationRule
    import app.normalization.rules as rules
    rules.NORMALIZATION_RULES["vitamin_a_uikg"] = NormalizationRule(
        field="vitamin_a_uikg", target_min=1000, target_max=100000
    )
    
    norm_df, _ = engine.normalize_dataframe(df)
    
    # UI deve permanecer
    assert norm_df.loc[0, "vitamin_a_uikg"] == 10530.0
    assert norm_df.loc[0, "vitamin_a_unit"] == "ui/kg"
    
    # Ash 1200 g/kg (max 150) -> deve ser corrigido para 120 g/kg se não for ambíguo
    # Nota: Em g/kg, o motor tenta dividir por 10, 100, 1000. 
    # 1200/10 = 120 (OK), 1200/100 = 12 (OK). Isso pode ser ambíguo.
    # Vamos testar um valor que só tenha UMA correção válida.
    # Ash target_min=10, target_max=150.
    # Valor 1200: /10=120 (Válido), /100=12 (Válido) -> AMBÍGUO.
    # Valor 1400: /10=140 (Válido), /100=14 (Válido) -> AMBÍGUO.
    # Para ser não ambíguo, precisamos de um valor que após uma divisão caia no range e após outra não.
    # Se usarmos um valor como 160: /10=16 (Válido), /100=1.6 (Inválido < 10).
    
    # CORREÇÃO DO BUG: ash_gkg=160 com unit=g/kg explícita e 160 > target_max=150
    # Antes: o resolver aplicava fix_10x_scale_down (dupla normalização)
    # Depois: com unidade explícita e valor fora do range, o dado é anulado (IMPLAUSIBLE)
    # Heurísticas de escala só se aplicam quando NÃO há unidade explícita
    data2 = {
        "product_id": [3, 4],
        "ash_gkg": [160.0, 160.0],
        "ash_unit": ["g/kg", None]  # Com e sem unidade explícita
    }
    df2 = pd.DataFrame(data2)
    norm_df2, _ = engine.normalize_dataframe(df2)
    # Com unidade explícita g/kg e valor 160 > 150: IMPLAUSIBLE
    assert pd.isna(norm_df2.loc[0, "ash_gkg"])
    assert norm_df2.loc[0, "ash_gkg_status"] == ValidationStatus.IMPLAUSIBLE
    # Sem unidade explícita e valor 160 > 150: heurística fix_10x -> 16.0
    assert norm_df2.loc[1, "ash_gkg"] == 16.0
    assert "fix_10x_scale_down" in norm_df2.loc[1, "ash_gkg_rule"]

def test_dim_product_enrichment():
    data = {
        "product_id": [1],
        "brand": ["Royal Canin"],
        "product_name": ["Ração Teste"],
        "product_type": ["Seca"],
        "package_weight": ["10kg"],
        "image_url": ["http://image.jpg"],
        "breed_size": ["Pequeno"]
    }
    df = pd.DataFrame(data)
    builder = ProductDimensionBuilder()
    dim = builder.build(df)
    
    assert "product_type" in dim.columns
    assert "image_url" in dim.columns
    assert dim.loc[0, "product_type"] == "Seca"
    assert dim.loc[0, "image_url"] == "http://image.jpg"

if __name__ == "__main__":
    print("Iniciando testes de melhorias v1.5...")
    test_metabolizable_energy_conversions()
    print("  - Conversões de Energia: OK")
    test_mass_balance_validation()
    print("  - Balanço de Massa: OK")
    test_scale_fix_and_ui()
    print("  - Correção de Escala e UI: OK")
    test_dim_product_enrichment()
    print("  - Enriquecimento dim_product: OK")
    print("\nTodos os testes passaram!")
