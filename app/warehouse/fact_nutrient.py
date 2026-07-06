from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.warehouse.models import NutrientFact


class NutrientFactBuilder:
    """
    Constrói a tabela fact_nutrient.

    Cada linha representa um nutriente de um produto.
    """

    NUTRIENT_COLUMNS = {
        "protein_gkg": "protein",
        "fat_gkg": "fat",
        "fiber_gkg": "fiber",
        "ash_gkg": "ash",
        "moisture_gkg": "moisture",
        "calcium_min_mgkg": "calcium_min",
        "calcium_max_mgkg": "calcium_max",
        "phosphorus_mgkg": "phosphorus",
        "sodium_mgkg": "sodium",
        "potassium_mgkg": "potassium",
    }

    def __init__(self) -> None:
        self.snapshot_date = datetime.utcnow()

    def build(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        facts: list[dict] = []

        for row in dataframe.to_dict(orient="records"):

            product_id = row.get("product_id")

            for column, nutrient in self.NUTRIENT_COLUMNS.items():

                if column not in row:
                    continue

                value = row.get(column)

                if pd.isna(value):
                    continue

                unit = self._infer_unit(column)

                fact = NutrientFact(

                    product_id=product_id,

                    nutrient=nutrient,

                    value=float(value),

                    unit=unit,

                    normalization_status=row.get(
                        f"{column}_status"
                    ),

                    rule_applied=row.get(
                        f"{column}_rule"
                    ),

                    confidence=row.get(
                        f"{column}_confidence"
                    ),

                    snapshot_date=self.snapshot_date,

                )

                facts.append(
                    fact.to_dict()
                )

        fact_df = pd.DataFrame(facts)

        if not fact_df.empty:

            fact_df = (

                fact_df

                .sort_values(
                    by=[
                        "product_id",
                        "nutrient",
                    ]
                )

                .reset_index(
                    drop=True
                )

            )

        return fact_df

    @staticmethod
    def _infer_unit(
        column: str,
    ) -> str:

        if column.endswith("_gkg"):
            return "g/kg"

        if column.endswith("_mgkg"):
            return "mg/kg"

        if column.endswith("_uikg"):
            return "UI/kg"

        return ""

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