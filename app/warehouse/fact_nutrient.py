from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from app.warehouse.models import NutrientFact


class NutrientFactBuilder:
    """
    Constrói a tabela fato de nutrientes.
    """

    NUTRIENT_COLUMNS = (
        # Macronutrientes
        "protein_gkg",
        "fat_gkg",
        "fiber_gkg",
        "ash_gkg",
        "moisture_gkg",
        
        # Minerais
        "calcium_min_mgkg",
        "calcium_max_mgkg",
        "phosphorus_mgkg",
        "sodium_mgkg",
        "potassium_mgkg",
        "magnesium_mgkg",
        "chlorine_mgkg",
        "iron_mgkg",
        "zinc_mgkg",
        "copper_mgkg",
        "selenium_mgkg",
        "iodine_mgkg",
        "manganese_mgkg",

        # Aminoácidos
        "lysine_mgkg",
        "methionine_mgkg",
        "tryptophan_mgkg",
        "arginine_mgkg",
        "taurine_mgkg",
        "l_carnitine_mgkg",

        # Ácidos Graxos
        "omega_3_mgkg",
        "omega_6_mgkg",
        "epa_dha_mgkg",

        # Vitaminas
        "vitamin_a_uikg",
        "vitamin_d3_uikg",
        "vitamin_e_uikg",
        "vitamin_b1_mgkg",
        "vitamin_b2_mgkg",
        "vitamin_b6_mgkg",
        "vitamin_b12_mgkg",
        "niacin_mgkg",
        "pantothenic_acid_mgkg",
        "folic_acid_mgkg",
        "biotin_mgkg",
        "choline_mgkg",
        "vitamin_c_mgkg",
        "vitamin_k3_mgkg",

        # Energia
        "metabolizable_energy_kcalkg",

        # Outros
        "beta_glucans_mgkg",
        "mos_mgkg",
    )

    def __init__(
        self,
        timestamp: datetime | None = None,
    ) -> None:

        self.timestamp = timestamp or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def build(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        if dataframe.empty:

            return pd.DataFrame()

        records: list[dict] = []

        for row in dataframe.to_dict(
            orient="records",
        ):

            product_id = row.get(
                "product_id",
            )

            for nutrient in self.NUTRIENT_COLUMNS:

                if nutrient not in row:
                    continue

                value = row.get(
                    nutrient,
                )

                if pd.isna(value):
                    continue

                fact = NutrientFact(

                    product_id=product_id,

                    nutrient_name=nutrient,

                    nutrient_value=float(value),

                    collected_at=self.timestamp,

                )

                records.append(
                    fact.to_dict(),
                )

        fact_df = pd.DataFrame(
            records,
        )

        return self._sort(
            fact_df,
        )

    @staticmethod
    def _sort(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        if dataframe.empty:

            return dataframe

        columns = [

            column

            for column

            in (
                "product_id",
                "nutrient_name",
            )

            if column in dataframe.columns

        ]

        if columns:

            dataframe = dataframe.sort_values(
                by=columns,
            )

        return dataframe.reset_index(
            drop=True,
        )

    @staticmethod
    def export_csv(
        dataframe: pd.DataFrame,
        output_path: str,
    ) -> None:

        dataframe.to_csv(

            output_path,

            index=False,

            encoding="utf-8-sig",

        )