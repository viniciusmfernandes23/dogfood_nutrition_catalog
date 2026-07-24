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
from app.semantic.scoring import NutritionalScoring


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
        "score_macro",
        "score_micro",
        "score_amino",
        "score_lipids",
    )

    TEXT_COLUMNS = (
        "product_name",
        "brand",
        "description",
        "category",
        "ingredients",
        "indication",
        "product_line",
        "product_type",
    )

    def __init__(self) -> None:

        self.scoring = NutritionalScoring()

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

            # v1.5.2: Lógica refinada de priorização Ficha Técnica vs Semântica
            
            # 1. Product Category
            # Se vier da ficha técnica (product_category), mantemos. Caso contrário, inferimos.
            if pd.isna(df.at[index, "product_category"]) or str(df.at[index, "product_category"]).strip() == "":
                df.at[index, "product_category"] = self._enum_value(semantic["product_category"])

            # 2. Life Stage
            # Prioridade: Ficha Técnica (life_stage) -> Inferência Semântica (Nome/Indicação)
            if pd.isna(df.at[index, "life_stage"]) or str(df.at[index, "life_stage"]).strip() == "":
                df.at[index, "life_stage"] = self._enum_value(semantic["life_stage"])

            # 3. Breed Size
            if pd.isna(df.at[index, "breed_size"]) or str(df.at[index, "breed_size"]).strip() == "":
                df.at[index, "breed_size"] = self._enum_value(semantic["breed_size"])

            # 4. Product Tier
            # v1.5.3: Lógica dinâmica baseada na Ficha Técnica (Tipo da Ração / Linha)
            tier_override = None
            # Consideramos tanto product_type (Tipo da Ração) quanto product_line (Linha)
            # como fontes da verdade da ficha técnica.
            ft_sources = [
                str(row.get("product_type", "")).lower(),
                str(row.get("product_line", "")).lower()
            ]
            
            # Mapeamento dinâmico de termos da ficha técnica para categorias canônicas
            tier_map = {
                "super premium": ProductTier.SUPER_PREMIUM.value,
                "premium especial": ProductTier.PREMIUM_SPECIAL.value,
                "premium": ProductTier.PREMIUM.value,
                "standard": ProductTier.STANDARD.value,
                "econômica": ProductTier.STANDARD.value,
                "economica": ProductTier.STANDARD.value,
                "manutenção": ProductTier.STANDARD.value,
                "manutencao": ProductTier.STANDARD.value,
                "high premium": ProductTier.PREMIUM_SPECIAL.value,
            }
            
            for source_text in ft_sources:
                if not source_text or source_text == "nan":
                    continue
                # Busca o melhor match no mapeamento dinâmico
                for term, canonical in tier_map.items():
                    if term in source_text:
                        tier_override = canonical
                        break
                if tier_override:
                    break
            
            if tier_override:
                df.at[index, "product_tier"] = tier_override
            else:
                # Fallback para inferência semântica baseada no contexto geral (nome, descrição, etc)
                df.at[index, "product_tier"] = self._enum_value(
                    semantic["product_tier"],
                    ProductTier.STANDARD.value,
                )

            # 5. Clinical Category
            df.at[index, "clinical_category"] = self._enum_value(
                semantic["clinical_category"],
                ClinicalCategory.NONE.value,
            )

            # 6. Protein Source
            proteins = semantic["protein_source"]
            df.at[index, "protein_source"] = (
                ", ".join(protein.value for protein in proteins)
                if proteins else ProteinSource.UNKNOWN.value
            )

        # Adiciona scores nutricionais categorizados
        df = self.scoring.enrich_dataframe(df)

        return df