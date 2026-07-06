from __future__ import annotations

import pandas as pd

from app.semantic.categories import (
    BreedSize,
    ClinicalCategory,
    LifeStage,
    ProductCategory,
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
    Responsável por enriquecer semanticamente
    o catálogo de produtos.
    """

    def __init__(self) -> None:

        self.product_classifier = SemanticClassifier(
            PRODUCT_CATEGORY_RULES
        )

        self.life_stage_classifier = SemanticClassifier(
            LIFESTAGE_RULES
        )

        self.breed_classifier = SemanticClassifier(
            BREED_SIZE_RULES
        )

        self.clinical_classifier = SemanticClassifier(
            CLINICAL_RULES
        )

        self.protein_classifier = SemanticClassifier(
            PROTEIN_RULES
        )

        self.tier_classifier = SemanticClassifier(
            PRODUCT_TIER_RULES
        )

    @staticmethod
    def _build_text(row: pd.Series) -> str:

        values = [

            str(row.get("product_name", "")),

            str(row.get("brand", "")),

            str(row.get("description", "")),

            str(row.get("category", "")),

            str(row.get("ingredients", "")),

        ]

        return " ".join(values)

    def classify_product(
        self,
        row: pd.Series,
    ) -> dict:

        text = self._build_text(row)

        return {

            "product_category":

                self.product_classifier.best_match(text),

            "life_stage":

                self.life_stage_classifier.best_match(text),

            "breed_size":

                self.breed_classifier.best_match(text),

            "clinical_category":

                self.clinical_classifier.best_match(text),

            "protein_source":

                self.protein_classifier.classify_many(text),

            "product_tier":

                self.tier_classifier.best_match(text),

        }

    def enrich_dataframe(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        df = df.copy()

        df["product_category"] = None

        df["life_stage"] = None

        df["breed_size"] = None

        df["clinical_category"] = None

        df["protein_source"] = None

        df["product_tier"] = None

        for index, row in df.iterrows():

            semantic = self.classify_product(row)

            df.at[
                index,
                "product_category"
            ] = (
                semantic["product_category"].value
                if semantic["product_category"]
                else None
            )

            df.at[
                index,
                "life_stage"
            ] = (
                semantic["life_stage"].value
                if semantic["life_stage"]
                else None
            )

            df.at[
                index,
                "breed_size"
            ] = (
                semantic["breed_size"].value
                if semantic["breed_size"]
                else None
            )

            df.at[
                index,
                "clinical_category"
            ] = (
                semantic["clinical_category"].value
                if semantic["clinical_category"]
                else ClinicalCategory.NONE.value
            )

            proteins = semantic["protein_source"]

            df.at[
                index,
                "protein_source"
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
                "product_tier"
            ] = (
                semantic["product_tier"].value
                if semantic["product_tier"]
                else ProductTier.STANDARD.value
            )

        return df