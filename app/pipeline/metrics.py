from __future__ import annotations

import time
from datetime import datetime

from app.pipeline.models import (
    PipelineMetrics,
    PipelineStatus,
    PipelineStep,
)


class PipelineMetricsCollector:
    """
    Responsável por coletar métricas da execução
    do pipeline.
    """

    def __init__(self) -> None:

        self.metrics = PipelineMetrics()

        self._pipeline_start: float | None = None

        self._step_start: float | None = None

    def start_pipeline(self) -> None:

        self._pipeline_start = time.perf_counter()

        self.metrics.started_at = datetime.utcnow()

    def finish_pipeline(self) -> PipelineMetrics:

        self.metrics.finished_at = datetime.utcnow()

        if self._pipeline_start is not None:

            self.metrics.execution_time_seconds = round(

                time.perf_counter() - self._pipeline_start,

                3,

            )

        return self.metrics

    def start_step(
        self,
        name: str,
    ) -> PipelineStep:

        self._step_start = time.perf_counter()

        return PipelineStep(

            name=name,

            status=PipelineStatus.RUNNING,

            started_at=datetime.utcnow(),

        )

    def finish_step(
        self,
        step: PipelineStep,
        *,
        records_processed: int = 0,
        errors: int = 0,
        message: str | None = None,
        metadata: dict | None = None,
    ) -> PipelineStep:

        step.finished_at = datetime.utcnow()

        step.status = (
            PipelineStatus.SUCCESS
            if errors == 0
            else PipelineStatus.FAILED
        )

        if self._step_start is not None:

            step.duration_seconds = round(

                time.perf_counter() - self._step_start,

                3,

            )

        step.records_processed = records_processed

        step.errors = errors

        step.message = message

        step.metadata = metadata or {}

        return step

    def fail_step(
        self,
        step: PipelineStep,
        error: Exception | str,
    ) -> PipelineStep:

        step.finished_at = datetime.utcnow()

        step.status = PipelineStatus.FAILED

        if self._step_start is not None:

            step.duration_seconds = round(

                time.perf_counter() - self._step_start,

                3,

            )

        step.errors = 1

        step.message = str(error)

        self.metrics.total_errors += 1

        return step

    def update_collection(
        self,
        count: int,
    ) -> None:

        self.metrics.collected_products = count

    def update_parser(
        self,
        count: int,
    ) -> None:

        self.metrics.parsed_products = count

    def update_normalization(
        self,
        count: int,
    ) -> None:

        self.metrics.normalized_products = count

    def update_semantic(
        self,
        count: int,
    ) -> None:

        self.metrics.semantic_products = count

    def update_export(
        self,
        count: int,
    ) -> None:

        self.metrics.exported_products = count

    def update_total_products(
        self,
        count: int,
    ) -> None:

        self.metrics.total_products = count

    def increment_warning(
        self,
    ) -> None:

        self.metrics.warnings += 1

    def increment_error(
        self,
    ) -> None:

        self.metrics.total_errors += 1

    @property
    def success_rate(
        self,
    ) -> float:

        if self.metrics.total_products == 0:

            return 0.0

        return round(

            (
                self.metrics.exported_products
                / self.metrics.total_products
            )
            * 100,

            2,

        )

    def summary(
        self,
    ) -> dict:

        return {

            "total_products":
                self.metrics.total_products,

            "collected_products":
                self.metrics.collected_products,

            "parsed_products":
                self.metrics.parsed_products,

            "normalized_products":
                self.metrics.normalized_products,

            "semantic_products":
                self.metrics.semantic_products,

            "exported_products":
                self.metrics.exported_products,

            "errors":
                self.metrics.total_errors,

            "warnings":
                self.metrics.warnings,

            "execution_time_seconds":
                self.metrics.execution_time_seconds,

            "success_rate":
                self.success_rate,

        }