
import pandas as pd
import numpy as np
from app.normalization.engine import NormalizationEngine
from app.normalization.models import ValidationStatus
from app.semantic.engine import SemanticEngine
from app.warehouse.dim_product import ProductDimensionBuilder

def test_metabolizable_energy_conversions():
    engine = NormalizationEngine()
    
    # Caso 1: kcal/100g -> kcal/kg
    # Caso 2: kcal/sache (85g) -> kcal/kg
    # Caso 3: MJ/kg -> kcal/kg
    # Caso 4: Unidade inválida (mg/kg) -> anular
    
    data = {
        "product_id": [1, 2, 3, 4, 5],
        "product_name": ["Prod 1", "Prod 2", "Prod 3", "Prod 4", "Prod 5"],
        "metabolizable_energy_kcalkg": [477.0, 72.0, 15.0, 300.0, 4038.0],
        "metabolizable_energy_unit": ["kcal/100g", "kcal/sache", "mj/kg", "mg/kg", "kcal/kg"]
    }
    df = pd.DataFrame(data)
    norm_df, _ = engine.normalize_dataframe(df)
    
    # 477 kcal/100g -> 4770 kcal/kg
    assert norm_df.loc[0, "metabolizable_energy_kcalkg"] == 4770.0
    
    # 72 kcal / 85g -> (72/85)*1000 = 847.06
    assert 847.0 <= norm_df.loc[1, "metabolizable_energy_kcalkg"] <= 847.1
    
    # 15 MJ/kg -> 15 * 239.006 = 3585.09
    assert 3585.0 <= norm_df.loc[2, "metabolizable_energy_kcalkg"] <= 3585.1
    
    # 300 mg/kg -> anular
    assert pd.isna(norm_df.loc[3, "metabolizable_energy_kcalkg"])
    
    # 4038 kcal/kg -> manter
    assert norm_df.loc[4, "metabolizable_energy_kcalkg"] == 4038.0

def test_mass_balance_validation():
    engine = NormalizationEngine()
    
    # v1.5.0:
    # OK: 850–1050 g/kg
    # REVIEW: 700–850 ou 1050–1150 g/kg
    # FAILED: < 700 ou > 1150 g/kg
    
    data = {
        "product_id": [1, 2, 3, 4, 5],
        "product_category": ["Ração Seca"] * 5,
        "protein_gkg": [300, 250, 400, 200, 500],
        "fat_gkg": [150, 100, 200, 100, 250],
        "fiber_gkg": [50, 50, 100, 50, 100],
        "ash_gkg": [100, 100, 100, 100, 100],
        "moisture_gkg": [300, 300, 300, 200, 300],
    }
    # Soma 1: 900 (OK)
    # Soma 2: 800 (REVIEW)
    # Soma 3: 1100 (REVIEW)
    # Soma 4: 650 (FAILED)
    # Soma 5: 1250 (FAILED)
    
    df = pd.DataFrame(data)
    norm_df, _ = engine.normalize_dataframe(df)
    
    assert norm_df.loc[0, "protein_gkg_status"] == ValidationStatus.NORMALIZED
    assert norm_df.loc[1, "protein_gkg_status"] == ValidationStatus.REVIEW
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
    
    data2 = {
        "product_id": [3],
        "ash_gkg": [160.0],
        "ash_unit": ["g/kg"]
    }
    df2 = pd.DataFrame(data2)
    norm_df2, _ = engine.normalize_dataframe(df2)
    assert norm_df2.loc[0, "ash_gkg"] == 16.0
    assert "fix_10x_scale_down" in norm_df2.loc[0, "ash_gkg_rule"]

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
