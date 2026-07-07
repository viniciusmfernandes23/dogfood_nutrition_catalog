from __future__ import annotations

from dataclasses import asdict

from app.pipeline.models import PipelineMetrics


class PipelineMetricsCollector:
    """
    Responsável por coletar e consolidar métricas
    durante a execução do pipeline.
    """

    def __init__(self) -> None:

        self.metrics = PipelineMetrics()

    # ==========================================================
    # Ciclo de vida
    # ==========================================================

    def start(self) -> None:

        self.metrics.start()

    def finish(self) -> None:

        self.metrics.finish()

    # ==========================================================
    # Incrementos
    # ==========================================================

    def increment_collected(
        self,
        amount: int = 1,
    ) -> None:

        self.metrics.products_collected += amount

    def increment_parsed(
        self,
        amount: int = 1,
    ) -> None:

        self.metrics.products_parsed += amount

    def increment_normalized(
        self,
        amount: int = 1,
    ) -> None:

        self.metrics.products_normalized += amount

    def increment_enriched(
        self,
        amount: int = 1,
    ) -> None:

        self.metrics.products_enriched += amount

    def increment_exported(
        self,
        amount: int = 1,
    ) -> None:

        self.metrics.products_exported += amount

    def increment_normalization_changes(
        self,
        amount: int = 1,
    ) -> None:

        self.metrics.normalization_changes += amount

    # ==========================================================
    # Setters
    # ==========================================================

    def set_collected(
        self,
        value: int,
    ) -> None:

        self.metrics.products_collected = value

    def set_parsed(
        self,
        value: int,
    ) -> None:

        self.metrics.products_parsed = value

    def set_normalized(
        self,
        value: int,
    ) -> None:

        self.metrics.products_normalized = value

    def set_enriched(
        self,
        value: int,
    ) -> None:

        self.metrics.products_enriched = value

    def set_exported(
        self,
        value: int,
    ) -> None:

        self.metrics.products_exported = value

    def set_normalization_changes(
        self,
        value: int,
    ) -> None:

        self.metrics.normalization_changes = value

    # ==========================================================
    # Helpers
    # ==========================================================

    def reset(self) -> None:

        self.metrics = PipelineMetrics()

    def snapshot(self) -> PipelineMetrics:

        return PipelineMetrics(
            **asdict(self.metrics),
        )

    def to_dict(self) -> dict:

        return self.metrics.to_dict()