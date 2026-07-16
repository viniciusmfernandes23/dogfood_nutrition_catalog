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

        # Se o DataFrame estiver vazio, garantimos que o arquivo exista (mesmo vazio) para evitar erros em scripts externos
        if dataframe is None or dataframe.empty:
            if not output_file.exists():
                # Cria um arquivo vazio com cabeçalhos padrão baseados no nome do arquivo
                headers = ["product_id"]
                if "fact_nutrient" in filename:
                    headers = ["product_id", "nutrient_name", "nutrient_value", "collected_at"]
                elif "fact_price" in filename:
                    headers = [
                        "product_id", "sku_id", "sku_name",
                        "package_weight_kg", "price", "list_price",
                        "subscriber_price", "price_per_kg",
                        "available", "collected_at",
                        "has_price", "has_price_per_kg", "has_subscriber_price",
                    ]
                elif "dim_product" in filename:
                    headers = ["product_id", "brand", "product_name", "product_category"]
                
                pd.DataFrame(columns=headers).to_csv(output_file, index=False, encoding="utf-8-sig")
            return output_file

        # Barreira de Sanidade Final (v1.3.2): Validação biológica obrigatória antes da escrita
        if filename == "fact_nutrient.csv" and "nutrient_value" in dataframe.columns:
            self._apply_final_biological_sanity_check(dataframe)
            
            # Aplica a Camada Semântica orientada por metadados
            # Converte da escala técnica interna para a escala de negócio real
            dataframe = SemanticLayer.apply_output_conversion(dataframe)

        if filename == "fact_price_snapshot.csv":
            for price_col in ("price", "list_price", "subscriber_price", "price_per_kg"):
                if price_col in dataframe.columns:
                    # Converte para numérico e arredonda apenas valores válidos
                    dataframe[price_col] = pd.to_numeric(dataframe[price_col], errors='coerce').round(2)

        # Se for append e o arquivo já existir, carregamos o existente para evitar duplicatas
        if append and output_file.exists():
            try:
                # Carrega o arquivo existente
                existing_df = pd.read_csv(output_file, encoding="utf-8-sig")
                
                # Garante tipos consistentes para detecção de duplicatas
                for col in ["product_id", "collected_at", "nutrient_name", "sku_id"]:
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
                
                # Garantir que collected_at seja datetime para ordenação correta
                if "collected_at" in combined_df.columns:
                    combined_df["collected_at_dt"] = pd.to_datetime(combined_df["collected_at"])
                    # Ordena por data para que 'last' seja realmente o mais recente
                    combined_df = combined_df.sort_values(by="collected_at_dt")
                
                # Ajuste: No caso de fact_price_snapshot, a deduplicação deve usar
                # product_id + sku_id + data para preservar múltiplas variações do
                # mesmo produto coletadas no mesmo dia (ex: embalagens de 10kg, 15kg, 20kg).
                if filename == "fact_price_snapshot.csv" and "collected_at" in combined_df.columns:
                    # Cria coluna temporária apenas com a data para deduplicação
                    combined_df["_date_only"] = combined_df["collected_at_dt"].dt.date
                    # Inclui sku_id na chave de deduplicação para preservar variações distintas
                    price_subset = ["product_id", "_date_only"]
                    if "sku_id" in combined_df.columns:
                        price_subset.append("sku_id")
                    combined_df = combined_df.drop_duplicates(subset=price_subset, keep='last')
                    combined_df = combined_df.drop(columns=["_date_only"])
                else:
                    # Remove duplicatas (mantém a versão mais recente se houver conflito no mesmo timestamp)
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
        Aplica as 5 regras de ouro biológicas como filtro final obrigatório no DataFrame de exportação.
        """
        if "nutrient_name" not in df.columns or "nutrient_value" not in df.columns:
            return

        # 1. Trava de Limites Absolutos (Física da Matéria Orgânica)
        macro_fields = ["protein_gkg", "fat_gkg", "fiber_gkg", "ash_gkg", "moisture_gkg"]
        mineral_fields = ["sodium_mgkg", "potassium_mgkg", "calcium_min_mgkg", "calcium_max_mgkg", "phosphorus_mgkg"]
        
        sanity_checks = [
            ((df["nutrient_name"].isin(macro_fields)) & (df["nutrient_value"] > 1000), "macro_exceeds_1000gkg"),
            ((df["nutrient_name"] == "metabolizable_energy_kcalkg") & (df["nutrient_value"] > 9000), "energy_exceeds_9000kcalkg"),
            ((df["nutrient_name"] == "metabolizable_energy_kcalkg") & (df["nutrient_value"] < 100), "energy_below_100kcalkg"),
            ((df["nutrient_name"].isin(mineral_fields)) & (df["nutrient_value"] > 60000), "mineral_toxicity_limit"),
            ((df["nutrient_name"].isin(mineral_fields)) & (df["nutrient_value"] < 1), "mineral_insignificant_limit")
        ]

        for mask, reason in sanity_checks:
            extreme_indices = df[mask].index
            if not extreme_indices.empty:
                for idx in extreme_indices:
                    self.sanity_logs.append({
                        "product_id": df.at[idx, "product_id"],
                        "field": df.at[idx, "nutrient_name"],
                        "original_value": df.at[idx, "nutrient_value"],
                        "action": "nullified",
                        "reason": reason,
                        "timestamp": datetime.now().isoformat()
                    })
                print(f"[FINAL SANITY BARRIER] Anulando {len(extreme_indices)} valores por {reason}.")
                df.loc[mask, "nutrient_value"] = None

        # 2. Âncora de Umidade vs Energia (Rações Úmidas)
        for product_id in df["product_id"].unique():
            prod_mask = df["product_id"] == product_id
            moisture_row = df[prod_mask & (df["nutrient_name"] == "moisture_gkg")]
            energy_row = df[prod_mask & (df["nutrient_name"] == "metabolizable_energy_kcalkg")]
            
            if not moisture_row.empty and not energy_row.empty:
                moisture = moisture_row["nutrient_value"].values[0]
                energy = energy_row["nutrient_value"].values[0]
                
                if pd.notna(moisture) and pd.notna(energy):
                    if moisture > 700 and energy > 1500:
                        action = "nullified" if energy > 6000 else "corrected_10x"
                        new_val = None if energy > 6000 else round(energy / 10.0, 2)
                        
                        self.sanity_logs.append({
                            "product_id": product_id,
                            "field": "metabolizable_energy_kcalkg",
                            "original_value": energy,
                            "action": action,
                            "reason": "moisture_energy_inconsistency",
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        print(f"[FINAL SANITY BARRIER] {action.capitalize()} Energia incompatível com Umidade para produto {product_id}")
                        df.loc[prod_mask & (df["nutrient_name"] == "metabolizable_energy_kcalkg"), "nutrient_value"] = new_val

        # 3. Validação de Soma de Macronutrientes por Produto
        for product_id in df["product_id"].unique():
            prod_mask = df["product_id"] == product_id
            macros_present = df[prod_mask & (df["nutrient_name"].isin(macro_fields))]
            
            if not macros_present.empty:
                total_sum = macros_present["nutrient_value"].sum()
                if total_sum > 1050:
                    for idx in macros_present.index:
                        self.sanity_logs.append({
                            "product_id": product_id,
                            "field": df.at[idx, "nutrient_name"],
                            "original_value": df.at[idx, "nutrient_value"],
                            "action": "nullified",
                            "reason": f"macro_sum_exceeded_{int(total_sum)}",
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    energy_row = df[prod_mask & (df["nutrient_name"] == "metabolizable_energy_kcalkg")]
                    if not energy_row.empty:
                        self.sanity_logs.append({
                            "product_id": product_id,
                            "field": "metabolizable_energy_kcalkg",
                            "original_value": energy_row["nutrient_value"].values[0],
                            "action": "nullified",
                            "reason": "macro_sum_inconsistency",
                            "timestamp": datetime.now().isoformat()
                        })

                    print(f"[FINAL SANITY BARRIER] Soma de macros impossível ({total_sum}g/kg) no produto {product_id}. Anulando nutrientes.")
                    df.loc[prod_mask & (df["nutrient_name"].isin(macro_fields)), "nutrient_value"] = None
                    df.loc[prod_mask & (df["nutrient_name"] == "metabolizable_energy_kcalkg"), "nutrient_value"] = None

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
        Se full_clean=True, remove tudo para uma nova execução completa.
        Caso contrário (incremental), preserva os arquivos existentes do Data Warehouse.
        """
        if full_clean:
            for file in self.output_dir.iterdir():
                if file.is_file():
                    file.unlink()
        else:
            print("[WAREHOUSE] Modo incremental: Preservando arquivos existentes no diretório de saída.")

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
