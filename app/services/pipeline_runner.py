"""
PipelineRunner — Orquestrador principal do pipeline de nutrição canina.

Responsável por:
  1. Coletar produtos (CollectionService)
  2. Enriquecer dados (ProductEnrichmentService)
  3. Executar crawler (modo full)
  4. Extrair nutrientes (NutritionExtractionService)
  5. Executar orquestrador de normalização (PipelineOrchestrator)
  6. Pós-processar warehouse (WarehousePostProcessor)

Mantém o executar_pipeline.py como wrapper enxuto.
"""

from __future__ import annotations

import os
from datetime import datetime

import pandas as pd

from app.collectors.crawler import CobasiCrawler
from app.core.logging import logger
from app.pipeline.models import PipelineConfig
from app.pipeline.orchestrator import PipelineOrchestrator
from app.services.collection_service import CollectionService
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
        output_dir: str = "output",
        mode: str = "full",
        marketplaces: list[str] | None = None,
        collector_kwargs: dict[str, dict] | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.mode = mode
        self.is_full = mode == "full"

        # Diretórios
        self._ensure_dirs()

        # Timestamp da execução
        self.timestamp = datetime.now()

        # Serviços
        self._collection = CollectionService(
            marketplaces=marketplaces or ["Cobasi"],
            collector_kwargs=collector_kwargs or {},
        )
        self._enrichment = ProductEnrichmentService()
        self._nutrition = NutritionExtractionService()
        self._post_processor = WarehousePostProcessor(
            warehouse_dir=os.path.join(output_dir, "warehouse")
        )

        # Orquestrador
        warehouse_dir = os.path.join(output_dir, "warehouse")
        self._config = PipelineConfig(
            full_update=self.is_full,
            output_directory=output_dir,
            warehouse_directory=warehouse_dir,
        )
        self._orchestrator = PipelineOrchestrator(self._config)

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

            # 3. Crawler (apenas modo full)
            if self.is_full:
                logger.info("Fase 3: Crawling (extração de níveis de garantia)...")
                self._run_crawler(full_df)

                # 4. Extração nutricional
                logger.info("Fase 4: Extração e mapeamento de nutrientes...")
                full_df = self._nutrition.extract_and_map(full_df)

            # 5. Orquestrador (normalização + warehouse)
            logger.info("Fase 5: Normalização e exportação do warehouse...")
            result = self._orchestrator.run(full_df)

            # 6. Pós-processamento
            logger.info("Fase 6: Pós-processamento do warehouse...")
            post_results = self._post_processor.process_all()

            logger.info("\nPipeline concluído com sucesso!")
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

    def _run_crawler(self, df: pd.DataFrame) -> None:
        """Executa o crawler para extrair níveis de garantia."""
        crawler = CobasiCrawler()
        guarantees = []
        total = len(df)

        for i, url in enumerate(df["url"]):
            if i % 20 == 0:
                logger.info("  Progresso: %d/%d", i, total)
            try:
                res = crawler.collect(url)
                guarantees.append(res.guarantee_section if res.success else None)
            except Exception:
                guarantees.append(None)

        df["raw_guarantee"] = guarantees
