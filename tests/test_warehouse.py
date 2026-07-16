from __future__ import annotations

from pathlib import Path
import pandas as pd
import pytest

from app.warehouse.dim_product import (
    ProductDimensionBuilder,
)
from app.warehouse.exporter import (
    WarehouseExporter,
)
from app.warehouse.fact_nutrient import (
    NutrientFactBuilder,
)
from app.warehouse.fact_price_snapshot import (
    PriceSnapshotFactBuilder,
)
from app.warehouse.pipeline import (
    WarehousePipeline,
)


def sample_dataframe() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "product_id": [1],
            "brand": ["Premier"],
            "manufacturer": ["Premier Pet"],
            "product_name": ["Ração Super Premium Frango"],
            "product_url": ["https://example.com"],
            "image_url": ["https://example.com/image.jpg"],
            "category": ["Ração Seca"],
            "product_category": ["Ração Seca"],
            "product_tier": ["Super Premium"],
            "life_stage": ["Adulto"],
            "breed_size": ["Pequeno"],
            "protein_source": ["Frango"],
            "clinical_category": ["Nenhuma"],
            "package_size": [15],
            "package_unit": ["kg"],
            "protein_gkg": [260],
            "fat_gkg": [150],
            "price": [249.90],
            "subscriber_price": [229.90],
            "price_per_kg": [16.66],
            "currency": ["BRL"],
            "in_stock": [True],
            "seller": ["Cobasi"],
            "source": ["crawler"],
            "marketplace": ["Cobasi"],
            # Variações de SKU com preços por embalagem (multi-variação)
            "sku_variations": [[
                {
                    "sku_id": "SKU001A",
                    "sku_name": "Ração Super Premium Frango 10kg",
                    "package_weight_kg": 10.0,
                    "price": 179.90,
                    "list_price": 199.90,
                    "subscriber_price": 161.91,
                    "price_per_kg": 17.99,
                    "available": True,
                    "marketplace": "Cobasi",
                    "ean": "7890000000001"
                },
                {
                    "sku_id": "SKU001B",
                    "sku_name": "Ração Super Premium Frango 15kg",
                    "package_weight_kg": 15.0,
                    "price": 249.90,
                    "list_price": 279.90,
                    "subscriber_price": 224.91,
                    "price_per_kg": 16.66,
                    "available": True,
                    "marketplace": "Cobasi",
                    "ean": "7890000000002"
                },
            ]],
        }
    )


def test_build_dim_product():

    builder = ProductDimensionBuilder()

    dim = builder.build(
        sample_dataframe()
    )

    assert len(dim) == 1

    assert (
        "product_id"
        in dim.columns
    )

    assert (
        "product_name"
        in dim.columns
    )


def test_build_fact_nutrient():

    builder = NutrientFactBuilder()

    fact = builder.build(
        sample_dataframe()
    )

    assert len(fact) >= 2

    # Correção: O builder usa 'nutrient_name' e não 'nutrient'
    assert (
        "nutrient_name"
        in fact.columns
    )

    assert (
        "nutrient_value"
        in fact.columns
    )


def test_build_fact_price_snapshot():

    builder = (
        PriceSnapshotFactBuilder()
    )

    fact = builder.build(
        sample_dataframe()
    )

    # Com 2 variações de SKU no sample_dataframe, espera-se 2 linhas
    assert len(fact) == 2

    assert (
        "price"
        in fact.columns
    )

    assert (
        "price_per_kg"
        in fact.columns
    )

    assert (
        "sku_id"
        in fact.columns
    )

    assert (
        "sku_name"
        in fact.columns
    )


def test_exporter_exports_csvs(
    tmp_path: Path,
):

    exporter = WarehouseExporter(
        output_dir=tmp_path,
    )

    df = sample_dataframe()

    exporter.export_dimension(
        df,
        "dim_product.csv",
    )

    exporter.export_fact(
        df,
        "fact_price_snapshot.csv",
    )

    assert (
        tmp_path
        / "dim_product.csv"
    ).exists()

    assert (
        tmp_path
        / "fact_price_snapshot.csv"
    ).exists()


