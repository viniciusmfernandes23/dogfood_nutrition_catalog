"""
PipelineRunner — Orquestrador principal do pipeline de nutrição canina.

Responsável por:
  1. Coletar produtos (CollectionService)
  2. Enriquecer dados (ProductEnrichmentService)
  3. Executar crawler paralelo (CrawlerService)
  4. Extrair nutrientes (NutritionExtractionService)
  5. Executar orquestrador de normalização (PipelineOrchestrator)
  6. Pós-processar warehouse (WarehousePostProcessor)

Mantém o executar_pipeline.py como wrapper enxuto.
"""

from __future__ import annotations

import os
from datetime import datetime

import pandas as pd

from app.core.config_loader import ConfigLoader, PipelineConfig as RuntimeConfig
from app.core.logging import logger
from app.pipeline.models import PipelineConfig
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services.collection_service import CollectionService
from app.services.crawler_service import CrawlerService
from app.services.nutrition_extraction import NutritionExtractionService
from app.services.product_enrichment import ProductEnrichmentService
from app.services.warehouse_post_processor import WarehousePostProcessor


class PipelineRunner:
    """
    Orquestra a execução completa do pipeline de nutrição canina.

    Uso:
        runner = PipelineRunner(output_dir="output", mode="full")
        runner.run()
    """

    def __init__(
        self,
        *,
        output_dir: str | None = None,
        mode: str | None = None,
        marketplaces: list[str] | None = None,
        collector_kwargs: dict[str, dict] | None = None,
        crawler_workers: int | None = None,
        crawler_timeout: int | None = None,
        config: RuntimeConfig | None = None,
    ) -> None:
        # Carrega configuração do YAML se não fornecida
        self._runtime_config = config or ConfigLoader.load()

        # Resolve output_dir: argumento > config > default
        self.output_dir = output_dir or self._runtime_config.output_dir
        self.mode = mode or self._runtime_config.default_mode
        self.is_full = self.mode == "full"
        self._crawler_workers = (
            crawler_workers or self._runtime_config.crawler.max_workers
        )
        self._crawler_timeout = (
            crawler_timeout or self._runtime_config.crawler.timeout
        )

        # Diretórios
        self._ensure_dirs()

        # Timestamp da execução
        self.timestamp = datetime.now()

        # Serviços
        self._collection = CollectionService(
            marketplaces=marketplaces or ["Cobasi", "Petlove", "Petz"],
            collector_kwargs=collector_kwargs or {},
        )
        self._enrichment = ProductEnrichmentService()
        self._post_processor = WarehousePostProcessor(
            warehouse_dir=os.path.join(self.output_dir, "warehouse")
        )

        # Orquestrador (cria o metrics collector interno)
        warehouse_dir = os.path.join(self.output_dir, "warehouse")
        self._config = PipelineConfig(
            full_update=self.is_full,
            output_directory=self.output_dir,
            warehouse_directory=warehouse_dir,
        )
        self._orchestrator = PipelineOrchestrator(self._config)

        # NutritionExtractionService (precisa do metrics collector)
        self._nutrition = NutritionExtractionService()

    # ----------------------------------------------------------
    # Pipeline principal
    # ----------------------------------------------------------

    def run(self) -> dict:
        """
        Executa o pipeline completo.

        Retorna um dicionário com o resumo da execução.
        """
        logger.info(
            "--- Dogfood Nutrition Pipeline ---\nData: %s\nModo: %s",
            self.timestamp.strftime("%d/%m/%Y %H:%M:%S"),
            self.mode,
        )

        try:
            # 1. Coleta
            logger.info("Fase 1: Coleta de produtos...")
            raw_products = self._collection.collect()

            if not raw_products:
                logger.warning("AVISO: Nenhum produto retornado. Encerrando.")
                return {"success": False, "reason": "no_products"}

            # 2. Enriquecimento
            logger.info("Fase 2: Enriquecimento de produtos...")
            product_dicts = self._enrichment.enrich_batch(raw_products)

            if not product_dicts:
                logger.warning("AVISO: Nenhum produto enriquecido. Encerrando.")
                return {"success": False, "reason": "no_enriched_products"}

            df = pd.DataFrame(product_dicts)
            full_df = df.copy()

            # 3. Crawler paralelo (apenas modo full)
            if self.is_full:
                logger.info("Fase 3: Crawling paralelo (extração de níveis de garantia)...")
                crawler_service = CrawlerService(
                    max_workers=self._crawler_workers,
                    timeout=self._crawler_timeout,
                    metrics_collector=self._orchestrator.metrics,
                )
                full_df = crawler_service.crawl(full_df)

                # 4. Extração nutricional
                logger.info("Fase 4: Extração e mapeamento de nutrientes...")
                full_df = self._nutrition.extract_and_map(
                    full_df,
                    metrics_collector=self._orchestrator.metrics,
                )

            # 5. Orquestrador (normalização + warehouse)
            logger.info("Fase 5: Normalização e exportação do warehouse...")
            result = self._orchestrator.run(full_df)

            # 6. Pós-processamento
            logger.info("Fase 6: Pós-processamento do warehouse...")
            post_results = self._post_processor.process_all()

            # Atualiza métricas de warehouse
            if result.metrics:
                from app.pipeline.summary_report import PipelineSummaryReporter
                reporter = PipelineSummaryReporter(result.metrics)
                summary = reporter.to_dict()

                # Popula métricas de warehouse
                result.metrics.warehouse_files_exported = len(result.exported_files)
                # A métrica do warehouse deve refletir fatos persistidos, não
                # produtos exportados; esses valores possuem granularidades
                # distintas e sua confusão ocultaria regressões na fact_nutrient.
                result.metrics.warehouse_records_exported = (
                    result.metrics.warehouse_fact_nutrient_records
                )
                result.metrics.normalization_rules_applied = result.metrics.normalization_changes

            # 7. Computar throughput final
            if result.metrics and result.metrics.elapsed_seconds > 0:
                result.metrics.compute_throughput()

            # Gera relatório consolidado
            if result.metrics:
                from app.pipeline.summary_report import PipelineSummaryReporter
                reporter = PipelineSummaryReporter(result.metrics)
                logger.info("\n%s", reporter.generate())

            logger.info("Arquivos gerados em: %s/warehouse/", self.output_dir)

            return {
                "success": result.success,
                "metrics": result.metrics.to_dict() if result.metrics else {},
                "exported_files": {
                    k: str(v) for k, v in result.exported_files.items()
                },
                "post_processing": post_results,
                "errors": result.errors,
            }

        except Exception as exc:
            logger.error("\nERRO NO PIPELINE: %s", exc)
            return {"success": False, "error": str(exc)}

    # ----------------------------------------------------------
    # Helpers internos
    # ----------------------------------------------------------

    def _ensure_dirs(self) -> None:
        """Cria os diretórios de saída se não existirem."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "warehouse"), exist_ok=True)
