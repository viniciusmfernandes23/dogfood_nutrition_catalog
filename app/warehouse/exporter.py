from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


class WarehouseExporter:
    """
    Responsável por exportar as tabelas do Data Warehouse.
    """

    def __init__(
        self,
        output_dir: str = "data/output/warehouse",
    ) -> None:

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def export_dimension(
        self,
        dataframe: pd.DataFrame,
        filename: str,
    ) -> Path:

        return self._export_csv(
            dataframe=dataframe,
            filename=filename,
        )

    def export_fact(
        self,
        dataframe: pd.DataFrame,
        filename: str,
    ) -> Path:

        return self._export_csv(
            dataframe=dataframe,
            filename=filename,
        )

    def export_all(
        self,
        *,
        dim_product: pd.DataFrame,
        fact_nutrient: pd.DataFrame,
        fact_price_snapshot: pd.DataFrame,
    ) -> dict[str, Path]:

        exported = {

            "dim_product":

                self.export_dimension(
                    dim_product,
                    "dim_product.csv",
                ),

            "fact_nutrient":

                self.export_fact(
                    fact_nutrient,
                    "fact_nutrient.csv",
                ),

            "fact_price_snapshot":

                self.export_fact(
                    fact_price_snapshot,
                    "fact_price_snapshot.csv",
                ),

        }

        self.export_metadata(
            exported,
        )

        return exported

    def export_metadata(
        self,
        exported_files: dict[str, Path],
    ) -> Path:

        metadata = {

            "generated_at":

                datetime.utcnow().isoformat(),

            "files": {

                name: {

                    "path": str(path),

                    "rows": self._count_rows(path),

                    "size_bytes": path.stat().st_size
                    if path.exists()
                    else 0,

                }

                for name, path

                in exported_files.items()

            },

        }

        metadata_path = (
            self.output_dir
            / "warehouse_metadata.json"
        )

        with metadata_path.open(
            "w",
            encoding="utf-8",
        ) as fp:

            json.dump(
                metadata,
                fp,
                indent=4,
                ensure_ascii=False,
            )

        return metadata_path

    def _export_csv(
        self,
        dataframe: pd.DataFrame,
        filename: str,
    ) -> Path:

        output_file = (
            self.output_dir
            / filename
        )

        dataframe.to_csv(

            output_file,

            index=False,

            encoding="utf-8-sig",

        )

        return output_file

    @staticmethod
    def _count_rows(
        file_path: Path,
    ) -> int:

        if not file_path.exists():

            return 0

        try:

            return len(
                pd.read_csv(
                    file_path,
                    low_memory=False,
                )
            )

        except Exception:

            return 0

    def clean_output_directory(
        self,
    ) -> None:

        for file in self.output_dir.glob("*"):

            if file.is_file():

                file.unlink()

    def file_exists(
        self,
        filename: str,
    ) -> bool:

        return (
            self.output_dir
            / filename
        ).exists()

    def list_exported_files(
        self,
    ) -> list[Path]:

        return sorted(

            self.output_dir.glob(
                "*.csv"
            )

        )