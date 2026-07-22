from __future__ import annotations

import pandas as pd
import numpy as np

from app.normalization.engine import NormalizationEngine
from app.normalization.models import (
    NormalizedNutrient,
    ValidationStatus,
)
from app.normalization.resolver import Resolver
from app.normalization.validator import Validator
from app.normalization.rules import get_rule


def test_validator_accepts_valid_protein():
    rule = get_rule("protein_gkg")
    nutrient = NormalizedNutrient(
        name="protein_gkg",
        value=260,
        unit="g/kg",
    )

    result = Validator().validate(
        nutrient,
        rule=rule
    )
    result.original_unit = nutrient.original_unit
    result.normalized_unit = nutrient.unit

    assert (
        result.status
        == ValidationStatus.NORMALIZED
    )


def test_validator_rejects_negative_value():
    rule = get_rule("protein_gkg")
    nutrient = NormalizedNutrient(
        name="protein_gkg",
        value=-10,
        unit="g/kg",
    )

    result = Validator().validate(
        nutrient,
        rule=rule
    )
    result.original_unit = nutrient.original_unit
    result.normalized_unit = nutrient.unit

    assert (
        result.status
        == ValidationStatus.IMPLAUSIBLE
    )


def test_validator_detects_implausible_value():
    rule = get_rule("protein_gkg")
    nutrient = NormalizedNutrient(
        name="protein_gkg",
        value=2000,
        unit="g/kg",
    )

    result = Validator().validate(
        nutrient,
        rule=rule
    )
    result.original_unit = nutrient.original_unit
    result.normalized_unit = nutrient.unit

    assert (
        result.status
        == ValidationStatus.IMPLAUSIBLE
    )


def test_resolver_converts_percent_to_gkg():
    rule = get_rule("protein_gkg")
    nutrient = NormalizedNutrient(
        name="protein_gkg",
        value=26,
        unit="g/kg",
        original_unit="%"
    )

    resolved = Resolver().resolve(
        nutrient,
        rule=rule
    )

    assert resolved.value == 260


def test_resolver_keeps_normalized_values():
    rule = get_rule("fat_gkg")
    nutrient = NormalizedNutrient(
        name="fat_gkg",
        value=150,
        unit="g/kg",
    )

    resolved = Resolver().resolve(
        nutrient,
        rule=rule
    )

    assert resolved.value == 150


def test_engine_normalizes_dataframe():

    df = pd.DataFrame(
        {
            "product_id": [1],
            "protein_gkg": [26],
            "protein_gkg_unit": ["%"],
        }
    )

    engine = NormalizationEngine()

    normalized, report = (
        engine.normalize_dataframe(
            df
        )
    )

    assert len(normalized) == 1
    assert report is not None
    assert normalized.at[0, "protein_gkg"] == 260.0


def test_engine_preserves_product_count():

    df = pd.DataFrame(
        {
            "product_id": [1, 2, 3],
        }
    )

    engine = NormalizationEngine()

    normalized, _ = (
        engine.normalize_dataframe(
            df
        )
    )

    assert len(normalized) == 3


def test_engine_returns_dataframe():

    df = pd.DataFrame(
        {
            "product_id": [1],
        }
    )

    engine = NormalizationEngine()

    normalized, _ = (
        engine.normalize_dataframe(
            df
        )
    )

    assert isinstance(
        normalized,
        pd.DataFrame,
    )


def test_validator_marks_missing_value():
    rule = get_rule("protein_gkg")
    nutrient = NormalizedNutrient(
        name="protein_gkg",
        value=None,
        unit="g/kg",
    )

    result = Validator().validate(
        nutrient,
        rule=rule
    )
    result.original_unit = nutrient.original_unit
    result.normalized_unit = nutrient.unit

    assert result.status == ValidationStatus.MISSING


def test_validator_accepts_calcium():
    rule = get_rule("calcium_min_mgkg")
    nutrient = NormalizedNutrient(
        name="calcium_min_mgkg",
        value=12000,
        unit="mg/kg",
    )

    result = Validator().validate(
        nutrient,
        rule=rule
    )
    result.original_unit = nutrient.original_unit
    result.normalized_unit = nutrient.unit

    assert result.status == ValidationStatus.NORMALIZED


def test_engine_handles_empty_dataframe():

    df = pd.DataFrame()

    engine = NormalizationEngine()

    normalized, report = (
        engine.normalize_dataframe(
            df
        )
    )

    assert normalized.empty

    assert report is not None


def test_engine_does_not_modify_original_dataframe():

    df = pd.DataFrame(
        {
            "product_id": [1],
            "protein_gkg": [26],
            "protein_gkg_unit": ["%"],
        }
    )

    original = df.copy(
        deep=True
    )

    engine = NormalizationEngine()

    engine.normalize_dataframe(
        df
    )

    pd.testing.assert_frame_equal(
        df,
        original,
    )

