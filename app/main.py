from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.pipeline.orchestrator import PipelineOrchestrator


DEFAULT_INPUT = (
    "data/output/clean/"
    "nutrition_clean.parquet"
)


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        prog="DogFoodNutritionPipeline",
        description=(
            "Pipeline de coleta, normalização, "
            "enriquecimento semântico e geração "
            "do Data Warehouse."
        ),
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default=DEFAULT_INPUT,
        help="Arquivo de entrada (.parquet ou .csv).",
    )

    parser.add_argument(
        "-w",
        "--warehouse-output",
        type=str,
        default="data/output/warehouse",
        help="Diretório de saída do Data Warehouse.",
    )

    parser.add_argument(
        "-r",
        "--reports-output",
        type=str,
        default="data/output/reports",
        help="Diretório de saída dos relatórios.",
    )

    return parser.parse_args()


def main() -> int:

    args = parse_args()

    input_file = Path(args.input)

    if not input_file.exists():

        print()

        print(f"Arquivo não encontrado: {input_file}")

        return 1

    pipeline = PipelineOrchestrator(

        warehouse_output=args.warehouse_output,

        reports_output=args.reports_output,

    )

    print()

    print("=" * 70)
    print("DOG FOOD NUTRITION PIPELINE")
    print("=" * 70)

    print(f"Entrada : {input_file}")

    print()

    if input_file.suffix.lower() == ".csv":

        result = pipeline.run_from_csv(
            input_file,
        )

    elif input_file.suffix.lower() == ".parquet":

        result = pipeline.run_from_parquet(
            input_file,
        )

    else:

        print(
            "Formato de arquivo não suportado."
        )

        return 1

    print()

    print("=" * 70)

    print(
        f"STATUS: {'SUCCESS' if result.success else 'FAILED'}"
    )

    print("=" * 70)

    metrics = result.metrics

    print(
        f"Total produtos.............: {metrics.products_collected}"
    )

    print(
        f"Normalizados...............: {metrics.products_normalized}"
    )

    print(
        f"Semântica aplicada.........: {metrics.products_enriched}"
    )

    print(
        f"Exportados.................: {metrics.products_exported}"
    )

    print(
        f"Warnings...................: {len(result.warnings)}"
    )

    print(
        f"Erros......................: {len(result.errors)}"
    )

    print(
        f"Tempo total................: {metrics.execution_time_seconds:.2f}s"
    )

    if result.exported_files:

        print()

        print("Arquivos gerados:")

        for name, path in result.exported_files.items():

            print(
                f"  • {name:<25} {path}"
            )

    print()

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())