import pytest
import pandas as pd
from app.normalization.engine import NormalizationEngine
from app.normalization.models import ValidationStatus

@pytest.fixture
def engine():
    return NormalizationEngine()

def test_priority_1_1_invalid_percent(engine):
    """Rejeitar percentual < 0% ou > 100%"""
    data = pd.DataFrame({
        "product_id": [1, 2, 3],
        "protein_gkg": [190, -5, 25],
        "protein_gkg_unit": ["%", "%", "%"],
        "fat_gkg": [50, 50, 50],
        "fiber_gkg": [10, 10, 10],
        "ash_gkg": [50, 50, 50],
        "moisture_gkg": [600, 600, 600] # Soma: 250+50+10+50+600 = 960 (OK)
    })
    
    df, report = engine.normalize_dataframe(data)
    
    # 190% -> Biologically Implausible Source
    assert pd.isna(df.at[0, "protein_gkg"])
    
    # -5% -> Biologically Implausible Source
    assert pd.isna(df.at[1, "protein_gkg"])
    
    # 25% -> OK (250 g/kg)
    assert df.at[2, "protein_gkg"] == 250.0

def test_priority_1_3_energy_limits(engine):
    """Aceitar apenas 500 kcal/kg <= Energia <= 9000 kcal/kg após conversão"""
    data = pd.DataFrame({
        "product_id": [1, 2, 3, 4],
        "metabolizable_energy_kcalkg": [45, 950, 350, 10000],
        "metabolizable_energy_unit": ["kcal/100g", "kcal/kg", "kcal/kg", "kcal/kg"]
    })
    
    df, report = engine.normalize_dataframe(data)
    
    # 45 kcal/100g -> 450 kcal/kg (Abaixo de 500) -> Implausible Energy
    assert pd.isna(df.at[0, "metabolizable_energy_kcalkg"])
    assert df.at[0, "metabolizable_energy_kcalkg_status"] == ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_ENERGY
    
    # 950 kcal/kg -> OK
    assert df.at[1, "metabolizable_energy_kcalkg"] == 950.0
    
    # 350 kcal/kg -> Implausible Energy
    assert pd.isna(df.at[2, "metabolizable_energy_kcalkg"])
    assert df.at[2, "metabolizable_energy_kcalkg_status"] == ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_ENERGY
    
    # 10000 kcal/kg -> Implausible Energy
    assert pd.isna(df.at[3, "metabolizable_energy_kcalkg"])
    assert df.at[3, "metabolizable_energy_kcalkg_status"] == ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_ENERGY

def test_priority_2_1_mass_balance(engine):
    """Validar soma dos nutrientes proximais (850–1050 g/kg)"""
    data = pd.DataFrame({
        "product_id": [1, 2],
        "protein_gkg": [300, 500],
        "fat_gkg": [200, 400],
        "fiber_gkg": [50, 100],
        "ash_gkg": [100, 200],
        "moisture_gkg": [300, 100],
        "protein_gkg_unit": ["g/kg", "g/kg"],
        "fat_gkg_unit": ["g/kg", "g/kg"],
        "fiber_gkg_unit": ["g/kg", "g/kg"],
        "ash_gkg_unit": ["g/kg", "g/kg"],
        "moisture_gkg_unit": ["g/kg", "g/kg"]
    })
    
    # Adicionar product_category para garantir que não é tratado como petisco
    data["product_category"] = "Ração Seca"
    
    df, report = engine.normalize_dataframe(data)
    
    # Prod 1: 300+200+50+100+300 = 950 (OK)
    assert df.at[0, "protein_gkg"] == 300
    
    # Prod 2: 500+400+100+200+100 = 1300 (Falha)
    # Nota: A proteína de 500 é convertida para 50.0 (already_gkg) se o target_max for 600.
    # Vamos usar valores que garantam a soma > 1050.
    data.at[1, "protein_gkg"] = 500.0
    data.at[1, "fat_gkg"] = 200.0
    data.at[1, "fiber_gkg"] = 100.0
    data.at[1, "ash_gkg"] = 100.0
    data.at[1, "moisture_gkg"] = 200.0
    # Soma: 500+200+100+100+200 = 1100 (Falha)
    
    df, report = engine.normalize_dataframe(data)
    
    assert pd.isna(df.at[1, "protein_gkg"])
    assert df.at[1, "protein_gkg_status"] == ValidationStatus.PRODUCT_MASS_BALANCE_FAILED

def test_priority_2_2_ca_p_ratio(engine):
    """Validar relação Cálcio:Fósforo (1:1 até 2:1)"""
    data = pd.DataFrame({
        "product_id": [1, 2, 3],
        "calcium_min_mgkg": [12000, 8000, 25000],
        "phosphorus_mgkg": [10000, 10000, 10000]
    })
    
    df, report = engine.normalize_dataframe(data)
    
    # 1.2:1 -> OK
    assert df.at[0, "calcium_min_mgkg"] == 12000
    
    # 0.8:1 -> Falha
    assert pd.isna(df.at[1, "calcium_min_mgkg"])
    assert df.at[1, "calcium_min_mgkg_status"] == ValidationStatus.INVALID_CA_P_RATIO
    
    # 2.5:1 -> Falha
    assert pd.isna(df.at[2, "calcium_min_mgkg"])
    assert df.at[2, "calcium_min_mgkg_status"] == ValidationStatus.INVALID_CA_P_RATIO

def test_priority_4_micronutrient_limits(engine):
    """Validar limites biológicos para micronutrientes (ex: Selênio 0-5 mg/kg)"""
    data = pd.DataFrame({
        "product_id": [1, 2],
        "selenium_mgkg": [0.5, 8312],
        "selenium_mgkg_unit": ["mg/kg", "mg/kg"]
    })
    
    df, report = engine.normalize_dataframe(data)
    
    # 0.5 mg/kg -> OK
    assert df.at[0, "selenium_mgkg"] == 0.5
    
    # 8312 mg/kg -> Implausible (target_max=5)
    assert pd.isna(df.at[1, "selenium_mgkg"])
    assert df.at[1, "selenium_mgkg_status"] == ValidationStatus.IMPLAUSIBLE
