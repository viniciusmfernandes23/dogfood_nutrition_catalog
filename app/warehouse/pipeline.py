from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.warehouse.dim_product import ProductDimensionBuilder
from app.warehouse.exporter import WarehouseExporter
from app.warehouse.fact_nutrient import NutrientFactBuilder
from app.warehouse.fact_price_snapshot import (
    PriceSnapshotFactBuilder,
)


class WarehousePipeline:
    """
    Pipeline responsável pela construção e exportação
    do Data Warehouse.
    """

    def __init__(
        self,
        output_dir: str = "data/output/warehouse",
    ) -> None:

        self.dim_builder = ProductDimensionBuilder()

        self.nutrient_builder = NutrientFactBuilder()

        self.price_builder = PriceSnapshotFactBuilder()

        self.exporter = WarehouseExporter(
            output_dir=output_dir,
        )

    # ==========================================================
    # Build
    # ==========================================================

    def build(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, pd.DataFrame]:

        return {

            "dim_product":
                self.dim_builder.build(
                    dataframe,
                ),

            "fact_nutrient":
                self.nutrient_builder.build(
                    dataframe,
                ),

            "fact_price_snapshot":
                self.price_builder.build(
                    dataframe,
                ),

        }

    # ==========================================================
    # Export
    # ==========================================================

    def export(
        self,
        tables: dict[str, pd.DataFrame],
    ) -> dict[str, Path]:

        return self.exporter.export_all(

            dim_product=tables["dim_product"],

            fact_nutrient=tables["fact_nutrient"],

            fact_price_snapshot=tables[
                "fact_price_snapshot"
            ],

        )

    # ==========================================================
    # Run
    # ==========================================================

    def run(
        self,
        dataframe: pd.DataFrame,
    ) -> tuple[
        dict[str, pd.DataFrame],
        dict[str, Path],
    ]:

        tables = self.build(
            dataframe,
        )

        exported = self.export(
            tables,
        )

        return (

            tables,

            exported,

        )

    # ==========================================================
    # Utilidades
    # ==========================================================

    def clean(
        self,
    ) -> None:

        self.exporter.clean_output_directory()

    def list_exports(
        self,
    ) -> list[Path]:

        return self.exporter.list_exported_files()

    def metadata_exists(
        self,
    ) -> bool:

        return self.exporter.file_exists(
            "warehouse_metadata.json",
        )