from __future__ import annotations

import json
from pathlib import Path

from app.pipeline.models import PipelineResult


class PipelineReport:
    """
    Responsável pela geração do relatório final do pipeline.
    """

    def __init__(
        self,
        output_dir: str = "data/output",
    ) -> None:

        self.output_dir = Path(
            output_dir,
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ==========================================================
    # Relatórios
    # ==========================================================

    def build(
        self,
        result: PipelineResult,
    ) -> dict:

        return result.to_dict()

    def save_json(
        self,
        result: PipelineResult,
        filename: str = "pipeline_report.json",
    ) -> Path:

        report = self.build(
            result,
        )

        output_file = (
            self.output_dir
            / filename
        )

        output_file.write_text(

            json.dumps(
                report,
                indent=4,
                ensure_ascii=False,
                default=str,
            ),

            encoding="utf-8",

        )

        return output_file

    # ==========================================================
    # Console
    # ==========================================================

    @staticmethod
    def print_summary(
        result: PipelineResult,
    ) -> None:

        metrics = result.metrics

        print()

        print("=" * 60)
        print("PIPELINE REPORT")
        print("=" * 60)

        print(
            f"Success                 : {result.success}"
        )

        print(
            f"Products Collected      : {metrics.products_collected}"
        )

        print(
            f"Products Parsed         : {metrics.products_parsed}"
        )

        print(
            f"Products Normalized     : {metrics.products_normalized}"
        )

        print(
            f"Normalization Changes   : {metrics.normalization_changes}"
        )

        print(
            f"Products Enriched       : {metrics.products_enriched}"
        )

        print(
            f"Products Exported       : {metrics.products_exported}"
        )

        print(
            f"Elapsed Seconds         : {metrics.elapsed_seconds:.3f}"
        )

        if result.exported_files:

            print("\nExported Files:")

            for name, path in result.exported_files.items():

                print(
                    f"  - {name}: {path}"
                )

        if result.warnings:

            print("\nWarnings:")

            for warning in result.warnings:

                print(
                    f"  - {warning}"
                )

        if result.errors:

            print("\nErrors:")

            for error in result.errors:

                print(
                    f"  - {error}"
                )

        print("=" * 60)

    # ==========================================================
    # Utilidades
    # ==========================================================

    @staticmethod
    def has_errors(
        result: PipelineResult,
    ) -> bool:

        return bool(
            result.errors,
        )

    @staticmethod
    def has_warnings(
        result: PipelineResult,
    ) -> bool:

        return bool(
            result.warnings,
        )