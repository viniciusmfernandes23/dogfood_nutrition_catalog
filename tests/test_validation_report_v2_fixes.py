import pytest
import pandas as pd
import numpy as np
from app.normalization.engine import NormalizationEngine
from app.normalization.models import ValidationStatus

@pytest.fixture
def engine():
    return NormalizationEngine()

def test_unit_conflict_handling(engine):
    """
    Relatório Item 🆕: already_normalized_despite_unit_conflict era um bug silencioso.
    Agora deve converter corretamente ou anular se for implausível.
    """
    # Caso 1: fat_gkg original "30 mg/kg" -> Deve virar 0.03 g/kg
    data = pd.DataFrame({
        "product_id": [1],
        "fat_gkg": [30.0],
        "fat_gkg_unit": ["mg/kg"]
    })
    df, _ = engine.normalize_dataframe(data)
    # g/kg = mg/kg / 1000
    assert df.at[0, "fat_gkg"] == 0.03
    assert df.at[0, "fat_gkg_status"] == ValidationStatus.AUTO_CORRECTED

    # Caso 2: tryptophan_mgkg original "2000 g/kg" -> 2.000.000 mg/kg (Implausível)
    data2 = pd.DataFrame({
        "product_id": [2],
        "tryptophan_mgkg": [2000.0],
        "tryptophan_mgkg_unit": ["g/kg"]
    })
    df2, _ = engine.normalize_dataframe(data2)
    assert pd.isna(df2.at[0, "tryptophan_mgkg"])
    assert df2.at[0, "tryptophan_mgkg_status"] == ValidationStatus.IMPLAUSIBLE

def test_magnesium_unit_mapping_bug(engine):
    """
    Relatório Item 10: Magnésio com unidade ui/kg ou kcal/kg deve ser anulado,
    não "corrigido" por divisões.
    """
    data = pd.DataFrame({
        "product_id": [1],
        "magnesium_mgkg": [6000.0],
        "magnesium_mgkg_unit": ["ui/kg"]
    })
    df, _ = engine.normalize_dataframe(data)
    assert pd.isna(df.at[0, "magnesium_mgkg"])
    assert "invalid_unit_uikg" in df.at[0, "magnesium_mgkg_rule"]

def test_mass_balance_recalibration(engine):
    """
    Relatório Item 6: Balanço de massa recalibrado para considerar NFE (600-1050 g/kg).
    """
    # Soma: 320+80+104+91+110 = 705 (Agora deve passar para acomodar NFE)
    data = pd.DataFrame({
        "product_id": [1],
        "protein_gkg": [320.0],
        "fat_gkg": [80.0],
        "fiber_gkg": [104.0],
        "ash_gkg": [91.0],
        "moisture_gkg": [110.0]
    })
    df, _ = engine.normalize_dataframe(data)
    assert pd.notna(df.at[0, "protein_gkg"])
    assert df.at[0, "protein_gkg_status"] != ValidationStatus.PRODUCT_MASS_BALANCE_FAILED

def test_energy_recording_fix(engine):
    """
    Relatório Item 7: Energia status=normalized mas valor nulo.
    """
    data = pd.DataFrame({
        "product_id": [1],
        "metabolizable_energy_kcalkg": [3118.0],
        "metabolizable_energy_unit": ["kcal/kg"]
    })
    df, _ = engine.normalize_dataframe(data)
    assert df.at[0, "metabolizable_energy_kcalkg"] == 3118.0
    assert df.at[0, "metabolizable_energy_kcalkg_status"] == ValidationStatus.NORMALIZED
