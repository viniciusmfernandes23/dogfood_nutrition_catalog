from __future__ import annotations

import pandas as pd

from app.semantic.classifier import SemanticClassifier
from app.semantic.engine import SemanticEngine
from app.semantic.rules import (
    BREED_SIZE_RULES,
    CLINICAL_RULES,
    LIFESTAGE_RULES,
    PRODUCT_CATEGORY_RULES,
    PRODUCT_TIER_RULES,
    PROTEIN_RULES,
)


def test_product_category_classifier():

    classifier = SemanticClassifier(
        PRODUCT_CATEGORY_RULES,
    )

    result = classifier.best_match(
        "Ração Seca Super Premium"
    )

    assert result is not None


def test_life_stage_classifier():

    classifier = SemanticClassifier(
        LIFESTAGE_RULES,
    )

    result = classifier.best_match(
        "Ração para Filhotes"
    )

    assert result is not None


def test_breed_classifier():

    classifier = SemanticClassifier(
        BREED_SIZE_RULES,
    )

    result = classifier.best_match(
        "Raças Pequenas"
    )

    assert result is not None


def test_clinical_classifier():

    classifier = SemanticClassifier(
        CLINICAL_RULES,
    )

    result = classifier.best_match(
        "Ração Renal Terapêutica"
    )

    assert result is not None


def test_protein_classifier():

    classifier = SemanticClassifier(
        PROTEIN_RULES,
    )

    result = classifier.classify_many(
        "Frango e Salmão"
    )

    assert len(result) >= 2


def test_product_tier_classifier():

    classifier = SemanticClassifier(
        PRODUCT_TIER_RULES,
    )

    result = classifier.best_match(
        "Super Premium"
    )

    assert result is not None


def test_classifier_returns_none_when_no_match():

    classifier = SemanticClassifier(
        PRODUCT_CATEGORY_RULES,
    )

    result = classifier.best_match(
        "Produto completamente desconhecido"
    )

    assert result is None


def test_classifier_is_case_insensitive():

    classifier = SemanticClassifier(
        PRODUCT_CATEGORY_RULES,
    )

    result = classifier.best_match(
        "RAÇÃO SECA"
    )

    assert result is not None


def test_classifier_extract_keywords():

    classifier = SemanticClassifier(
        PRODUCT_CATEGORY_RULES,
    )

    keywords = classifier.extract_keywords(
        "Ração Seca Premium"
    )

    assert len(keywords) > 0


def test_classifier_score():

    classifier = SemanticClassifier(
        PRODUCT_CATEGORY_RULES,
    )

    scores = classifier.score(
        "Ração Premium"
    )

    assert isinstance(
        scores,
        dict,
    )


def test_semantic_engine_enrich_dataframe():

    df = pd.DataFrame(

        {

            "product_id": [1],

            "product_name": [

                "Ração Super Premium Frango para Filhotes"

            ],

            "brand": [

                "Premier"

            ],

            "description": [

                "Raças Pequenas"

            ],

            "category": [

                "Ração Seca"

            ],

            "ingredients": [

                "Frango"

            ],

        }

    )

    engine = SemanticEngine()

    enriched = engine.enrich_dataframe(
        df
    )

    assert len(
        enriched
    ) == 1

    assert (
        "product_category"
        in enriched.columns
    )

    assert (
        "life_stage"
        in enriched.columns
    )

    assert (
        "breed_size"
        in enriched.columns
    )

    assert (
        "protein_source"
        in enriched.columns
    )

    assert (
        "product_tier"
        in enriched.columns
    )


def test_semantic_engine_preserves_row_count():

    df = pd.DataFrame(

        {

            "product_id": [1, 2],

            "product_name": [

                "Ração Premium",

                "Ração Úmida",

            ],

        }

    )

    engine = SemanticEngine()

    enriched = engine.enrich_dataframe(
        df
    )

    assert len(
        enriched
    ) == len(df)


def test_semantic_engine_handles_empty_dataframe():

    df = pd.DataFrame()

    engine = SemanticEngine()

    enriched = engine.enrich_dataframe(
        df
    )

    assert enriched.empty


def test_semantic_engine_does_not_modify_original_dataframe():

    df = pd.DataFrame(

        {

            "product_id": [1],

            "product_name": [

                "Ração Premium"

            ],

        }

    )

    original = df.copy(
        deep=True
    )

    engine = SemanticEngine()

    engine.enrich_dataframe(
        df
    )

    pd.testing.assert_frame_equal(
        df,
        original,
    )