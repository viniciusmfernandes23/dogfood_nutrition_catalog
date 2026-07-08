from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd


class WarehouseExporter:
    """
    Responsável pela exportação das tabelas do Data Warehouse.
    Suporta exportação incremental (append) para tabelas fato.
    """

    def __init__(
        self,
        output_dir: str = "data/output/warehouse",
    ) -> None:

        self.output_dir = Path(
            output_dir,
        )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ==========================================================
    # Exportações
    # ==========================================================

    def export_dimension(
        self,
        dataframe: pd.DataFrame,
        filename: str,
    ) -> Path:
        """Dimensões são sobrescritas para manter o estado atual."""
        return self._export_csv(
            dataframe,
            filename,
            append=False
        )

    def export_fact(
        self,
        dataframe: pd.DataFrame,
        filename: str,
    ) -> Path:
        """Tabelas fato de preços são incrementais. Outras (nutrientes) são sobrescritas."""
        # Apenas fact_price_snapshot mantém histórico
        is_incremental = (filename == "fact_price_snapshot.csv")
        return self._export_csv(
            dataframe,
            filename,
            append=is_incremental
        )

    def export_all(
        self,
        *,
        dim_product: pd.DataFrame,
        fact_nutrient: pd.DataFrame,
        fact_price_snapshot: pd.DataFrame,
    ) -> dict[str, Path]:

        exported = {
            "dim_product": self.export_dimension(
                dim_product,
                "dim_product.csv",
            ),
            "fact_nutrient": self.export_fact(
                fact_nutrient,
                "fact_nutrient.csv",
            ),
            "fact_price_snapshot": self.export_fact(
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
            "generated_at": datetime.now(
                UTC,
            ).isoformat(),
            "files": {
                name: {
                    "path": str(path),
                    "rows": self._count_rows(
                        path,
                    ),
                    "size_bytes": (
                        path.stat().st_size
                        if path.exists()
                        else 0
                    ),
                }
                for name, path
                in exported_files.items()
            },
        }

        metadata_path = (
            self.output_dir
            / "warehouse_metadata.json"
        )

        metadata_path.write_text(
            json.dumps(
                metadata,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return metadata_path

    # ==========================================================
    # CSV
    # ==========================================================

    def _export_csv(
        self,
        dataframe: pd.DataFrame,
        filename: str,
        append: bool = False
    ) -> Path:

        output_file = (
            self.output_dir
            / filename
        )

        # Se for append e o arquivo já existir, carregamos o existente para evitar duplicatas
        if append and output_file.exists():
            try:
                # Carrega o arquivo existente
                existing_df = pd.read_csv(output_file, encoding="utf-8-sig")
                
                # Garante tipos consistentes para detecção de duplicatas
                for col in ["product_id", "collected_at", "nutrient_name"]:
                    if col in existing_df.columns:
                        existing_df[col] = existing_df[col].astype(str)
                    if col in dataframe.columns:
                        dataframe[col] = dataframe[col].astype(str)

                # Concatenamos
                combined_df = pd.concat([existing_df, dataframe], ignore_index=True)
                
                # Identifica colunas para detecção de duplicatas
                subset = ["product_id"]
                if "collected_at" in combined_df.columns:
                    subset.append("collected_at")
                if "nutrient_name" in combined_df.columns:
                    subset.append("nutrient_name")
                
                # Ajuste: No caso de fact_price_snapshot, a deduplicação deve usar apenas a data (sem hora)
                # pois o pipeline atualiza os preços diariamente
                if filename == "fact_price_snapshot.csv" and "collected_at" in combined_df.columns:
                    # Cria coluna temporária apenas com a data para deduplicação
                    combined_df["_date_only"] = pd.to_datetime(combined_df["collected_at"]).dt.date
                    subset = ["product_id", "_date_only"]
                    combined_df = combined_df.drop_duplicates(subset=subset, keep='last')
                    combined_df = combined_df.drop(columns=["_date_only"])
                else:
                    # Remove duplicatas (mantém a versão mais recente se houver conflito no mesmo timestamp)
                    combined_df = combined_df.drop_duplicates(subset=subset, keep='last')
                
                dataframe = combined_df
            except Exception as e:
                print(f"Erro ao carregar histórico ({filename}): {e}. Sobrescrevendo...")

        dataframe.to_csv(
            output_file,
            index=False,
            encoding="utf-8-sig",
        )

        return output_file

    # ==========================================================
    # Helpers
    # ==========================================================

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
        full_clean: bool = False,
    ) -> None:
        """
        Limpa o diretório de saída.
        Se full_clean=True, remove tudo. Caso contrário, preserva histórico de preços.
        Nota: fact_nutrient.csv nunca é preservado para evitar acúmulo de valores de escala errados.
        """
        preserved_files = [] if full_clean else ["fact_price_snapshot.csv"]
        for file in self.output_dir.iterdir():
            if file.is_file() and file.name not in preserved_files:
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
                "*.csv",
            )
        )

    def list_metadata_files(
        self,
    ) -> list[Path]:

        return sorted(
            self.output_dir.glob(
                "*.json",
            )
        )
