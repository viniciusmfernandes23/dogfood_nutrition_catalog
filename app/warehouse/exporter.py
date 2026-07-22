from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from app.normalization.semantic import SemanticLayer


class WarehouseExporter:
    """
    Exportador central do Data Warehouse.
    
    Responsável por consolidar os dados processados em arquivos CSV, aplicar 
    a camada semântica final, realizar auditorias de sanidade biológica 
    em nível de arquivo e gerenciar metadados de execução.
    """

    def __init__(
        self,
        output_dir: str = "data/output/warehouse",
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.sanity_logs = []

    def export_dimension(
        self,
        dataframe: pd.DataFrame,
        filename: str,
    ) -> Path:
        """
        Exporta tabelas de dimensão. 
        Utiliza modo append para preservar o histórico de produtos em execuções parciais.
        """
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
        """
        Exporta tabelas fato. 
        Apenas o histórico de preços é incremental; dados nutricionais são sobrescritos.
        """
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
        """
        Orquestra a exportação de todas as tabelas do warehouse.
        """
        from app.warehouse.nutrient_reference import NutrientReferenceBuilder
        dim_nutrient_ref = NutrientReferenceBuilder.build()

        exported = {
            "dim_product": self.export_dimension(dim_product, "dim_product.csv"),
            "dim_nutrient_reference": self._export_csv(dim_nutrient_ref, "dim_nutrient_reference.csv", append=False),
            "fact_nutrient": self.export_fact(fact_nutrient, "fact_nutrient.csv"),
            "fact_price_snapshot": self.export_fact(fact_price_snapshot, "fact_price_snapshot.csv"),
        }
        
        if self.sanity_logs:
            exported["sanity_audit_logs"] = self.export_sanity_logs()

        self.export_metadata(exported)
        return exported

    def export_sanity_logs(self) -> Path:
        """
        Exporta os logs da barreira de sanidade biológica final.
        """
        output_file = self.output_dir / "sanity_audit_logs.csv"
        df_logs = pd.DataFrame(self.sanity_logs)
        
        if output_file.exists():
            try:
                df_existing = pd.read_csv(output_file)
                df_logs = pd.concat([df_existing, df_logs], ignore_index=True)
            except Exception:
                pass
            
        df_logs.to_csv(output_file, index=False, encoding="utf-8-sig")
        return output_file

    def export_metadata(self, exported_files: dict[str, Path]) -> Path:
        """
        Gera o arquivo de metadados JSON com estatísticas da exportação.
        """
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "files": {
                name: {
                    "path": str(path),
                    "rows": self._count_rows(path),
                    "size_bytes": path.stat().st_size if path.exists() else 0,
                }
                for name, path in exported_files.items()
            },
        }

        metadata_path = self.output_dir / "warehouse_metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        return metadata_path

    def _export_csv(
        self,
        dataframe: pd.DataFrame,
        filename: str,
        append: bool = False
    ) -> Path:
        """
        Método interno para escrita de CSV com suporte a append e deduplicação.
        """
        output_file = self.output_dir / filename

        # Garante estrutura mínima para arquivos vazios
        if dataframe is None or dataframe.empty:
            if not output_file.exists():
                headers = self._get_default_headers(filename)
                pd.DataFrame(columns=headers).to_csv(output_file, index=False, encoding="utf-8-sig")
            return output_file

        # Processamento específico para Nutrientes (Barreira Final e Camada Semântica)
        if filename == "fact_nutrient.csv" and "nutrient_value" in dataframe.columns:
            self._apply_final_biological_sanity_check(dataframe)
            
            # Remove duplicatas exatas de perfil nutricional (Relatório Item 8)
            dataframe = dataframe.drop_duplicates(
                subset=["product_id", "nutrient_key", "nutrient_value"],
                keep="last"
            )
            
            # Aplica nomes amigáveis para exportação final (Power BI)
            dataframe = SemanticLayer.apply_output_conversion(dataframe)

        # Formatação de Preços
        if filename == "fact_price_snapshot.csv":
            for price_col in ("price", "list_price", "subscriber_price", "price_per_kg"):
                if price_col in dataframe.columns:
                    dataframe[price_col] = pd.to_numeric(dataframe[price_col], errors='coerce').round(2)

        # Lógica de Append com Deduplicação
        if append and output_file.exists():
            try:
                existing_df = pd.read_csv(output_file, encoding="utf-8-sig")
                
                # Normaliza tipos para garantir join correto
                id_cols = ["product_id", "collected_at", "nutrient_key", "sku_id", "marketplace", "ean"]
                for col in id_cols:
                    if col in existing_df.columns:
                        existing_df[col] = existing_df[col].astype(str)
                    if col in dataframe.columns:
                        dataframe[col] = dataframe[col].astype(str)

                combined_df = pd.concat([existing_df, dataframe], ignore_index=True)
                
                # Deduplicação inteligente baseada no tipo de dado
                if filename == "fact_price_snapshot.csv" and "collected_at" in combined_df.columns:
                    combined_df["collected_at_dt"] = pd.to_datetime(combined_df["collected_at"])
                    combined_df["_date_only"] = combined_df["collected_at_dt"].dt.date
                    price_subset = ["product_id", "_date_only"]
                    for col in ["sku_id", "marketplace"]:
                        if col in combined_df.columns:
                            price_subset.append(col)
                    combined_df = combined_df.sort_values(by="collected_at_dt").drop_duplicates(subset=price_subset, keep='last')
                    combined_df = combined_df.drop(columns=["_date_only", "collected_at_dt"])
                else:
                    subset = ["product_id"]
                    for col in ["collected_at", "nutrient_key"]:
                        if col in combined_df.columns:
                            subset.append(col)
                    combined_df = combined_df.drop_duplicates(subset=subset, keep='last')
                
                dataframe = combined_df
            except Exception as e:
                print(f"Erro ao carregar histórico ({filename}): {e}. Sobrescrevendo...")

        dataframe.to_csv(output_file, index=False, encoding="utf-8-sig")
        return output_file

    def _get_default_headers(self, filename: str) -> list[str]:
        """
        Retorna os cabeçalhos padrão para cada tipo de arquivo.
        """
        if "fact_nutrient" in filename:
            return ["product_id", "nutrient_key", "nutrient_value", "nutrient_unit", "original_value", "original_unit", "status", "rule_applied", "collected_at", "reason"]
        elif "fact_price" in filename:
            return ["product_id", "marketplace", "ean", "sku_id", "sku_name", "package_weight_kg", "price", "list_price", "subscriber_price", "price_per_kg", "available", "collected_at"]
        elif "dim_product" in filename:
            return ["product_id", "brand", "product_name", "product_category"]
        return ["product_id"]

    def _apply_final_biological_sanity_check(self, df: pd.DataFrame) -> None:
        """
        Barreira de Sanidade Final: Filtra valores fisicamente impossíveis 
        que podem ter passado pelas camadas anteriores.
        """
        if "nutrient_key" not in df.columns or "nutrient_value" not in df.columns:
            return

        macro_fields = ["protein_gkg", "fat_gkg", "fiber_gkg", "ash_gkg", "moisture_gkg"]
        mineral_fields = ["sodium_mgkg", "potassium_mgkg", "calcium_min_mgkg", "calcium_max_mgkg", "phosphorus_mgkg"]
        
        sanity_checks = [
            ((df["nutrient_key"].isin(macro_fields)) & (df["nutrient_value"] > 1000), "macro_exceeds_1000gkg"),
            ((df["nutrient_key"] == "metabolizable_energy_kcalkg") & (df["nutrient_value"] > 4500), "energy_exceeds_4500kcalkg"),
            ((df["nutrient_key"] == "metabolizable_energy_kcalkg") & (df["nutrient_value"] < 500), "energy_below_500kcalkg"),
            ((df["nutrient_key"].isin(mineral_fields)) & (df["nutrient_value"] > 60000), "mineral_toxicity_limit"),
            ((df["nutrient_key"].isin(mineral_fields)) & (df["nutrient_value"] < 0.01), "mineral_insignificant_limit")
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
                df.loc[mask, "nutrient_value"] = None

    def _count_rows(self, path: Path) -> int:
        if not path.exists():
            return 0
        try:
            return len(pd.read_csv(path))
        except Exception:
            return 0

    def clean_output_directory(self, full_clean: bool = False) -> None:
        """
        Limpa o diretório de saída. 
        Por padrão, preserva o histórico de preços.
        """
        if full_clean:
            for f in self.output_dir.glob("*.*"):
                f.unlink()
        else:
            for f in self.output_dir.glob("*.csv"):
                if f.name != "fact_price_snapshot.csv":
                    f.unlink()
            for f in self.output_dir.glob("*.json"):
                f.unlink()
