"""
NutritionExtractionService — Serviço de extração nutricional.

Responsável por:
  1. Executar o crawler para obter o HTML da seção de garantia.
  2. Fazer o parse nutricional.
  3. Mapear nutrientes para colunas canônicas.
  4. Selecionar o melhor match por prioridade.
"""

from __future__ import annotations

import pandas as pd

from app.core.logging import logger
from app.normalization.rules import NORMALIZATION_RULES
from app.parsers.nutrition_parser import parse_nutrition


# Mapeamento de nutrientes → colunas canônicas do DataFrame
NUTRIENT_MAPPING: dict[str, str] = {
    "protein": "protein_gkg",
    "fat": "fat_gkg",
    "fiber": "fiber_gkg",
    "ash": "ash_gkg",
    "moisture": "moisture_gkg",
    "calcium_min": "calcium_min_mgkg",
    "calcium_max": "calcium_max_mgkg",
    "metabolizable_energy": "metabolizable_energy_kcalkg",
}

# Complementa com chaves das NORMALIZATION_RULES
for rule_key in NORMALIZATION_RULES.keys():
    short = rule_key.split("_")[0]
    if short not in NUTRIENT_MAPPING and short + "_gkg" == rule_key:
        NUTRIENT_MAPPING[short] = rule_key


class NutritionExtractionService:
    """
    Extrai nutrientes dos dados brutos de garantia e os mapeia
    para colunas canônicas no DataFrame.
    """

    def __init__(self) -> None:
        pass

    def extract_and_map(
        self,
        dataframe: pd.DataFrame,
        guarantee_column: str = "raw_guarantee",
    ) -> pd.DataFrame:
        """
        Para cada linha do DataFrame, faz o parse da coluna de garantia
        e escreve os nutrientes nas colunas canônicas.

        Retorna o DataFrame modificado com as colunas de nutrientes preenchidas.
        """
        logger.info(
            "Processando %d produtos para extração de nutrientes...",
            len(dataframe),
        )

        nutrient_cols = list(NUTRIENT_MAPPING.values())

        # Garante que as colunas canônicas existam
        for col in nutrient_cols:
            if col not in dataframe.columns:
                dataframe[col] = None
            # Garante também a coluna de unidade original
            unit_col = f"{col}_unit"
            if unit_col not in dataframe.columns:
                dataframe[unit_col] = None

        for index, row in dataframe.iterrows():
            raw_guarantee = row.get(guarantee_column)
            if not raw_guarantee or (isinstance(raw_guarantee, float) and pd.isna(raw_guarantee)):
                continue

            nutrients = parse_nutrition(raw_guarantee)
            logger.info(
                "  Nutrientes brutos para %s: %d",
                row.get("product_name", "?"),
                len(nutrients),
            )

            best_matches = self._select_best(nutrients)

            for target_col, data in best_matches.items():
                dataframe.at[index, target_col] = data["value"]
                unit_col = f"{target_col}_unit"
                dataframe.at[index, unit_col] = data.get("unit")

        return dataframe

    def _select_best(
        self, nutrients: dict
    ) -> dict[str, dict]:
        """
        Seleciona o melhor match para cada nutriente canônico,
        priorizando valores com 'mín' ou 'máx' no alias.
        """
        best_matches: dict[str, dict] = {}

        for _nut_key, nut_data in nutrients.items():
            nut_type = nut_data["nutrient"]
            target_col = NUTRIENT_MAPPING.get(nut_type)
            if not target_col:
                continue

            alias = nut_data.get("matched_alias", "").lower()
            priority = 2 if any(x in alias for x in ["mín", "min", "máx", "max"]) else 1

            if (
                target_col not in best_matches
                or priority > best_matches[target_col]["priority"]
            ):
                best_matches[target_col] = {
                    "value": nut_data["value"],
                    "unit": nut_data.get("unit"),
                    "priority": priority,
                }

        return best_matches
