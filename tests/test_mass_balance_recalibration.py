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

if __name__ == "__main__":
    test_dry_food_mass_balance_with_carbs()
    test_invalid_low_mass_balance()
    print("Todos os testes de recalibração de balanço de massa passaram!")
