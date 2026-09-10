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
    # Vamos usar valores que garantam a soma > 1100 (limite de FAILED).
    data.at[1, "protein_gkg"] = 500.0
    data.at[1, "fat_gkg"] = 250.0
    data.at[1, "fiber_gkg"] = 100.0
    data.at[1, "ash_gkg"] = 100.0
    data.at[1, "moisture_gkg"] = 200.0
    # Soma: 500+250+100+100+200 = 1150 (Falha: > 1100)
    
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


def test_ca_p_ratio_does_not_invalidate_treats(engine):
    """Petiscos não devem ser descartados pela razão Ca:P de alimentos completos."""
    data = pd.DataFrame({
        "product_id": [31174738],
        "product_category": ["Petisco"],
        "calcium_min_mgkg": [15000],
        "calcium_max_mgkg": [60000],
        "phosphorus_mgkg": [30000],
    })

    df, report = engine.normalize_dataframe(data)

    assert df.at[0, "calcium_min_mgkg"] == 15000
    assert df.at[0, "calcium_max_mgkg"] == 60000
    assert df.at[0, "phosphorus_mgkg"] == 30000
    assert df.at[0, "calcium_min_mgkg_status"] == ValidationStatus.NORMALIZED


def test_biscuit_does_not_fail_mass_balance(engine):
    """Biscoitos são petiscos e não devem falhar no balanço de ração completa."""
    data = pd.DataFrame({
        "product_id": [3325775],
        "product_category": ["Cookies e Biscoitos Cachorro"],
        "protein_gkg": [100.0],
        "fat_gkg": [55.0],
        "fiber_gkg": [40.0],
        "ash_gkg": [70.0],
        "moisture_gkg": [100.0],
    })

    df, report = engine.normalize_dataframe(data)

    assert df.at[0, "protein_gkg"] == 100.0
    assert df.at[0, "fat_gkg"] == 55.0
    assert df.at[0, "fiber_gkg"] == 40.0
    assert df.at[0, "ash_gkg"] == 70.0
    assert df.at[0, "moisture_gkg"] == 100.0
    assert df.at[0, "protein_gkg_status"] == ValidationStatus.NORMALIZED


def test_wet_food_keeps_low_fiber_ash_and_skips_ca_p_ratio(engine):
    """Alimento úmido não deve falhar pelos mínimos de alimento seco."""
    data = pd.DataFrame({
        "product_id": [3448095],
        "product_category": ["Ração Úmida"],
        "protein_gkg": [85],
        "fat_gkg": [5000.0],
        "fat_gkg_unit": ["mg/kg"],
        "fiber_gkg": [3500.0],
        "fiber_gkg_unit": ["mg/kg"],
        "moisture_gkg": [880.0],
        "ash_gkg": [6000.0],
        "ash_gkg_unit": ["mg/kg"],
        "calcium_min_mgkg": [100],
        "calcium_max_mgkg": [400],
        "phosphorus_mgkg": [500],
    })

    df, report = engine.normalize_dataframe(data)

    assert df.at[0, "fiber_gkg"] == 3.5
    assert df.at[0, "ash_gkg"] == 6.0
    assert df.at[0, "calcium_min_mgkg"] == 100
    assert df.at[0, "phosphorus_mgkg"] == 500


def test_energy_per_sachet_is_converted_to_kcal_per_kg(engine):
    data = pd.DataFrame({
        "product_id": [3472182],
        "product_category": ["Ração Úmida"],
        "metabolizable_energy_kcalkg": [72.0],
        "metabolizable_energy_unit": ["kcal/sache"],
    })

    df, report = engine.normalize_dataframe(data)

    assert round(df.at[0, "metabolizable_energy_kcalkg"], 2) == 847.06
    assert df.at[0, "metabolizable_energy_kcalkg_status"] == ValidationStatus.NORMALIZED


def test_wet_food_preserves_low_enrichment_values(engine):
    data = pd.DataFrame({
        "product_id": [3472107],
        "product_category": ["Ração Úmida"],
        "folic_acid_mgkg": [0.06],
        "niacin_mgkg": [4.10],
        "pantothenic_acid_mgkg": [3.50],
        "vitamin_b1_mgkg": [0.53],
        "vitamin_b6_mgkg": [0.36],
        "vitamin_k3_mgkg": [0.05],
        "zinc_mgkg": [18.0],
    })

    df, report = engine.normalize_dataframe(data)

    for field in data.columns[2:]:
        assert df.at[0, field] == data.at[0, field]
        assert df.at[0, f"{field}_status"] == ValidationStatus.NORMALIZED


def test_energy_per_unit_is_not_normalized(engine):
    data = pd.DataFrame({
        "product_id": [3928380],
        "product_category": ["Petisco Snack"],
        "metabolizable_energy_kcalkg": [None],
    })

    df, report = engine.normalize_dataframe(data)

    assert pd.isna(df.at[0, "metabolizable_energy_kcalkg"])
    assert df.at[0, "metabolizable_energy_kcalkg_status"] == ValidationStatus.MISSING

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
