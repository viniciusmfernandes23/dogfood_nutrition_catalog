from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.warehouse.models import PriceSnapshotFact


class PriceSnapshotFactBuilder:
    """
    Constrói a tabela fact_price_snapshot.

    Cada linha representa um snapshot de preço
    de um produto.
    """

    def __init__(self) -> None:
        self.snapshot_date = datetime.utcnow()

    def build(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        facts: list[dict] = []

        for row in dataframe.to_dict(orient="records"):

            price = self._to_float(
                row.get("price")
            )

            subscriber_price = self._to_float(
                row.get("subscriber_price")
            )

            price_per_kg = self._to_float(
                row.get("price_per_kg")
            )

            fact = PriceSnapshotFact(

                product_id=row.get("product_id"),

                snapshot_date=self.snapshot_date,

                price=price,

                subscriber_price=subscriber_price,

                price_per_kg=price_per_kg,

                currency=row.get(
                    "currency",
                    "BRL",
                ),

                in_stock=self._to_bool(
                    row.get("in_stock")
                ),

                has_price=price is not None,

                has_price_per_kg=(
                    price_per_kg is not None
                ),

                has_subscriber_price=(
                    subscriber_price is not None
                ),

                seller=row.get(
                    "seller"
                ),

                source=row.get(
                    "source"
                ),

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
                        "snapshot_date",
                        "product_id",
                    ]
                )

                .reset_index(
                    drop=True
                )

            )

        return fact_df

    @staticmethod
    def _to_float(
        value,
    ) -> float | None:

        if value is None:
            return None

        if pd.isna(value):
            return None

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _to_bool(
        value,
    ) -> bool:

        if isinstance(
            value,
            bool,
        ):
            return value

        if value is None:
            return False

        if pd.isna(value):
            return False

        if isinstance(
            value,
            (int, float),
        ):
            return value > 0

        value = str(
            value
        ).strip().lower()

        return value in {

            "true",

            "1",

            "sim",

            "yes",

            "y",

            "disponível",

            "available",

            "in_stock",

        }

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