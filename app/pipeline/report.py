from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.pipeline.models import PipelineResult


class PipelineReport:
    """
    Gera os relatórios finais da execução do pipeline.
    """

    def __init__(
        self,
        output_dir: str = "data/output/reports",
    ) -> None:

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def export(
        self,
        result: PipelineResult,
    ) -> dict[str, Path]:

        files = {}

        files["json"] = self.export_json(result)

        files["csv"] = self.export_csv(result)

        files["txt"] = self.export_txt(result)

        return files

    def export_json(
        self,
        result: PipelineResult,
    ) -> Path:

        output = (
            self.output_dir
            / "pipeline_report.json"
        )

        with output.open(
            "w",
            encoding="utf-8",
        ) as fp:

            json.dump(

                result.to_dict(),

                fp,

                indent=4,

                ensure_ascii=False,

                default=str,

            )

        return output

    def export_csv(
        self,
        result: PipelineResult,
    ) -> Path:

        output = (
            self.output_dir
            / "pipeline_report.csv"
        )

        rows = []

        for step in result.steps:

            rows.append(

                {

                    "step": step.name,

                    "status": step.status.value,

                    "duration_seconds": step.duration_seconds,

                    "records_processed": step.records_processed,

                    "errors": step.errors,

                    "message": step.message,

                }

            )

        pd.DataFrame(rows).to_csv(

            output,

            index=False,

            encoding="utf-8-sig",

        )

        return output

    def export_txt(
        self,
        result: PipelineResult,
    ) -> Path:

        output = (
            self.output_dir
            / "pipeline_report.txt"
        )

        with output.open(
            "w",
            encoding="utf-8",
        ) as fp:

            fp.write("=" * 70)
            fp.write("\n")
            fp.write("DOG FOOD NUTRITION PIPELINE REPORT\n")
            fp.write("=" * 70)
            fp.write("\n\n")

            fp.write(
                f"Status: {result.status.value}\n"
            )

            fp.write(
                f"Started At: {result.metrics.started_at}\n"
            )

            fp.write(
                f"Finished At: {result.metrics.finished_at}\n"
            )

            fp.write(
                f"Execution Time: {result.metrics.execution_time_seconds:.3f}s\n"
            )

            fp.write("\n")

            fp.write("METRICS\n")
            fp.write("-" * 70)
            fp.write("\n")

            fp.write(
                f"Total Products: {result.metrics.total_products}\n"
            )

            fp.write(
                f"Collected: {result.metrics.collected_products}\n"
            )

            fp.write(
                f"Parsed: {result.metrics.parsed_products}\n"
            )

            fp.write(
                f"Normalized: {result.metrics.normalized_products}\n"
            )

            fp.write(
                f"Semantic: {result.metrics.semantic_products}\n"
            )

            fp.write(
                f"Exported: {result.metrics.exported_products}\n"
            )

            fp.write(
                f"Warnings: {result.metrics.warnings}\n"
            )

            fp.write(
                f"Errors: {result.metrics.total_errors}\n"
            )

            fp.write("\n")

            fp.write("PIPELINE STEPS\n")
            fp.write("-" * 70)
            fp.write("\n")

            for step in result.steps:

                fp.write(
                    f"{step.name:<25}"
                )

                fp.write(
                    f"{step.status.value:<12}"
                )

                fp.write(
                    f"{step.records_processed:>8} registros"
                )

                fp.write(
                    f"   {step.duration_seconds:.3f}s"
                )

                fp.write("\n")

            if result.outputs:

                fp.write("\n")

                fp.write("OUTPUT FILES\n")

                fp.write("-" * 70)

                fp.write("\n")

                for name, path in result.outputs.items():

                    fp.write(
                        f"{name:<25}{path}\n"
                    )

            if result.warnings:

                fp.write("\n")

                fp.write("WARNINGS\n")

                fp.write("-" * 70)

                fp.write("\n")

                for warning in result.warnings:

                    fp.write(
                        f"- {warning}\n"
                    )

            if result.errors:

                fp.write("\n")

                fp.write("ERRORS\n")

                fp.write("-" * 70)

                fp.write("\n")

                for error in result.errors:

                    fp.write(
                        f"- {error}\n"
                    )

            fp.write("\n")

            fp.write("=" * 70)

            fp.write("\n")

            fp.write(
                "Pipeline finished.\n"
            )

        return output