def test_biological_audit_regression():
    """Testa as novas regras de auditoria biológica v1.4.1"""
    engine = NormalizationEngine()
    
    data = {
        "product_id": [101, 102, 103, 104],
        "calcium_min_mgkg": [1000.0, 2000.0, 0.0, 5000.0],
        "phosphorus_mgkg": [1300.0, 50.0, 0.0, 5000.0],
        "protein_gkg": [250.0, 250.0, 250.0, 1.0], # 1.0g/kg é insuficiente
        "fat_gkg": [100.0, 100.0, 100.0, 100.0],
        "sodium_mgkg": [2000.0, 2000.0, 2000.0, 3000.0],
    }
    df = pd.DataFrame(data)
    normalized_df, _ = engine.normalize_dataframe(df)
    
    # 101: Razão Ca:P < 1.0 (0.77) -> Anulado
    assert pd.isna(normalized_df.at[0, "calcium_min_mgkg"])
    assert pd.isna(normalized_df.at[0, "phosphorus_mgkg"])
    
    # 102: Razão Ca:P > 2.0 (40.0) -> Anulado
    assert pd.isna(normalized_df.at[1, "calcium_min_mgkg"])
    assert pd.isna(normalized_df.at[1, "phosphorus_mgkg"])
    
    # 103: Minerais Zerados -> Anulado
    assert pd.isna(normalized_df.at[2, "calcium_min_mgkg"])
    assert pd.isna(normalized_df.at[2, "phosphorus_mgkg"])
    
    # 104: Proteína Insignificante (1.0g/kg) -> OK (target_min agora é 0.1)
    assert normalized_df.at[3, "protein_gkg"] == 1.0


# =============================================================================
# Testes de Regressão: Barreira Biológica de Unidade de Energia Metabolizável
# Ref: Bug Biofresh Cães Sênior Raças Grandes — valor 300 mg/kg para energia
# =============================================================================

def test_resolver_rejects_mgkg_for_metabolizable_energy():
    """
    Energia metabolizável com unidade mg/kg deve ser anulada (None).
    Caso concreto: Biofresh Sênior Raças Grandes — 300 mg/kg é fisicamente
    impossível para energia; a unidade correta seria kcal/kg.
    """
    rule = get_rule("metabolizable_energy_kcalkg")
    nutrient = NormalizedNutrient(
        name="metabolizable_energy_kcalkg",
        value=300,
        unit="kcal/kg",
        original_unit="mg/kg",
    )

    resolved = Resolver().resolve(nutrient, rule=rule)

    assert resolved.value is None, (
        "Energia em mg/kg deve ser anulada pela barreira biológica"
    )


def test_resolver_accepts_kcal_per_100g_for_metabolizable_energy():
    """
    Energia metabolizável em kcal/100g deve ser convertida para kcal/kg
    multiplicando por 10. Ex.: 350 kcal/100g -> 3500 kcal/kg.
    """
    rule = get_rule("metabolizable_energy_kcalkg")
    nutrient = NormalizedNutrient(
        name="metabolizable_energy_kcalkg",
        value=350,
        unit="kcal/kg",
        original_unit="kcal/100g",
    )

    resolved = Resolver().resolve(nutrient, rule=rule)

    assert resolved.value == 3500.0, (
        "350 kcal/100g deve ser convertido para 3500 kcal/kg"
    )


def test_resolver_accepts_mjkg_for_metabolizable_energy():
    """
    Energia metabolizável em MJ/kg deve ser convertida para kcal/kg
    multiplicando por 239.006. Ex.: 14.6 MJ/kg -> ~3489.49 kcal/kg.
    """
    rule = get_rule("metabolizable_energy_kcalkg")
    nutrient = NormalizedNutrient(
        name="metabolizable_energy_kcalkg",
        value=14.6,
        unit="kcal/kg",
        original_unit="mj/kg",
    )

    resolved = Resolver().resolve(nutrient, rule=rule)

    assert resolved.value is not None, (
        "Energia em MJ/kg deve ser convertida, não anulada"
    )
    assert abs(resolved.value - 3489.49) < 1.0, (
        f"14.6 MJ/kg deve ser ~3489.49 kcal/kg, obtido {resolved.value}"
    )


def test_engine_nullifies_energy_with_mgkg_unit():
    """
    Teste de ponta a ponta: o engine deve anular a energia metabolizável
    quando a coluna de unidade indica mg/kg (caso Biofresh).
    """
    engine = NormalizationEngine()

    df = pd.DataFrame({
        "product_id": [999],
        "metabolizable_energy_kcalkg": [300.0],
        "metabolizable_energy_unit": ["mg/kg"],
    })

    normalized, _ = engine.normalize_dataframe(df)

    assert pd.isna(normalized.at[0, "metabolizable_energy_kcalkg"]), (
        "Energia com unidade mg/kg deve ser anulada no pipeline completo"
    )


def test_engine_converts_plausible_kcal_100g():
    """
    Testa se o engine converte kcal/100g para kcal/kg mesmo quando o valor
    original já está no range plausível de kcal/kg (ex: 1200 kcal/100g).
    Sem a correção da trava de segurança, o engine ignoraria a unidade.
    """
    engine = NormalizationEngine()

    df = pd.DataFrame({
        "product_id": [123],
        "metabolizable_energy_kcalkg": [1200.0],
        "metabolizable_energy_unit": ["kcal/100g"],
    })

    normalized, _ = engine.normalize_dataframe(df)

    # 1200 kcal/100g -> 12000 kcal/kg
    # Como 12000 > 4500 (limite biológico atualizado), o resolver deve anular o valor
    # com a regra 'biologically_implausible_energy'.
    assert pd.isna(normalized.at[0, "metabolizable_energy_kcalkg"]), (
        "O engine deve anular energia que excede 4500 kcal/kg após conversão"
    )

def test_engine_nullifies_energy_without_unit():
    """
    Testa se o engine anula energia metabolizável quando não há unidade,
    seguindo a nova abordagem determinística.
    """
    engine = NormalizationEngine()
    df = pd.DataFrame({
        "product_id": [456],
        "metabolizable_energy_kcalkg": [3500.0],
        # Sem coluna de unidade
    })
    normalized, _ = engine.normalize_dataframe(df)
    assert pd.isna(normalized.at[0, "metabolizable_energy_kcalkg"]), (
        "Energia sem unidade deve ser anulada por ser indeterminística"
    )
