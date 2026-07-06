from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.pipeline.orchestrator import PipelineOrchestrator


DEFAULT_INPUT = (
    "data/output/clean/nutrition_clean.parquet"
)


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        prog="dogfood-pipeline",
        description=(
            "Pipeline de dados nutricionais "
            "para rações de cães."
        ),
    )

    parser.add_argument(
        "-i",
        "--input",
        default=DEFAULT_INPUT,
        help="Arquivo de entrada (.csv ou .parquet).",
    )

    parser.add_argument(
        "-w",
        "--warehouse-output",
        default="data/output/warehouse",
        help="Diretório de saída do Data Warehouse.",
    )

    parser.add_argument(
        "-r",
        "--reports-output",
        default="data/output/reports",
        help="Diretório de saída dos relatórios.",
    )

    parser.add_argument(
        "--clean-output",
        action="store_true",
        help="Remove os arquivos antigos antes da execução.",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Exibe um resumo da execução.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="DogFood Nutrition Pipeline 1.0.0",
    )

    return parser


def print_summary(result) -> None:

    metrics = result.metrics

    print()
    print("=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)

    print(f"Status.................... {result.status.value}")
    print(f"Tempo..................... {metrics.execution_time_seconds:.2f}s")
    print(f"Produtos................. {metrics.total_products}")
    print(f"Normalizados............ {metrics.normalized_products}")
    print(f"Semântica............... {metrics.semantic_products}")
    print(f"Exportados.............. {metrics.exported_products}")
    print(f"Warnings................ {metrics.warnings}")
    print(f"Erros................... {metrics.total_errors}")

    if result.outputs:

        print()
        print("Arquivos gerados:")

        for name, path in sorted(result.outputs.items()):

            print(f"  • {name:<24} {path}")

    print("=" * 70)
    print()


def main() -> int:

    parser = build_parser()

    args = parser.parse_args()

    input_file = Path(args.input)

    if not input_file.exists():

        print(
            f"Arquivo não encontrado: {input_file}"
        )

        return 1

    pipeline = PipelineOrchestrator(

        warehouse_output=args.warehouse_output,

        reports_output=args.reports_output,

    )

    if args.clean_output:

        pipeline.warehouse.clean_output()

    print()
    print("=" * 70)
    print("DOG FOOD NUTRITION PIPELINE")
    print("=" * 70)
    print(f"Entrada: {input_file}")
    print()

    suffix = input_file.suffix.lower()

    if suffix == ".csv":

        result = pipeline.run_from_csv(
            input_file
        )

    elif suffix == ".parquet":

        result = pipeline.run_from_parquet(
            input_file
        )

    else:

        print(
            "Formato de arquivo não suportado."
        )

        return 1

    if args.summary:

        print_summary(result)

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())