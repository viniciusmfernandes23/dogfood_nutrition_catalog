from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.normalization.engine import NormalizationEngine
from app.pipeline.metrics import PipelineMetricsCollector
from app.pipeline.models import (
    PipelineResult,
    PipelineStatus,
)
from app.pipeline.report import PipelineReport
from app.semantic.engine import SemanticEngine
from app.warehouse.pipeline import WarehousePipeline


class PipelineOrchestrator:
    """
    Orquestra todo o fluxo do pipeline.

        Input
            ↓
        Normalization
            ↓
        Semantic
            ↓
        Data Warehouse
            ↓
        Reports
    """

    def __init__(
        self,
        warehouse_output: str = "data/output/warehouse",
        reports_output: str = "data/output/reports",
    ) -> None:

        self.normalizer = NormalizationEngine()

        self.semantic = SemanticEngine()

        self.warehouse = WarehousePipeline(
            output_dir=warehouse_output,
        )

        self.report = PipelineReport(
            output_dir=reports_output,
        )

        self.metrics = PipelineMetricsCollector()

    def run(
        self,
        dataframe: pd.DataFrame,
    ) -> PipelineResult:

        result = PipelineResult()

        self.metrics.start_pipeline()

        result.status = PipelineStatus.RUNNING

        try:

            self.metrics.update_total_products(
                len(dataframe)
            )

            # -------------------------------------------------
            # Normalization
            # -------------------------------------------------

            step = self.metrics.start_step(
                "Normalization"
            )

            normalized_df, normalization_report = (
                self.normalizer.normalize_dataframe(
                    dataframe
                )
            )

            self.metrics.update_normalization(
                len(normalized_df)
            )

            result.add_step(

                self.metrics.finish_step(

                    step,

                    records_processed=len(
                        normalized_df
                    ),

                    metadata={
                        "changed_records":
                        normalization_report.changed_records,

                        "manual_review":
                        normalization_report.manual_review_records,

                        "auto_corrected":
                        normalization_report.auto_corrected_records,

                    },

                )

            )

            # -------------------------------------------------
            # Semantic
            # -------------------------------------------------

            step = self.metrics.start_step(
                "Semantic"
            )

            semantic_df = self.semantic.enrich_dataframe(
                normalized_df
            )

            self.metrics.update_semantic(
                len(semantic_df)
            )

            result.add_step(

                self.metrics.finish_step(

                    step,

                    records_processed=len(
                        semantic_df
                    ),

                )

            )

            # -------------------------------------------------
            # Warehouse
            # -------------------------------------------------

            step = self.metrics.start_step(
                "Warehouse"
            )

            tables = self.warehouse.run(
                semantic_df
            )

            exported_rows = sum(

                len(df)

                for df

                in tables.values()

            )

            self.metrics.update_export(
                exported_rows
            )

            result.add_step(

                self.metrics.finish_step(

                    step,

                    records_processed=exported_rows,

                )

            )

            # -------------------------------------------------
            # Outputs
            # -------------------------------------------------

            warehouse_dir = Path(
                self.warehouse.exporter.output_dir
            )

            for file in warehouse_dir.glob("*.csv"):

                result.add_output(
                    file.stem,
                    str(file),
                )

            metadata = (
                warehouse_dir
                / "warehouse_metadata.json"
            )

            if metadata.exists():

                result.add_output(
                    "warehouse_metadata",
                    str(metadata),
                )

            # -------------------------------------------------
            # Finalização
            # -------------------------------------------------

            result.metrics = self.metrics.finish_pipeline()

            result.status = PipelineStatus.SUCCESS

            self.report.export(
                result
            )

            return result

        except Exception as exc:

            result.status = PipelineStatus.FAILED

            result.add_error(
                str(exc)
            )

            result.metrics = (
                self.metrics.finish_pipeline()
            )

            self.report.export(
                result
            )

            return result

    def run_from_csv(
        self,
        input_file: str | Path,
    ) -> PipelineResult:

        dataframe = pd.read_csv(
            input_file,
            low_memory=False,
        )

        return self.run(
            dataframe
        )

    def run_from_parquet(
        self,
        input_file: str | Path,
    ) -> PipelineResult:

        dataframe = pd.read_parquet(
            input_file
        )

        return self.run(
            dataframe
        )