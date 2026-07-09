from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from app.warehouse.models import NutrientFact


class NutrientFactBuilder:
    """
    Constrói a tabela fato de nutrientes.
    """

    NUTRIENT_COLUMNS = (
        "protein_gkg",
        "fat_gkg",
        "fiber_gkg",
        "ash_gkg",
        "moisture_gkg",
        "calcium_min_mgkg",
        "calcium_max_mgkg",
        "phosphorus_mgkg",
        "sodium_mgkg",
        "potassium_mgkg",
        "metabolizable_energy_kcalkg",
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