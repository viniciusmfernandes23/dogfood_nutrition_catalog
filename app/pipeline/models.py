from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class PipelineStep:
    """
    Representa uma etapa do pipeline.
    """

    name: str

    status: PipelineStatus = PipelineStatus.PENDING

    started_at: datetime | None = None

    finished_at: datetime | None = None

    duration_seconds: float = 0.0

    records_processed: int = 0

    errors: int = 0

    message: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict,
    )

    def to_dict(self) -> dict[str, Any]:

        return {

            "name": self.name,

            "status": self.status.value,

            "started_at": (
                self.started_at.isoformat()
                if self.started_at
                else None
            ),

            "finished_at": (
                self.finished_at.isoformat()
                if self.finished_at
                else None
            ),

            "duration_seconds": self.duration_seconds,

            "records_processed": self.records_processed,

            "errors": self.errors,

            "message": self.message,

            "metadata": self.metadata,

        }


@dataclass(slots=True)
class PipelineMetrics:
    """
    Métricas globais da execução.
    """

    total_products: int = 0

    collected_products: int = 0

    parsed_products: int = 0

    normalized_products: int = 0

    semantic_products: int = 0

    exported_products: int = 0

    total_errors: int = 0

    warnings: int = 0

    execution_time_seconds: float = 0.0

    started_at: datetime | None = None

    finished_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:

        return {

            "total_products": self.total_products,

            "collected_products": self.collected_products,

            "parsed_products": self.parsed_products,

            "normalized_products": self.normalized_products,

            "semantic_products": self.semantic_products,

            "exported_products": self.exported_products,

            "total_errors": self.total_errors,

            "warnings": self.warnings,

            "execution_time_seconds": self.execution_time_seconds,

            "started_at": (
                self.started_at.isoformat()
                if self.started_at
                else None
            ),

            "finished_at": (
                self.finished_at.isoformat()
                if self.finished_at
                else None
            ),

        }


@dataclass(slots=True)
class PipelineResult:
    """
    Resultado completo da execução.
    """

    status: PipelineStatus = PipelineStatus.PENDING

    metrics: PipelineMetrics = field(
        default_factory=PipelineMetrics,
    )

    steps: list[PipelineStep] = field(
        default_factory=list,
    )

    outputs: dict[str, str] = field(
        default_factory=dict,
    )

    errors: list[str] = field(
        default_factory=list,
    )

    warnings: list[str] = field(
        default_factory=list,
    )

    def add_step(
        self,
        step: PipelineStep,
    ) -> None:

        self.steps.append(step)

    def add_error(
        self,
        message: str,
    ) -> None:

        self.errors.append(message)

        self.metrics.total_errors += 1

    def add_warning(
        self,
        message: str,
    ) -> None:

        self.warnings.append(message)

        self.metrics.warnings += 1

    def add_output(
        self,
        name: str,
        path: str,
    ) -> None:

        self.outputs[name] = path

    @property
    def success(self) -> bool:

        return self.status == PipelineStatus.SUCCESS

    @property
    def failed(self) -> bool:

        return self.status == PipelineStatus.FAILED

    def to_dict(self) -> dict[str, Any]:

        return {

            "status": self.status.value,

            "metrics": self.metrics.to_dict(),

            "steps": [

                step.to_dict()

                for step

                in self.steps

            ],

            "outputs": self.outputs,

            "errors": self.errors,

            "warnings": self.warnings,

        }