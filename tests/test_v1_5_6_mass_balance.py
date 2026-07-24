
import pandas as pd
import numpy as np
from app.normalization.engine import NormalizationEngine
from app.normalization.models import ValidationStatus

def test_mass_balance_600_ok():
    engine = NormalizationEngine()
    
    # Caso: Soma = 650 g/kg (Deve ser NORMALIZED na v1.5.6)
    data = {
        "product_id": [1],
        "product_category": ["Ração Seca"],
        "protein_gkg": [250.0],
        "fat_gkg": [150.0],
        "fiber_gkg": [50.0],
        "ash_gkg": [100.0],
        "moisture_gkg": [100.0], # Soma = 650
        "metabolizable_energy_kcalkg": [3500.0],
        "metabolizable_energy_unit": ["kcal/kg"]
    }
    df = pd.DataFrame(data)
    normalized_df, _ = engine.normalize_dataframe(df)
    
    assert normalized_df.loc[0, "protein_gkg_status"] == ValidationStatus.NORMALIZED
    assert normalized_df.loc[0, "metabolizable_energy_kcalkg"] == 3500.0
    print("  - Soma 650 g/kg (OK): Passou")

def test_mass_balance_550_review():
    engine = NormalizationEngine()
    
    # Caso: Soma = 550 g/kg (Deve ser REVIEW na v1.5.6)
    data = {
        "product_id": [2],
        "product_category": ["Ração Seca"],
        "protein_gkg": [200.0],
        "fat_gkg": [100.0],
        "fiber_gkg": [50.0],
        "ash_gkg": [100.0],
        "moisture_gkg": [100.0], # Soma = 550
        "metabolizable_energy_kcalkg": [3500.0],
        "metabolizable_energy_unit": ["kcal/kg"]
    }
    df = pd.DataFrame(data)
    normalized_df, _ = engine.normalize_dataframe(df)
    
    assert normalized_df.loc[0, "protein_gkg_status"] == ValidationStatus.REVIEW
    assert normalized_df.loc[0, "metabolizable_energy_kcalkg"] == 3500.0 # Não deve ser anulado em REVIEW
    print("  - Soma 550 g/kg (REVIEW): Passou")

def test_mass_balance_450_failed():
    engine = NormalizationEngine()
    
    # Caso: Soma = 450 g/kg (Deve ser FAILED na v1.5.6)
    data = {
        "product_id": [3],
        "product_category": ["Ração Seca"],
        "protein_gkg": [150.0],
        "fat_gkg": [50.0],
        "fiber_gkg": [50.0],
        "ash_gkg": [100.0],
        "moisture_gkg": [100.0], # Soma = 450
        "metabolizable_energy_kcalkg": [3500.0],
        "metabolizable_energy_unit": ["kcal/kg"]
    }
    df = pd.DataFrame(data)
    normalized_df, _ = engine.normalize_dataframe(df)
    
    assert normalized_df.loc[0, "protein_gkg_status"] == ValidationStatus.PRODUCT_MASS_BALANCE_FAILED
    assert pd.isna(normalized_df.loc[0, "metabolizable_energy_kcalkg"]) # Deve ser anulado em FAILED
    print("  - Soma 450 g/kg (FAILED): Passou")

if __name__ == "__main__":
    print("Iniciando testes de balanço de massa v1.5.6...")
    test_mass_balance_600_ok()
    test_mass_balance_550_review()
    test_mass_balance_450_failed()
    print("\nTodos os testes de balanço de massa v1.5.6 passaram!")
