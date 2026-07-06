from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.pipeline.models import PipelineStatus
from app.pipeline.orchestrator import PipelineOrchestrator


def sample_dataframe() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "product_id": [1],
            "sku": ["SKU001"],
            "brand": ["Premier"],
            "manufacturer": ["Premier Pet"],
            "product_name": [
                "Ração Super Premium Frango para Cães Adultos"
            ],
            "product_url": [
                "https://example.com/product"
            ],
            "image_url": [
                "https://example.com/image.jpg"
            ],
            "category": [
                "Ração Seca"
            ],
            "description": [
                "Alimento completo para cães adultos."
            ],
            "ingredients": [
                "Farinha de frango, arroz"
            ],
            "protein": [26],
            "protein_unit": ["%"],
            "fat": [15],
            "fat_unit": ["%"],
            "fiber": [3],
            "fiber_unit": ["%"],
            "moisture": [10],
            "moisture_unit": ["%"],
            "price": [249.90],
            "subscriber_price": [229.90],
            "price_per_kg": [16.66],
            "currency": ["BRL"],
            "in_stock": [True],
            "seller": ["Cobasi"],
            "source": ["crawler"],
        }
    )


def test_pipeline_execution(
    tmp_path: Path,
):

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    result = pipeline.run(
        sample_dataframe()
    )

    assert result.success

    assert (
        result.status
        == PipelineStatus.SUCCESS
    )


def test_pipeline_generates_outputs(
    tmp_path: Path,
):

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    result = pipeline.run(
        sample_dataframe()
    )

    assert len(
        result.outputs
    ) > 0


def test_pipeline_generates_reports(
    tmp_path: Path,
):

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    pipeline.run(
        sample_dataframe()
    )

    reports = tmp_path / "reports"

    assert (
        reports
        / "pipeline_report.json"
    ).exists()

    assert (
        reports
        / "pipeline_report.csv"
    ).exists()

    assert (
        reports
        / "pipeline_report.txt"
    ).exists()


def test_pipeline_generates_warehouse(
    tmp_path: Path,
):

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    pipeline.run(
        sample_dataframe()
    )

    warehouse = (
        tmp_path
        / "warehouse"
    )

    assert (
        warehouse
        / "dim_product.csv"
    ).exists()

    assert (
        warehouse
        / "fact_nutrient.csv"
    ).exists()

    assert (
        warehouse
        / "fact_price_snapshot.csv"
    ).exists()


def test_pipeline_metrics(
    tmp_path: Path,
):

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    result = pipeline.run(
        sample_dataframe()
    )

    metrics = result.metrics

    assert (
        metrics.total_products
        == 1
    )

    assert (
        metrics.normalized_products
        == 1
    )

    assert (
        metrics.semantic_products
        == 1
    )


def test_pipeline_steps(
    tmp_path: Path,
):

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    result = pipeline.run(
        sample_dataframe()
    )

    assert len(
        result.steps
    ) >= 3


def test_pipeline_execution_time(
    tmp_path: Path,
):

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    result = pipeline.run(
        sample_dataframe()
    )

    assert (
        result.metrics.execution_time_seconds
        >= 0
    )


def test_pipeline_outputs_registered(
    tmp_path: Path,
):

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    result = pipeline.run(
        sample_dataframe()
    )

    assert (
        "dim_product"
        in result.outputs
    )

    assert (
        "fact_nutrient"
        in result.outputs
    )

    assert (
        "fact_price_snapshot"
        in result.outputs
    )


def test_pipeline_from_csv(
    tmp_path: Path,
):

    csv_file = (
        tmp_path
        / "input.csv"
    )

    sample_dataframe().to_csv(
        csv_file,
        index=False,
    )

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    result = pipeline.run_from_csv(
        csv_file
    )

    assert result.success


def test_pipeline_from_parquet(
    tmp_path: Path,
):

    parquet_file = (
        tmp_path
        / "input.parquet"
    )

    sample_dataframe().to_parquet(
        parquet_file,
        index=False,
    )

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    result = pipeline.run_from_parquet(
        parquet_file
    )

    assert result.success


def test_pipeline_without_errors(
    tmp_path: Path,
):

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    result = pipeline.run(
        sample_dataframe()
    )

    assert (
        result.metrics.total_errors
        == 0
    )

    assert (
        len(result.errors)
        == 0
    )


def test_pipeline_returns_pipeline_result(
    tmp_path: Path,
):

    pipeline = PipelineOrchestrator(
        warehouse_output=tmp_path / "warehouse",
        reports_output=tmp_path / "reports",
    )

    result = pipeline.run(
        sample_dataframe()
    )

    assert hasattr(
        result,
        "metrics",
    )

    assert hasattr(
        result,
        "steps",
    )

    assert hasattr(
        result,
        "outputs",
    )