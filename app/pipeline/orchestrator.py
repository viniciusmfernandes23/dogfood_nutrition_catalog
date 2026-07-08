from __future__ import annotations

import pandas as pd

from app.normalization.engine import NormalizationEngine
from app.pipeline.metrics import PipelineMetricsCollector
from app.pipeline.models import (
    PipelineConfig,
    PipelineResult,
)
from app.pipeline.report import PipelineReport
from app.semantic.engine import SemanticEngine
from app.warehouse.pipeline import WarehousePipeline


class PipelineOrchestrator:
    """
    Orquestra toda a execução do pipeline.
    """

    def __init__(
        self,
        config: PipelineConfig | None = None,
    ) -> None:

        self.config = config or PipelineConfig()

        self.metrics = PipelineMetricsCollector()

        self.normalization_engine = NormalizationEngine()

        self.semantic_engine = SemanticEngine()

        self.warehouse_pipeline = WarehousePipeline(
            output_dir=self.config.warehouse_directory,
        )

        self.report = PipelineReport(
            output_dir=self.config.output_directory,
        )

    # ==========================================================
    # Pipeline
    # ==========================================================

    def run(
        self,
        dataframe: pd.DataFrame,
    ) -> PipelineResult:

        self.metrics.reset()

        self.metrics.start()

        # Se configurado para sobrescrever, limpamos o diretório antes da execução
        if self.config.overwrite:
            self.clean_output()

        result = PipelineResult(

            success=True,

            metrics=self.metrics.metrics,

        )

        try:

            # ----------------------------------------------
            # Coleta e Métricas
            # ----------------------------------------------
            self.metrics.set_collected(len(dataframe))

            # Se for atualização parcial, ignoramos parser, normalização e semântica
            # e vamos direto para a atualização de preços no warehouse.
            if not self.config.full_update:
                print("Modo de Atualização Parcial: Atualizando apenas Preços e Disponibilidade...")
                
                # Tentamos carregar o dim_product existente para manter a integridade
                # mas o warehouse_pipeline.run cuidará de construir apenas o necessário.
                tables, exported = self.warehouse_pipeline.run(dataframe)
                
                result.exported_files = exported
                self.metrics.set_exported(len(tables.get("fact_price_snapshot", pd.DataFrame())))
                return result

            # ----------------------------------------------
            # Fluxo Completo (Parser + Normalização + Semântica)
            # ----------------------------------------------

            self.metrics.set_parsed(len(dataframe))

            normalized_df, normalization_report = (
                self.normalization_engine.normalize_dataframe(dataframe)
            )

            self.metrics.set_normalized(len(normalized_df))
            self.metrics.set_normalization_changes(normalization_report.auto_corrected_records)

            semantic_df = self.semantic_engine.enrich_dataframe(normalized_df)
            self.metrics.set_enriched(len(semantic_df))

            # ----------------------------------------------
            # Warehouse
            # ----------------------------------------------

            tables, exported = self.warehouse_pipeline.run(semantic_df)

            result.exported_files = exported

            self.metrics.set_exported(
                len(
                    tables["dim_product"],
                )
            )

        except Exception as exc:

            result.add_error(
                str(exc),
            )

        finally:

            self.metrics.finish()

            result.metrics = self.metrics.snapshot()

            if self.config.save_logs:

                self.report.save_json(
                    result,
                )

        return result

    # ==========================================================
    # Utilidades
    # ==========================================================

    def print_report(
        self,
        result: PipelineResult,
    ) -> None:

        self.report.print_summary(
            result,
        )

    def clean_output(
        self,
    ) -> None:

        self.warehouse_pipeline.clean()