def test_export_all(
    tmp_path: Path,
):

    exporter = WarehouseExporter(
        output_dir=tmp_path,
    )

    df = sample_dataframe()

    # Prepara DataFrames de fato corretos para o export_all
    fact_nutrient = NutrientFactBuilder().build(df)
    fact_price = PriceSnapshotFactBuilder().build(df)

    exporter.export_all(
        dim_product=df,
        fact_nutrient=fact_nutrient,
        fact_price_snapshot=fact_price,
    )

    assert (
        tmp_path
        / "dim_product.csv"
    ).exists()

    assert (
        tmp_path
        / "fact_nutrient.csv"
    ).exists()

    assert (
        tmp_path
        / "fact_price_snapshot.csv"
    ).exists()

    assert (
        tmp_path
        / "warehouse_metadata.json"
    ).exists()


def test_export_fact_creates_csv_for_empty_dataframe(
    tmp_path: Path,
):

    exporter = WarehouseExporter(
        output_dir=tmp_path,
    )

    empty_df = pd.DataFrame(
        columns=[
            "product_id",
            "nutrient_name",
            "nutrient_value",
            "collected_at",
        ]
    )

    output_path = exporter.export_fact(
        empty_df,
        "fact_nutrient.csv",
    )

    assert output_path.exists()
    assert "nutrient_name" in output_path.read_text(
        encoding="utf-8-sig"
    )


def test_pipeline_builds_tables(
    tmp_path: Path,
):

    pipeline = WarehousePipeline(
        output_dir=tmp_path,
    )

    # Correção: pipeline.run retorna uma tupla (tables, exported)
    tables, exported = pipeline.run(
        sample_dataframe()
    )

    assert (
        "dim_product"
        in tables
    )

    assert (
        "fact_nutrient"
        in tables
    )

    assert (
        "fact_price_snapshot"
        in tables
    )


def test_pipeline_exports_files(
    tmp_path: Path,
):

    pipeline = WarehousePipeline(
        output_dir=tmp_path,
    )

    pipeline.run(
        sample_dataframe()
    )

    assert (
        tmp_path
        / "dim_product.csv"
    ).exists()

    assert (
        tmp_path
        / "fact_nutrient.csv"
    ).exists()

    assert (
        tmp_path
        / "fact_price_snapshot.csv"
    ).exists()


def test_pipeline_preserves_product():

    pipeline = WarehousePipeline()

    # Correção: pipeline.run retorna uma tupla
    tables, exported = pipeline.run(
        sample_dataframe()
    )

    dim = tables[
        "dim_product"
    ]

    assert (
        str(dim.iloc[0]["product_id"])
        == "1"
    )


def test_fact_nutrient_contains_protein():

    builder = NutrientFactBuilder()

    fact = builder.build(
        sample_dataframe()
    )

    # Correção: O nome da coluna é 'nutrient_name' e o valor contém 'protein_gkg'
    assert (
        "protein_gkg"
        in fact["nutrient_name"].values
    )


def test_fact_price_has_price_flags():

    builder = (
        PriceSnapshotFactBuilder()
    )

    fact = builder.build(
        sample_dataframe()
    )

    # Verifica flags em todas as variações
    for _, row in fact.iterrows():

        assert row["has_price"]

        assert row[
            "has_price_per_kg"
        ]

        assert row[
            "has_subscriber_price"
        ]


def test_exporter_lists_csvs(
    tmp_path: Path,
):

    exporter = WarehouseExporter(
        output_dir=tmp_path,
    )

    df = sample_dataframe()

    exporter.export_dimension(
        df,
        "dim_product.csv",
    )

    exporter.export_fact(
        df,
        "fact_price_snapshot.csv",
    )

    files = (
        exporter.list_exported_files()
    )

    assert len(files) >= 2


def test_clean_output_directory(
    tmp_path: Path,
):

    exporter = WarehouseExporter(
        output_dir=tmp_path,
    )

    df = sample_dataframe()

    exporter.export_dimension(
        df,
        "dim_product.csv",
    )

    # Correção: clean_output_directory por padrão é incremental. 
    # Para deletar tudo, precisa de full_clean=True.
    exporter.clean_output_directory(full_clean=True)

    assert len(
        list(
            tmp_path.glob("*.csv")
        )
    ) == 0
