import pandas as pd
import numpy as np
from app.normalization.engine import NormalizationEngine
from app.normalization.models import ValidationStatus

def test_dry_food_mass_balance_with_carbs():
    """
    Testa se uma ração seca com soma de macros ~650g/kg (comum em rações secas)
    agora é aceita, em vez de ser anulada.
    """
    engine = NormalizationEngine()
    
    # Simula ração seca típica:
    # Proteína: 250g/kg
    # Gordura: 120g/kg
    # Fibra: 30g/kg
    # Cinzas: 70g/kg
    # Umidade: 100g/kg
    # SOMA: 570g/kg -> Isso deve falhar se o limite for 600
    # Se aumentarmos um pouco:
    # SOMA: 650g/kg -> Deve passar agora
    
    data = {
        "product_id": [1],
        "product_category": ["Ração Seca"],
        "protein_gkg": [250.0],
        "fat_gkg": [150.0],
        "fiber_gkg": [50.0],
        "ash_gkg": [100.0],
        "moisture_gkg": [100.0]
    }
    # Soma = 250+150+50+100+100 = 650 g/kg
    
    df = pd.DataFrame(data)
    normalized_df, _ = engine.normalize_dataframe(df)
    
    # Deve passar (status NORMALIZED ou AUTO_CORRECTED, não MASS_BALANCE_FAILED)
    status = str(normalized_df.at[0, "protein_gkg_status"])
    print(f"Soma 650g/kg - Status: {status}")
    assert "product_mass_balance_failed" not in status.lower()
    assert pd.notna(normalized_df.at[0, "protein_gkg"])

def test_invalid_low_mass_balance():
    """
    Testa se uma soma realmente impossível (ex: 300g/kg) continua sendo rejeitada.
    """
    engine = NormalizationEngine()
    
    data = {
        "product_id": [2],
        "product_category": ["Ração Seca"],
        "protein_gkg": [20.0],
        "fat_gkg": [20.0],
        "fiber_gkg": [20.0],
        "ash_gkg": [20.0],
        "moisture_gkg": [80.0]
    }
    # Soma = 20+20+20+20+80 = 160 g/kg
    
    df = pd.DataFrame(data)
    normalized_df, _ = engine.normalize_dataframe(df)
    
    status = str(normalized_df.at[0, "protein_gkg_status"])
    print(f"Soma 250g/kg - Status: {status}")
    assert "product_mass_balance_failed" in status.lower()
    assert pd.isna(normalized_df.at[0, "protein_gkg"])


def test_mass_balance_requires_moisture():
    """Sem umidade declarada, o balanço não deve reprovar o produto."""
    data = {
        "product_id": [3457329],
        "product_category": ["Ração Seca"],
        "protein_gkg": [260.0],
        "fat_gkg": [120.0],
        "fiber_gkg": [40.0],
        "ash_gkg": [72.0],
    }

    normalized_df, _ = NormalizationEngine().normalize_dataframe(pd.DataFrame(data))

    assert normalized_df.at[0, "protein_gkg"] == 260.0
    assert normalized_df.at[0, "protein_gkg_status"] == ValidationStatus.NORMALIZED


def test_dry_food_high_nfe_mass_balance_is_review():
    """Uma ração seca com NFE alto deve ser revisada, não descartada."""
    data = {
        "product_id": [3643874],
        "product_category": ["Ração Seca"],
        "protein_gkg": [105.0],
        "fat_gkg": [165.0],
        "fiber_gkg": [35.0],
        "ash_gkg": [65.0],
        "moisture_gkg": [100.0],
    }

    normalized_df, _ = NormalizationEngine().normalize_dataframe(pd.DataFrame(data))

    assert normalized_df.at[0, "protein_gkg"] == 105.0
    assert normalized_df.at[0, "protein_gkg_status"] == ValidationStatus.REVIEW


def test_therapeutic_dry_food_with_low_protein_is_review():
    """Dieta renal com NFE alto não deve ser descartada pelo balanço genérico."""
    data = {
        "product_id": [3647250],
        "product_name": ["Ração Vet Life Natural Renal"],
        "product_category": ["Ração Seca"],
        "protein_gkg": [133.0],
        "fat_gkg": [170.0],
        "fiber_gkg": [16.0],
        "ash_gkg": [46.0],
        "moisture_gkg": [90.0],
        "lysine_mgkg": [4600.0],
        "lysine_mgkg_unit": ["mg/kg"],
    }

    normalized_df, _ = NormalizationEngine().normalize_dataframe(pd.DataFrame(data))

    assert normalized_df.at[0, "protein_gkg"] == 133.0
    assert normalized_df.at[0, "protein_gkg_status"] == ValidationStatus.REVIEW
    assert normalized_df.at[0, "lysine_mgkg"] == 4600.0

if __name__ == "__main__":
    test_dry_food_mass_balance_with_carbs()
    test_invalid_low_mass_balance()
    print("Todos os testes de recalibração de balanço de massa passaram!")
