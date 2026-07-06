from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.semantic.engine import SemanticEngine
from app.warehouse.dim_product import ProductDimensionBuilder
from app.warehouse.exporter import WarehouseExporter
from app.warehouse.fact_nutrient import NutrientFactBuilder
from app.warehouse.fact_price_snapshot import (
    PriceSnapshotFactBuilder,
)


class WarehousePipeline:
    """
    Pipeline responsável pela geração do
    Data Warehouse analítico.

    Fluxo:

        DataFrame
            ↓
        Semantic Engine
            ↓
        dim_product
        fact_nutrient
        fact_price_snapshot
            ↓
        CSV
    """

    def __init__(
        self,
        output_dir: str = "data/output/warehouse",
    ) -> None:

        self.semantic_engine = SemanticEngine()

        self.dim_builder = ProductDimensionBuilder()

        self.nutrient_builder = NutrientFactBuilder()

        self.price_builder = (
            PriceSnapshotFactBuilder()
        )

        self.exporter = WarehouseExporter(
            output_dir=output_dir,
        )

    def run(
        self,
        dataframe: pd.DataFrame,
    ) -> dict[str, pd.DataFrame]:
        """
        Executa todo o pipeline.

        Retorna todas as tabelas geradas.
        """

        enriched = self.semantic_engine.enrich_dataframe(
            dataframe,
        )

        dim_product = self.dim_builder.build(
            enriched,
        )

        fact_nutrient = (
            self.nutrient_builder.build(
                enriched,
            )
        )

        fact_price_snapshot = (
            self.price_builder.build(
                enriched,
            )
        )

        self.exporter.export_all(

            dim_product=dim_product,

            fact_nutrient=fact_nutrient,

            fact_price_snapshot=fact_price_snapshot,

        )

        return {

            "dim_product": dim_product,

            "fact_nutrient": fact_nutrient,

            "fact_price_snapshot": fact_price_snapshot,

        }

    def run_from_csv(
        self,
        input_file: str | Path,
    ) -> dict[str, pd.DataFrame]:
        """
        Executa o pipeline a partir
        de um CSV.
        """

        dataframe = pd.read_csv(
            input_file,
            low_memory=False,
        )

        return self.run(
            dataframe,
        )

    def run_from_parquet(
        self,
        input_file: str | Path,
    ) -> dict[str, pd.DataFrame]:
        """
        Executa o pipeline a partir
        de um arquivo Parquet.
        """

        dataframe = pd.read_parquet(
            input_file,
        )

        return self.run(
            dataframe,
        )

    def clean_output(self) -> None:
        """
        Remove todos os arquivos
        anteriormente exportados.
        """

        self.exporter.clean_output_directory()


if __name__ == "__main__":

    INPUT_FILE = (
        "data/output/clean/"
        "nutrition_clean.parquet"
    )

    pipeline = WarehousePipeline()

    pipeline.clean_output()

    tables = pipeline.run_from_parquet(
        INPUT_FILE,
    )

    print()

    print("=" * 60)
    print("DATA WAREHOUSE GERADO COM SUCESSO")
    print("=" * 60)

    for name, table in tables.items():

        print(
            f"{name:<25} "
            f"{len(table):>8} registros"
        )

    print()
    print(
        "Arquivos exportados para:"
    )
    print(
        "data/output/warehouse/"
    )