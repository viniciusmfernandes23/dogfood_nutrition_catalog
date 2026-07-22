from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from app.normalization.semantic import SemanticLayer


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
        
        # Lista para armazenar logs da barreira de sanidade
        self.sanity_logs = []

    # ==========================================================
    # Exportações
    # ==========================================================

    def export_dimension(
        self,
        dataframe: pd.DataFrame,
        filename: str,
    ) -> Path:
        """Dimensões são incrementais para evitar perda de produtos em execuções parciais."""
        return self._export_csv(
            dataframe,
            filename,
            append=True
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
        
        # Gera a dimensão de referência de nutrientes
        from app.warehouse.nutrient_reference import NutrientReferenceBuilder
        dim_nutrient_ref = NutrientReferenceBuilder.build()

        exported = {
            "dim_product": self.export_dimension(
                dim_product,
                "dim_product.csv",
            ),
            "dim_nutrient_reference": self._export_csv(
                dim_nutrient_ref,
                "dim_nutrient_reference.csv",
                append=False
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
        
        # Exporta logs da barreira de sanidade se houver
        if self.sanity_logs:
            exported["sanity_audit_logs"] = self.export_sanity_logs()

        self.export_metadata(
            exported,
        )

        return exported

    def export_sanity_logs(self) -> Path:
        """Exporta os logs capturados pela barreira de sanidade biológica."""
        output_file = self.output_dir / "sanity_audit_logs.csv"
        df_logs = pd.DataFrame(self.sanity_logs)
        
        # Modo append se já existir para manter histórico de auditoria
        if output_file.exists():
            try:
                df_existing = pd.read_csv(output_file)
                df_logs = pd.concat([df_existing, df_logs], ignore_index=True)
            except Exception:
                pass
            
        df_logs.to_csv(output_file, index=False, encoding="utf-8-sig")
        return output_file

    def export_metadata(
        self,
        exported_files: dict[str, Path],
    ) -> Path:

        metadata = {
            "generated_at": datetime.now().isoformat(),
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

        # Se o DataFrame estiver vazio, garantimos que o arquivo exista (mesmo vazio)
        if dataframe is None or dataframe.empty:
            if not output_file.exists():
                headers = ["product_id"]
                if "fact_nutrient" in filename:
                    headers = [
                        "product_id", "nutrient_key", "nutrient_value", "nutrient_unit",
                        "original_value", "original_unit", "status", "rule_applied", "collected_at"
                    ]
                elif "fact_price" in filename:
                    headers = [
                        "product_id", "marketplace", "ean", "sku_id", "sku_name",
                        "package_weight_kg", "price", "list_price",
                        "subscriber_price", "price_per_kg",
                        "available", "collected_at",
                        "has_price", "has_price_per_kg", "has_subscriber_price",
                    ]
                elif "dim_product" in filename:
                    headers = ["product_id", "brand", "product_name", "product_category"]
                
                pd.DataFrame(columns=headers).to_csv(output_file, index=False, encoding="utf-8-sig")
            return output_file

        # Barreira de Sanidade Final
        if filename == "fact_nutrient.csv" and "nutrient_value" in dataframe.columns:
            self._apply_final_biological_sanity_check(dataframe)
            
            # Prioridade 6: O Power BI não deve realizar correções. Receber apenas dados já consistentes.
            # Aplica a Camada Semântica orientada por metadados
            dataframe = SemanticLayer.apply_output_conversion(dataframe)

        if filename == "fact_price_snapshot.csv":
            for price_col in ("price", "list_price", "subscriber_price", "price_per_kg"):
                if price_col in dataframe.columns:
                    dataframe[price_col] = pd.to_numeric(dataframe[price_col], errors='coerce').round(2)

        if append and output_file.exists():
            try:
                existing_df = pd.read_csv(output_file, encoding="utf-8-sig")
                
                for col in ["product_id", "collected_at", "nutrient_key", "sku_id", "marketplace", "ean"]:
                    if col in existing_df.columns:
                        existing_df[col] = existing_df[col].astype(str)
                    if col in dataframe.columns:
                        dataframe[col] = dataframe[col].astype(str)

                combined_df = pd.concat([existing_df, dataframe], ignore_index=True)
                
                subset = ["product_id"]
                if "collected_at" in combined_df.columns:
                    subset.append("collected_at")
                if "nutrient_key" in combined_df.columns:
                    subset.append("nutrient_key")
                
                if "collected_at" in combined_df.columns:
                    combined_df["collected_at_dt"] = pd.to_datetime(combined_df["collected_at"])
                    combined_df = combined_df.sort_values(by="collected_at_dt")
                
                if filename == "fact_price_snapshot.csv" and "collected_at" in combined_df.columns:
                    combined_df["_date_only"] = combined_df["collected_at_dt"].dt.date
                    price_subset = ["product_id", "_date_only"]
                    if "sku_id" in combined_df.columns:
                        price_subset.append("sku_id")
                    if "marketplace" in combined_df.columns:
                        price_subset.append("marketplace")
                    combined_df = combined_df.drop_duplicates(subset=price_subset, keep='last')
                    combined_df = combined_df.drop(columns=["_date_only"])
                else:
                    combined_df = combined_df.drop_duplicates(subset=subset, keep='last')
                
                if "collected_at_dt" in combined_df.columns:
                    combined_df = combined_df.drop(columns=["collected_at_dt"])
                
                dataframe = combined_df
            except Exception as e:
                print(f"Erro ao carregar histórico ({filename}): {e}. Sobrescrevendo...")

        dataframe.to_csv(
            output_file,
            index=False,
            encoding="utf-8-sig",
        )

        return output_file

    def _apply_final_biological_sanity_check(self, df: pd.DataFrame) -> None:
        """
        Aplica as regras de ouro biológicas como filtro final obrigatório.
        """
        # Alinhado para usar nutrient_key conforme fact_nutrient.py
        if "nutrient_key" not in df.columns or "nutrient_value" not in df.columns:
            return

        # 1. Trava de Limites Absolutos
        macro_fields = ["protein_gkg", "fat_gkg", "fiber_gkg", "ash_gkg", "moisture_gkg"]
        mineral_fields = ["sodium_mgkg", "potassium_mgkg", "calcium_min_mgkg", "calcium_max_mgkg", "phosphorus_mgkg"]
        
        sanity_checks = [
            ((df["nutrient_key"].isin(macro_fields)) & (df["nutrient_value"] > 1000), "macro_exceeds_1000gkg"),
            ((df["nutrient_key"] == "metabolizable_energy_kcalkg") & (df["nutrient_value"] > 4500), "energy_exceeds_4500kcalkg"), # Ajustado para 4500
            ((df["nutrient_key"] == "metabolizable_energy_kcalkg") & (df["nutrient_value"] < 500), "energy_below_500kcalkg"),
            ((df["nutrient_key"].isin(mineral_fields)) & (df["nutrient_value"] > 60000), "mineral_toxicity_limit"),
            ((df["nutrient_key"].isin(mineral_fields)) & (df["nutrient_value"] < 0.01), "mineral_insignificant_limit") # Ajustado para 0.01
        ]

        for mask, reason in sanity_checks:
            extreme_indices = df[mask].index
            if not extreme_indices.empty:
                for idx in extreme_indices:
                    self.sanity_logs.append({
                        "product_id": df.at[idx, "product_id"],
                        "field": df.at[idx, "nutrient_key"],
                        "original_value": df.at[idx, "nutrient_value"],
                        "action": "nullified",
                        "reason": reason,
                        "timestamp": datetime.now().isoformat()
                    })
                print(f"[FINAL SANITY BARRIER] Anulando {len(extreme_indices)} valores por {reason}.")
                df.loc[mask, "nutrient_value"] = None

    def _count_rows(self, path: Path) -> int:
        if not path.exists():
            return 0
        try:
            return len(pd.read_csv(path))
        except Exception:
            return 0

    def clean_output_directory(self, full_clean: bool = False) -> None:
        if full_clean:
            for f in self.output_dir.glob("*.csv"):
                f.unlink()
            for f in self.output_dir.glob("*.json"):
                f.unlink()
        else:
            # Mantém histórico de preços se não for full_clean
            for f in self.output_dir.glob("*.csv"):
                if f.name != "fact_price_snapshot.csv":
                    f.unlink()

    def list_exported_files(self) -> list[Path]:
        return list(self.output_dir.glob("*.csv"))

    def file_exists(self, filename: str) -> bool:
        return (self.output_dir / filename).exists()
