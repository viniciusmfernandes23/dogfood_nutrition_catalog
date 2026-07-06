from __future__ import annotations

import pandas as pd

from app.normalization.engine import NormalizationEngine
from app.normalization.models import (
    NormalizedNutrient,
    ValidationStatus,
)
from app.normalization.resolver import Resolver
from app.normalization.validator import Validator


def test_validator_accepts_valid_protein():

    nutrient = NormalizedNutrient(
        name="protein",
        value=260,
        unit="g/kg",
    )

    result = Validator().validate(
        nutrient
    )

    assert (
        result.status
        == ValidationStatus.NORMALIZED
    )


def test_validator_rejects_negative_value():

    nutrient = NormalizedNutrient(
        name="protein",
        value=-10,
        unit="g/kg",
    )

    result = Validator().validate(
        nutrient
    )

    assert (
        result.status
        == ValidationStatus.IMPLAUSIBLE
    )


def test_validator_detects_implausible_value():

    nutrient = NormalizedNutrient(
        name="protein",
        value=2000,
        unit="g/kg",
    )

    result = Validator().validate(
        nutrient
    )

    assert (
        result.status
        == ValidationStatus.IMPLAUSIBLE
    )


def test_resolver_converts_percent_to_gkg():

    nutrient = NormalizedNutrient(
        name="protein",
        value=26,
        unit="%",
    )

    resolved = Resolver().resolve(
        nutrient
    )

    assert resolved.unit == "g/kg"

    assert resolved.value == 260


def test_resolver_keeps_normalized_values():

    nutrient = NormalizedNutrient(
        name="fat",
        value=150,
        unit="g/kg",
    )

    resolved = Resolver().resolve(
        nutrient
    )

    assert resolved.value == 150

    assert resolved.unit == "g/kg"


def test_engine_normalizes_dataframe():

    df = pd.DataFrame(

        {

            "product_id": [1],

            "protein": [26],

            "protein_unit": ["%"],

        }

    )

    engine = NormalizationEngine()

    normalized, report = (
        engine.normalize_dataframe(
            df
        )
    )

    assert len(
        normalized
    ) == 1

    assert report is not None


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

    assert len(
        normalized
    ) == 3


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

    nutrient = NormalizedNutrient(
        name="protein",
        value=None,
        unit="g/kg",
    )

    result = Validator().validate(
        nutrient
    )

    assert result.status in {

        ValidationStatus.MISSING,

        ValidationStatus.REVIEW,

    }


def test_validator_accepts_calcium():

    nutrient = NormalizedNutrient(
        name="calcium_min",
        value=12000,
        unit="mg/kg",
    )

    result = Validator().validate(
        nutrient
    )

    assert result.status == (
        ValidationStatus.NORMALIZED
    )


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

            "protein": [26],

            "protein_unit": ["%"],

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