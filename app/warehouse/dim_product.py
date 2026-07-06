from __future__ import annotations

from datetime import datetime

import pandas as pd

from app.warehouse.models import ProductDimension


class ProductDimensionBuilder:
    """
    Constrói a dimensão de produtos (dim_product).
    """

    DEFAULT_COLUMNS = [
        "product_id",
        "sku",
        "brand",
        "manufacturer",
        "product_name",
        "product_url",
        "image_url",
        "category",
        "product_category",
        "product_tier",
        "life_stage",
        "breed_size",
        "protein_source",
        "clinical_category",
        "package_size",
        "package_unit",
    ]

    def __init__(self) -> None:
        self.timestamp = datetime.utcnow()

    def build(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        records: list[dict] = []

        for row in dataframe.to_dict(orient="records"):

            product = ProductDimension(

                product_id=row.get("product_id"),

                sku=row.get("sku"),

                brand=row.get("brand"),

                manufacturer=row.get("manufacturer"),

                product_name=row.get("product_name"),

                product_url=row.get("product_url"),

                image_url=row.get("image_url"),

                category=row.get("category"),

                product_category=row.get("product_category"),

                product_tier=row.get("product_tier"),

                life_stage=row.get("life_stage"),

                breed_size=row.get("breed_size"),

                protein_source=row.get("protein_source"),

                clinical_category=row.get("clinical_category"),

                package_size=row.get("package_size"),

                package_unit=row.get("package_unit"),

                has_guarantee_levels=self._has_guarantee_levels(
                    row,
                ),

                created_at=self.timestamp,

                updated_at=self.timestamp,

            )

            records.append(
                product.to_dict()
            )

        dim = pd.DataFrame(records)

        dim = self._remove_duplicates(dim)

        dim = self._sort(dim)

        return dim

    @staticmethod
    def _has_guarantee_levels(
        row: dict,
    ) -> bool:

        nutrient_columns = [

            column

            for column in row.keys()

            if column.endswith("_gkg")
            or column.endswith("_mgkg")
            or column.endswith("_uikg")

        ]

        for column in nutrient_columns:

            value = row.get(column)

            if pd.notna(value):

                return True

        return False

    @staticmethod
    def _remove_duplicates(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        if "product_id" not in dataframe.columns:

            return dataframe

        return (

            dataframe

            .sort_values("product_id")

            .drop_duplicates(
                subset=["product_id"],
                keep="last",
            )

            .reset_index(drop=True)

        )

    @staticmethod
    def _sort(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        if "product_name" in dataframe.columns:

            dataframe = dataframe.sort_values(
                by=[
                    "brand",
                    "product_name",
                ],
                na_position="last",
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