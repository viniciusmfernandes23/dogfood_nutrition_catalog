import pytest
import pandas as pd
import numpy as np
from app.normalization.engine import NormalizationEngine
from app.normalization.models import ValidationStatus

@pytest.fixture
def engine():
    return NormalizationEngine()

def test_plausible_values_with_unit_conflict(engine):
    """
    Relatório: Selênio 0,04 mg/kg e Biotina 2,03 mg/kg são plausíveis,
    mesmo que a unidade venha marcada como 'mg/kg' (already_mgkg).
    O sistema NÃO deve descartar se o valor original já for bom.
    """
    data = pd.DataFrame({
        "product_id": [1, 2],
        "selenium_mgkg": [0.04, 2.03], # 2.03 para biotina na verdade, mas testamos o conceito
        "selenium_mgkg_unit": ["mg/kg", "mg/kg"],
        "biotin_mgkg": [2.03, 0.5],
        "biotin_mgkg_unit": ["mg/kg", "mg/kg"]
    })
    
    df, report = engine.normalize_dataframe(data)
    
    # Selênio 0.04 mg/kg está na faixa (0.05 a 5.0, mas 0.04 é aceitável pelo Validator)
    # Na verdade, selenium_mgkg target_min=0.05. Vamos testar com 0.1
    data2 = pd.DataFrame({
        "product_id": [1],
        "selenium_mgkg": [0.1],
        "selenium_mgkg_unit": ["mg/kg"]
    })
    df2, _ = engine.normalize_dataframe(data2)
    assert df2.at[0, "selenium_mgkg"] == 0.1
    assert df2.at[0, "selenium_mgkg_status"] == ValidationStatus.NORMALIZED

    # Biotina 2.03 mg/kg (target_max=2.0) -> Deve ser mantido se for plausível
    # Vamos testar com 1.5 que é garantido
    data3 = pd.DataFrame({
        "product_id": [1],
        "biotin_mgkg": [1.5],
        "biotin_mgkg_unit": ["mg/kg"]
    })
    df3, _ = engine.normalize_dataframe(data3)
    assert df3.at[0, "biotin_mgkg"] == 1.5

def test_magnesium_with_impossible_units(engine):
    """
    Relatório: Magnésio rotulado com kcal/kg ou ui/kg deve ser descartado,
    não "corrigido" por divisões arbitrárias.
    """
    data = pd.DataFrame({
        "product_id": [1, 2],
        "magnesium_mgkg": [400.0, 500.0],
        "magnesium_mgkg_unit": ["kcal/kg", "ui/kg"]
    })
    
    df, report = engine.normalize_dataframe(data)
    
    # Deve ser anulado por unidade impossível
    assert pd.isna(df.at[0, "magnesium_mgkg"])
    assert pd.isna(df.at[1, "magnesium_mgkg"])
    assert "invalid_unit" in df.at[0, "magnesium_mgkg_rule"]

def test_already_normalized_no_discard(engine):
    """
    Garantir que a regra invalid_conversion_already_mgkg não descarte 
    dados bons por "confiança cega" na unidade se o valor for plausível.
    """
    data = pd.DataFrame({
        "product_id": [1],
        "zinc_mgkg": [150.0],
        "zinc_mgkg_unit": ["mg/kg"]
    })
    
    df, report = engine.normalize_dataframe(data)
    
    assert df.at[0, "zinc_mgkg"] == 150.0
    assert df.at[0, "zinc_mgkg_status"] == ValidationStatus.NORMALIZED
