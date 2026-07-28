"""Regressões da extração nutricional antes da normalização."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.normalization.engine import NormalizationEngine
from app.normalization.rules import NORMALIZATION_RULES
from app.pipeline.metrics import PipelineMetricsCollector
from app.pipeline.models import PipelineConfig
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services.nutrition_extraction import (
    NUTRIENT_MAPPING,
    NutritionExtractionService,
)
from app.warehouse.fact_nutrient import NutrientFactBuilder


UNIT_SUFFIXES = ("_kcalkg", "_uikg", "_mgkg", "_gkg")


def _nutrient_key(field: str) -> str:
    """Remove somente o sufixo de unidade de um campo canônico."""
    for suffix in UNIT_SUFFIXES:
        if field.endswith(suffix):
            return field[: -len(suffix)]
    return field


def test_mapping_covers_every_normalization_rule() -> None:
    """Cada regra normalizável deve poder ser preenchida pelo parser."""
    expected_mapping = {
        _nutrient_key(field): field
        for field in NORMALIZATION_RULES
    }

    assert NUTRIENT_MAPPING == expected_mapping


def test_extract_and_map_keeps_non_gkg_nutrients() -> None:
    """Nutrientes de minerais, energia e vitaminas não podem ser descartados."""
    dataframe = pd.DataFrame(
        {
            "product_name": ["Ração de regressão"],
            "raw_guarantee": [
                "Fósforo (mín.) 0,8%; "
                "Ômega 3 (mín.) 0,3%; "
                "Vitamina A 20.000 UI/kg; "
                "Energia Metabolizável 3.600 kcal/kg"
            ],
        }
    )

    result = NutritionExtractionService().extract_and_map(dataframe)

    assert result.loc[0, "phosphorus_mgkg"] == 0.8
    assert result.loc[0, "omega_3_mgkg"] == 0.3
    assert result.loc[0, "vitamin_a_uikg"] == 20000.0
    assert result.loc[0, "metabolizable_energy_kcalkg"] == 3600.0

    for field in (
        "phosphorus_mgkg",
        "omega_3_mgkg",
        "vitamin_a_uikg",
        "metabolizable_energy_kcalkg",
    ):
        assert result.loc[0, f"{field}_unit"] is not None


def test_extract_and_map_reports_parser_counts() -> None:
    """As métricas distinguem o retorno bruto do parser do mapeamento canônico."""
    dataframe = pd.DataFrame(
        {
            "product_name": ["Ração de regressão"],
            "raw_guarantee": [
                "Fósforo (mín.) 0,8%; "
                "Ômega 3 (mín.) 0,3%; "
                "Vitamina A 20.000 UI/kg; "
                "Energia Metabolizável 3.600 kcal/kg"
            ],
        }
    )
    collector = PipelineMetricsCollector()

    NutritionExtractionService().extract_and_map(
        dataframe,
        metrics_collector=collector,
    )

    metrics = collector.metrics
    assert metrics.parser_nutrients_parsed == 4
    assert metrics.parser_nutrients_mapped == 4
    assert metrics.parser_nutrients_found == metrics.parser_nutrients_mapped
    assert metrics.parser_products_with_nutrients == 1


def test_non_gkg_nutrients_reach_fact_nutrient() -> None:
    """O fluxo completo deve persistir nutrientes além dos cinco macronutrientes."""
    dataframe = pd.DataFrame(
        {
            "product_id": ["produto-regressao"],
            "product_name": ["Ração de regressão"],
            "raw_guarantee": [
                "Fósforo (mín.) 0,8%; "
                "Ômega 3 (mín.) 0,3%; "
                "Vitamina A 20.000 UI/kg; "
                "Energia Metabolizável 3.600 kcal/kg"
            ],
        }
    )

    extracted = NutritionExtractionService().extract_and_map(dataframe)
    normalized, _ = NormalizationEngine().normalize_dataframe(extracted)
    fact = NutrientFactBuilder().build(normalized)

    expected_keys = {
        "phosphorus_mgkg",
        "omega_3_mgkg",
        "vitamin_a_uikg",
        "metabolizable_energy_kcalkg",
    }
    assert expected_keys.issubset(set(fact["nutrient_key"]))


def test_orchestrator_reports_nutrient_flow_metrics(tmp_path: Path) -> None:
    """O orquestrador deve expor as contagens de normalização e persistência."""
    dataframe = pd.DataFrame(
        {
            "product_id": ["produto-regressao"],
            "product_name": ["Ração de regressão"],
            "brand": ["Marca de teste"],
            "category": ["Ração seca"],
            "raw_guarantee": [
                "Fósforo (mín.) 0,8%; "
                "Ômega 3 (mín.) 0,3%; "
                "Vitamina A 20.000 UI/kg; "
                "Energia Metabolizável 3.600 kcal/kg"
            ],
        }
    )
    extracted = NutritionExtractionService().extract_and_map(dataframe)
    pipeline = PipelineOrchestrator(
        PipelineConfig(
            warehouse_directory=str(tmp_path / "warehouse"),
            output_directory=str(tmp_path / "reports"),
        )
    )

    result = pipeline.run(extracted)

    assert result.success
    assert result.metrics.normalization_nutrients_output == 4
    assert result.metrics.warehouse_fact_nutrient_records == 4
    assert result.metrics.warehouse_records_exported == 4
