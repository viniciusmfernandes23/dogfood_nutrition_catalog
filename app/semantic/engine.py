from __future__ import annotations

import pandas as pd

from app.semantic.categories import (
    ClinicalCategory,
    ProductTier,
    ProteinSource,
    ProductCategory,
    LifeStage,
    BreedSize,
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
        "product_type",
        "target_breeds",
        "product_line",
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

        from app.semantic.rules import SEMANTIC_RULES
        self.product_classifier = SemanticClassifier(
            SEMANTIC_RULES["product_category"],
        )

        self.life_stage_classifier = SemanticClassifier(
            SEMANTIC_RULES["life_stage"],
        )

        self.breed_classifier = SemanticClassifier(
            SEMANTIC_RULES["breed_size"],
        )

        self.clinical_classifier = SemanticClassifier(
            SEMANTIC_RULES["clinical_category"],
        )

        self.protein_classifier = SemanticClassifier(
            SEMANTIC_RULES["protein_source"],
        )

        self.tier_classifier = SemanticClassifier(
            SEMANTIC_RULES["product_tier"],
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

        if isinstance(value, str):
            return value

        return value.value if hasattr(value, 'value') else str(value)

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

        for index, _ in df.iterrows():
            row = df.loc[index]
            # v1.5.7: Garantimos que o texto de entrada para o classificador seja completo
            text_context = self._build_text(row)
            
            # Recalculamos semantic para garantir que os classificadores usem o contexto completo
            semantic = {
                "product_category": self.product_classifier.classify(text_context),
                "life_stage": self.life_stage_classifier.classify(text_context),
                "breed_size": self.breed_classifier.classify(text_context),
                "clinical_category": self.clinical_classifier.classify(text_context),
                "protein_source": self.protein_classifier.classify_many(text_context),
                "product_tier": self.tier_classifier.classify(text_context),
            }

            # v1.5.2: Lógica refinada de priorização Ficha Técnica vs Semântica
            
            # 1. Product Category
            if pd.isna(df.loc[index, "product_category"]) or str(df.loc[index, "product_category"]).strip() in ["", "nan", "None"]:
                df.loc[index, "product_category"] = self._enum_value(semantic["product_category"])

            # 2. Life Stage
            if pd.isna(df.loc[index, "life_stage"]) or str(df.loc[index, "life_stage"]).strip() in ["", "nan", "None"]:
                # Prioriza match no nome
                name_match = self.life_stage_classifier.best_match(str(row.get("product_name", "")))
                df.loc[index, "life_stage"] = self._enum_value(name_match) if name_match else self._enum_value(semantic["life_stage"])

            # 3. Breed Size
            if pd.isna(df.loc[index, "breed_size"]) or str(df.loc[index, "breed_size"]).strip() in ["", "nan", "None"]:
                df.loc[index, "breed_size"] = self._enum_value(semantic["breed_size"])

            # 3.1 Product Type
            if pd.isna(df.loc[index, "product_type"]) or str(df.loc[index, "product_type"]).strip() in ["", "nan", "None"]:
                df.loc[index, "product_type"] = self._enum_value(semantic["product_category"])

            # 3.2 Target Breeds (v1.5.7: Heurística baseada no nome se vazio)
            if pd.isna(df.loc[index, "target_breeds"]) or str(df.loc[index, "target_breeds"]).strip() == "" or str(df.loc[index, "target_breeds"]).lower() == "nan":
                # Se o nome contiver "Todas as Raças" ou for genérico, preenchemos
                name_norm = str(row.get("product_name", "")).lower()
                if "todas as racas" in name_norm or "racas pequenas e medias" in name_norm:
                    df.loc[index, "target_breeds"] = "Todas as Raças"
                elif "especifica" not in name_norm:
                    # Se não for uma raça específica no nome, tendemos a colocar Todas as Raças como heurística
                    df.loc[index, "target_breeds"] = "Todas as Raças"

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
                df.loc[index, "product_tier"] = tier_override
            else:
                # Fallback para inferência semântica baseada no contexto geral (nome, descrição, etc)
                df.loc[index, "product_tier"] = self._enum_value(
                    semantic["product_tier"],
                    ProductTier.STANDARD.value,
                )

            # 5. Clinical Category
            df.loc[index, "clinical_category"] = self._enum_value(
                semantic["clinical_category"],
                ClinicalCategory.NONE.value,
            )

            # 6. Protein Source
            proteins = semantic["protein_source"]
            df.loc[index, "protein_source"] = (
                ", ".join(protein.value for protein in proteins)
                if proteins else ProteinSource.UNKNOWN.value
            )

        # Adiciona scores nutricionais categorizados
        df = self.scoring.enrich_dataframe(df)

        return df