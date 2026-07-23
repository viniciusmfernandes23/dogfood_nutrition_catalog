from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from app.warehouse.models import ProductDimension


class ProductDimensionBuilder:
    """
    Constrói a dimensão de produtos (dim_product).
    """

    DEFAULT_COLUMNS = (
        "product_id",
        "brand",
        "product_name",
        "product_url",
        "product_category",
        "product_tier",
        "life_stage",
        "breed_size",
        "protein_source",
        "clinical_category",
        "product_type",
        "package_weight",
        "contains_coloring",
        "target_breeds",
        "indication",
        "product_line",
        "is_transgenic",
        "gender",
        "image_url",
    )

    NUTRIENT_SUFFIXES = (
        "_gkg",
        "_mgkg",
        "_uikg",
        "_kcalkg",
    )

    def __init__(
        self,
        timestamp: datetime | None = None,
    ) -> None:

        self.timestamp = timestamp or datetime.now()

    def build(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        if dataframe.empty:

            return pd.DataFrame()

        records = [

            ProductDimension(

                product_id=row.get("product_id"),

                brand=row.get("brand"),

                product_name=row.get("product_name"),

                # Remapeamento: a coleta produz 'url', a dimensão espera 'product_url'
                product_url=row.get("product_url") or row.get("url"),

                product_category=row.get("product_category"),

                product_tier=row.get("product_tier"),

                life_stage=row.get("life_stage"),

                breed_size=row.get("breed_size"),

                protein_source=row.get("protein_source"),

                clinical_category=row.get("clinical_category"),
                
                # v1.4.0: Mapeamento da Ficha Técnica
                product_type=row.get("product_type"),
                package_weight=row.get("package_weight"),
                contains_coloring=row.get("contains_coloring"),
                target_breeds=row.get("target_breeds"),
                indication=row.get("indication"),
                product_line=row.get("product_line"),
                is_transgenic=row.get("is_transgenic"),
                gender=row.get("gender"),
                image_url=row.get("image_url"),

                has_guarantee_levels=self._has_guarantee_levels(
                    row,
                ),

                created_at=self.timestamp,

                updated_at=self.timestamp,

            ).to_dict()

            for row

            in dataframe.to_dict(
                orient="records",
            )

        ]

        dim = pd.DataFrame(
            records,
        )

        dim = self._remove_duplicates(
            dim,
        )

        dim = self._sort(
            dim,
        )

        return dim

    @classmethod
    def _has_guarantee_levels(
        cls,
        row: dict,
    ) -> bool:

        return any(

            pd.notna(value)

            for column, value

            in row.items()

            if column.endswith(
                cls.NUTRIENT_SUFFIXES,
            )

        )

    @staticmethod
    def _remove_duplicates(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        if (
            dataframe.empty
            or "product_id"
            not in dataframe.columns
        ):

            return dataframe

        return (

            dataframe

            .drop_duplicates(
                subset="product_id",
                keep="last",
            )

            .reset_index(
                drop=True,
            )

        )

    @staticmethod
    def _sort(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:

        columns = [

            column

            for column

            in (
                "brand",
                "product_name",
            )

            if column in dataframe.columns

        ]

        if columns:

            dataframe = dataframe.sort_values(

                by=columns,

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