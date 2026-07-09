from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PipelineConfig:
    """
    Configuração da execução do pipeline.
    """

    input_url: str | None = None

    output_directory: str = "data/output"

    warehouse_directory: str = "data/output/warehouse"

    # Se True, atualiza todo o catálogo (API + Crawler). 
    # Se False, atualiza apenas preços e disponibilidade (API apenas).
    full_update: bool = True

    overwrite: bool = True

    export_csv: bool = True

    save_logs: bool = True

    def to_dict(self) -> dict[str, Any]:

        return asdict(self)


@dataclass(slots=True)
class PipelineMetrics:
    """
    Métricas consolidadas da execução.
    """

    products_collected: int = 0

    products_parsed: int = 0

    products_normalized: int = 0

    products_enriched: int = 0

    products_exported: int = 0

    normalization_changes: int = 0

    elapsed_seconds: float = 0.0

    started_at: datetime | None = None

    finished_at: datetime | None = None

    def start(self) -> None:

        self.started_at = datetime.now()

    def finish(self) -> None:

        self.finished_at = datetime.now()

        if self.started_at is not None:

            self.elapsed_seconds = round(

                (
                    self.finished_at
                    - self.started_at
                ).total_seconds(),

                3,

            )

    def to_dict(self) -> dict[str, Any]:

        return asdict(self)


@dataclass(slots=True)
class PipelineResult:
    """
    Resultado final do pipeline.
    """

    success: bool

    metrics: PipelineMetrics

    exported_files: dict[str, Path] = field(
        default_factory=dict,
    )

    errors: list[str] = field(
        default_factory=list,
    )

    warnings: list[str] = field(
        default_factory=list,
    )

    def add_error(
        self,
        message: str,
    ) -> None:

        self.errors.append(
            message,
        )

        self.success = False

    def add_warning(
        self,
        message: str,
    ) -> None:

        self.warnings.append(
            message,
        )

    def to_dict(self) -> dict[str, Any]:

        return {

            "success": self.success,

            "metrics": self.metrics.to_dict(),

            "exported_files": {

                name: str(path)

                for name, path

                in self.exported_files.items()

            },

            "errors": self.errors,

            "warnings": self.warnings,

        }