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
                    headers = ["product_id", "price", "collected_at"]
                elif "dim_product" in filename:
                    headers = ["product_id", "name", "brand", "category"]
                
                pd.DataFrame(columns=headers).to_csv(output_file, index=False, encoding="utf-8-sig")
            return output_file

        # Barreira de Sanidade Final (v1.3.2): Validação biológica obrigatória antes da escrita
        if filename == "fact_nutrient.csv" and "nutrient_value" in dataframe.columns:
            self._apply_final_biological_sanity_check(dataframe)
            
            # Aplica a Camada Semântica orientada por metadados
            # Converte da escala técnica interna para a escala de negócio real
            dataframe = SemanticLayer.apply_output_conversion(dataframe)

        if filename == "fact_price_snapshot.csv" and "price" in dataframe.columns:
            dataframe["price"] = dataframe["price"].round(2)

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
                
                # Garantir que collected_at seja datetime para ordenação correta
                if "collected_at" in combined_df.columns:
                    combined_df["collected_at_dt"] = pd.to_datetime(combined_df["collected_at"])
                    # Ordena por data para que 'last' seja realmente o mais recente
                    combined_df = combined_df.sort_values(by="collected_at_dt")
                
                # Ajuste: No caso de fact_price_snapshot, a deduplicação deve usar apenas a data (sem hora)
                # pois o pipeline atualiza os preços diariamente
                if filename == "fact_price_snapshot.csv" and "collected_at" in combined_df.columns:
                    # Cria coluna temporária apenas com a data para deduplicação
                    combined_df["_date_only"] = combined_df["collected_at_dt"].dt.date
                    subset = ["product_id", "_date_only"]
                    combined_df = combined_df.drop_duplicates(subset=subset, keep='last')
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
        # Macros e Umidade não podem exceder 1000 g/kg
        macro_fields = ["protein_gkg", "fat_gkg", "fiber_gkg", "ash_gkg", "moisture_gkg"]
        mask_macro_extreme = (df["nutrient_name"].isin(macro_fields)) & (df["nutrient_value"] > 1000)
        
        # Energia não pode exceder 9000 kcal/kg (limite da gordura pura) e nem ser inferior a 100 kcal/kg
        mask_energy_extreme = (df["nutrient_name"] == "metabolizable_energy_kcalkg") & ((df["nutrient_value"] > 9000) | (df["nutrient_value"] < 100))
        
        # Minerais não podem exceder 60.000 mg/kg (6%) ou serem insignificantes (< 1mg/kg para essenciais)
        # Reduzido de 10 para 1mg/kg para aceitar dietas líquidas/medicamentosas muito diluídas
        mineral_fields = ["sodium_mgkg", "potassium_mgkg", "calcium_min_mgkg", "calcium_max_mgkg", "phosphorus_mgkg"]
        mask_mineral_extreme = (df["nutrient_name"].isin(mineral_fields)) & ((df["nutrient_value"] > 60000) | (df["nutrient_value"] < 1))

        # Aplica anulações
        total_extreme = mask_macro_extreme.sum() + mask_energy_extreme.sum() + mask_mineral_extreme.sum()
        if total_extreme > 0:
            print(f"[FINAL SANITY BARRIER] Anulando {total_extreme} valores fisicamente impossíveis ou insignificantes.")
            df.loc[mask_macro_extreme | mask_energy_extreme | mask_mineral_extreme, "nutrient_value"] = None

        # 2. Âncora de Umidade vs Energia (Rações Úmidas)
        # Identificamos produtos com alta umidade e energia incompatível
        for product_id in df["product_id"].unique():
            prod_mask = df["product_id"] == product_id
            
            # Pega umidade e energia do mesmo produto
            moisture_row = df[prod_mask & (df["nutrient_name"] == "moisture_gkg")]
            energy_row = df[prod_mask & (df["nutrient_name"] == "metabolizable_energy_kcalkg")]
            
            if not moisture_row.empty and not energy_row.empty:
                moisture = moisture_row["nutrient_value"].values[0]
                energy = energy_row["nutrient_value"].values[0]
                
                if pd.notna(moisture) and pd.notna(energy):
                    # Regra: Umidade > 70% -> Energia Máxima 1.500 kcal/kg
                    if moisture > 700 and energy > 1500:
                        print(f"[FINAL SANITY BARRIER] Corrigindo Energia incompatível com Umidade para produto {product_id}")
                        # Se for erro de escala 10x, corrigimos. Se for lixo total, anulamos.
                        if energy > 6000:
                            df.loc[prod_mask & (df["nutrient_name"] == "metabolizable_energy_kcalkg"), "nutrient_value"] = None
                        else:
                            df.loc[prod_mask & (df["nutrient_name"] == "metabolizable_energy_kcalkg"), "nutrient_value"] = round(energy / 10.0, 2)

        # 3. Validação de Soma de Macronutrientes e Relações por Produto
        for product_id in df["product_id"].unique():
            prod_mask = df["product_id"] == product_id
            
            # Validação de Macronutrientes
            macros_present = df[prod_mask & (df["nutrient_name"].isin(macro_fields))]
            if not macros_present.empty:
                total_sum = macros_present["nutrient_value"].sum()
                
                # Proteção contra macros insignificantes (ex: 0.06 g/kg gordura)
                protein_val = df.loc[prod_mask & (df["nutrient_name"] == "protein_gkg"), "nutrient_value"]
                fat_val = df.loc[prod_mask & (df["nutrient_name"] == "fat_gkg"), "nutrient_value"]
                
                is_insignificant = False
                if not protein_val.empty and protein_val.values[0] < 5: is_insignificant = True
                if not fat_val.empty and fat_val.values[0] < 1: is_insignificant = True
                
                if total_sum > 1050 or is_insignificant:
                    print(f"[FINAL SANITY BARRIER] Macros inconsistentes no produto {product_id}. Anulando.")
                    df.loc[prod_mask & (df["nutrient_name"].isin(macro_fields)), "nutrient_value"] = None
                    df.loc[prod_mask & (df["nutrient_name"] == "metabolizable_energy_kcalkg"), "nutrient_value"] = None
            
            # Validação de Relação Ca:P
            ca_min = df.loc[prod_mask & (df["nutrient_name"] == "calcium_min_mgkg"), "nutrient_value"]
            ca_max = df.loc[prod_mask & (df["nutrient_name"] == "calcium_max_mgkg"), "nutrient_value"]
            p_val = df.loc[prod_mask & (df["nutrient_name"] == "phosphorus_mgkg"), "nutrient_value"]
            
            ca = ca_min.values[0] if not ca_min.empty else (ca_max.values[0] if not ca_max.empty else None)
            p = p_val.values[0] if not p_val.empty else None
            
            if pd.notna(ca) and pd.notna(p) and p > 0:
                ratio = ca / p
                if ratio < 0.9 or ratio > 4.5:
                    print(f"[FINAL SANITY BARRIER] Razão Ca:P bizarra ({ratio:.2f}) no produto {product_id}. Anulando minerais.")
                    df.loc[prod_mask & (df["nutrient_name"].isin(["calcium_min_mgkg", "calcium_max_mgkg", "phosphorus_mgkg"])), "nutrient_value"] = None

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
            # Em modo incremental/price, não apagamos nada para garantir a integridade do DW
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
