from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from app.warehouse.models import PriceSnapshotFact


class PriceSnapshotFactBuilder:
    """
    Constrói a tabela fato de preços.
    """

    def __init__(self) -> None:

        self.timestamp = datetime.now(
            UTC,
        ).replace(hour=0, minute=0, second=0, microsecond=0)

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

            fact = PriceSnapshotFact(

                product_id=row.get(
                    "product_id",
                ),

                price=row.get(
                    "price",
                ),

                available=row.get(
                    "available",
                ),

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

        if "product_id" in dataframe.columns:

            dataframe = dataframe.sort_values(
                by="product_id",
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