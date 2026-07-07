from __future__ import annotations

import pandas as pd

from app.semantic.categories import (
    ClinicalCategory,
    ProductTier,
    ProteinSource,
)
from app.semantic.classifier import SemanticClassifier
from app.semantic.rules import (
    BREED_SIZE_RULES,
    CLINICAL_RULES,
    LIFESTAGE_RULES,
    PRODUCT_CATEGORY_RULES,
    PRODUCT_TIER_RULES,
    PROTEIN_RULES,
)


class SemanticEngine:
    """
    Enriquecimento semântico do catálogo de produtos.
    """

    OUTPUT_COLUMNS = (
        "product_category",
        "life_stage",
        "breed_size",
        "clinical_category",
        "protein_source",
        "product_tier",
    )

    TEXT_COLUMNS = (
        "product_name",
        "brand",
        "description",
        "category",
        "ingredients",
    )

    def __init__(self) -> None:

        self.product_classifier = SemanticClassifier(
            PRODUCT_CATEGORY_RULES,
        )

        self.life_stage_classifier = SemanticClassifier(
            LIFESTAGE_RULES,
        )

        self.breed_classifier = SemanticClassifier(
            BREED_SIZE_RULES,
        )

        self.clinical_classifier = SemanticClassifier(
            CLINICAL_RULES,
        )

        self.protein_classifier = SemanticClassifier(
            PROTEIN_RULES,
        )

        self.tier_classifier = SemanticClassifier(
            PRODUCT_TIER_RULES,
        )

    # ==========================================================
    # Helpers
    # ==========================================================

    @classmethod
    def _build_text(
        cls,
        row: pd.Series,
    ) -> str:

        return " ".join(

            str(
                row.get(
                    column,
                    "",
                )
            )

            for column

            in cls.TEXT_COLUMNS

            if pd.notna(
                row.get(
                    column,
                )
            )

        )

    @staticmethod
    def _enum_value(
        value,
        default: str | None = None,
    ) -> str | None:

        if value is None:
            return default

        return value.value

    # ==========================================================
    # Classificação
    # ==========================================================

    def classify_product(
        self,
        row: pd.Series,
    ) -> dict[str, object]:

        text = self._build_text(
            row,
        )

        return {

            "product_category":
                self.product_classifier.best_match(
                    text,
                ),

            "life_stage":
                self.life_stage_classifier.best_match(
                    text,
                ),

            "breed_size":
                self.breed_classifier.best_match(
                    text,
                ),

            "clinical_category":
                self.clinical_classifier.best_match(
                    text,
                ),

            "protein_source":
                self.protein_classifier.classify_many(
                    text,
                ),

            "product_tier":
                self.tier_classifier.best_match(
                    text,
                ),

        }

    # ==========================================================
    # DataFrame
    # ==========================================================

    def enrich_dataframe(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df = df.copy()

        for column in self.OUTPUT_COLUMNS:
            if column not in df.columns:
                df[column] = None

        for index, row in df.iterrows():

            semantic = self.classify_product(
                row,
            )

            df.at[
                index,
                "product_category",
            ] = self._enum_value(
                semantic["product_category"],
            )

            df.at[
                index,
                "life_stage",
            ] = self._enum_value(
                semantic["life_stage"],
            )

            df.at[
                index,
                "breed_size",
            ] = self._enum_value(
                semantic["breed_size"],
            )

            df.at[
                index,
                "clinical_category",
            ] = self._enum_value(
                semantic["clinical_category"],
                ClinicalCategory.NONE.value,
            )

            proteins = semantic["protein_source"]

            df.at[
                index,
                "protein_source",
            ] = (
                ", ".join(
                    protein.value
                    for protein in proteins
                )
                if proteins
                else ProteinSource.UNKNOWN.value
            )

            df.at[
                index,
                "product_tier",
            ] = self._enum_value(
                semantic["product_tier"],
                ProductTier.STANDARD.value,
            )

        return df