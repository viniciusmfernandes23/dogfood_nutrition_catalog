from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import pandas as pd

from app.normalization.models import (
    DatasetNormalizationReport,
    NormalizationLog,
    ValidationStatus,
)
from app.normalization.resolver import Resolver
from app.normalization.rules import (
    NORMALIZABLE_FIELDS,
    get_rule,
)


class NormalizationEngine:
    """
    Engine responsável por aplicar a normalização
    dos nutrientes em DataFrames e Series.
    """

    def __init__(self) -> None:
        self.resolver = Resolver()

    def _normalize_fields(
        self,
        df: pd.DataFrame,
        index: int,
        row: pd.Series,
        fields: Sequence[str],
        report: DatasetNormalizationReport,
        product_id_column: str,
    ) -> None:

        product_id = row.get(product_id_column, -1)
        row_changed = False

        for field in fields:
            rule = get_rule(field)
            if rule is None:
                continue

            # Tenta obter a unidade original de várias formas
            original_unit = None
            
            # 1. Busca por {field}_unit (ex: sodium_mgkg_unit)
            unit_col_full = f"{field}_unit"
            # 2. Busca por {base_name}_unit (ex: sodium_unit)
            base_name = field.split('_')[0]
            unit_col_base = f"{base_name}_unit"
            # 3. Busca por {base_name}_{suffix}_unit (ex: calcium_min_unit)
            unit_col_special = None
            if "_min_" in field:
                unit_col_special = f"{base_name}_min_unit"
            elif "_max_" in field:
                unit_col_special = f"{base_name}_max_unit"
            elif "metabolizable_energy" in field:
                unit_col_special = "metabolizable_energy_unit"
            
            if unit_col_full in row and pd.notna(row.get(unit_col_full)):
                original_unit = row.get(unit_col_full)
            elif unit_col_special and unit_col_special in row and pd.notna(row.get(unit_col_special)):
                original_unit = row.get(unit_col_special)
            elif unit_col_base in row and pd.notna(row.get(unit_col_base)):
                original_unit = row.get(unit_col_base)

            current_value = row.get(field)
            
            # Trava de Segurança: Se o valor já estiver no range plausível, 
            # ignoramos a unidade original para evitar re-multiplicação indevida
            # (Ex: se o valor é 1700 e a unidade é %, não multiplicamos por 10000 de novo)
            if pd.notna(current_value) and rule.target_min <= current_value <= rule.target_max:
                original_unit = None

            result = self.resolver.resolve_value(
                value=current_value,
                rule=rule,
                original_unit=original_unit
            )

            df.at[index, field] = result.normalized_value

            report.add_log(
                NormalizationLog(
                    product_id=product_id,
                    field=field,
                    original_value=result.original_value,
                    normalized_value=result.normalized_value,
                    rule_applied=result.rule_applied,
                    status=result.status,
                    confidence_score=result.confidence,
                )
            )

            self._update_statistics(report, result.status)
            if result.changed:
                row_changed = True

        if row_changed:
            report.changed_records += 1
        else:
            report.unchanged_records += 1
            
        # Auditoria de Coerência Nutricional (v1.3.0)
        self._audit_biological_coherence(df, index, product_id)

    def _audit_biological_coherence(self, df: pd.DataFrame, index: int, product_id: Any) -> None:
        """
        Realiza validações cruzadas rigorosas para garantir a integridade biológica do produto.
        v1.3.1: Foco em anulação de dados impossíveis e âncora de umidade.
        """
        # 1. Inversão Mínimo vs Máximo (Cálcio)
        ca_min = df.at[index, "calcium_min_mgkg"]
        ca_max = df.at[index, "calcium_max_mgkg"]
        if pd.notna(ca_min) and pd.notna(ca_max) and ca_min > ca_max:
            print(f"[BIOLOGICAL AUDIT] Inversão Ca Min/Max detectada no produto {product_id}. Trocando valores.")
            df.at[index, "calcium_min_mgkg"], df.at[index, "calcium_max_mgkg"] = ca_max, ca_min

        # 2. Soma de Macronutrientes (Proteína + Gordura + Fibra + Cinzas + Umidade <= 1000 g/kg)
        macros_all = ["protein_gkg", "fat_gkg", "fiber_gkg", "ash_gkg", "moisture_gkg"]
        macro_sum = sum(df.at[index, m] for m in macros_all if pd.notna(df.at[index, m]))
        if macro_sum > 1050: # Tolerância de 5% para erros de arredondamento em rótulos
            print(f"[BIOLOGICAL AUDIT] Soma total de nutrientes ({macro_sum}g/kg) impossível no produto {product_id}. Anulando linha nutricional.")
            for m in macros_all:
                df.at[index, m] = None
            df.at[index, "metabolizable_energy_kcalkg"] = None
            return # Interrompe auditoria para esta linha já invalidada

        # 3. Âncora de Umidade vs Energia (Rações Úmidas)
        moisture = df.at[index, "moisture_gkg"]
        energy = df.at[index, "metabolizable_energy_kcalkg"]
        if pd.notna(moisture) and pd.notna(energy):
            # Regra de Ouro: Umidade > 70% -> Energia Máxima 1.500 kcal/kg
            if moisture > 700 and energy > 1500:
                print(f"[BIOLOGICAL AUDIT] Energia Impossível para Ração Úmida ({energy} kcal/kg com {moisture}g/kg umidade) no produto {product_id}.")
                # Se for > 6000 (limite físico absoluto), anulamos. Se for intermediário, tentamos dividir por 10.
                if energy > 6000:
                    df.at[index, "metabolizable_energy_kcalkg"] = None
                else:
                    df.at[index, "metabolizable_energy_kcalkg"] = round(energy / 10.0, 2)

        # 4. Limite Físico Absoluto de Energia (Gordura pura = 9000 kcal/kg)
        if pd.notna(energy):
            if energy > 9000:
                print(f"[BIOLOGICAL AUDIT] Energia excede limite físico da matéria orgânica ({energy} kcal/kg) no produto {product_id}. Anulando.")
                df.at[index, "metabolizable_energy_kcalkg"] = None
            elif energy < 100:
                print(f"[BIOLOGICAL AUDIT] Energia abaixo do limite mínimo plausível ({energy} kcal/kg) no produto {product_id}. Anulando.")
                df.at[index, "metabolizable_energy_kcalkg"] = None

        # 5. Coerência Cinzas vs Minerais
        ash = df.at[index, "ash_gkg"]
        minerals_mgkg = ["sodium_mgkg", "potassium_mgkg", "calcium_max_mgkg", "phosphorus_mgkg"]
        minerals_sum_gkg = sum(df.at[index, m] / 1000.0 for m in minerals_mgkg if pd.notna(df.at[index, m]))
        if pd.notna(ash) and minerals_sum_gkg >= ash: # A soma dos minerais não deve exceder o teor de cinzas
            print(f"[BIOLOGICAL AUDIT] Soma de minerais ({minerals_sum_gkg}g/kg) excede cinzas ({ash}g/kg) no produto {product_id}. Anulando minerais suspeitos.")
            for m in minerals_mgkg:
                df.at[index, m] = None

        # 6. Razão Cálcio : Fósforo (Auditoria de Toxicidade/Deficiência)
        p = df.at[index, "phosphorus_mgkg"]
        ca = df.at[index, "calcium_min_mgkg"] or df.at[index, "calcium_max_mgkg"]
        if pd.notna(ca) and pd.notna(p) and p > 0:
            ratio = ca / p
            if ratio < 0.4 or ratio > 5.0:
                print(f"[BIOLOGICAL AUDIT] Razão Ca:P bizarra ({ratio:.2f}) no produto {product_id}. Anulando minerais suspeitos.")
                df.at[index, "calcium_min_mgkg"] = None
                df.at[index, "calcium_max_mgkg"] = None
                df.at[index, "phosphorus_mgkg"] = None

        # 7. Trava de Toxicidade para Minerais (Sódio/Potássio)
        for mineral in ["sodium_mgkg", "potassium_mgkg"]:
            val = df.at[index, mineral]
            if pd.notna(val) and val > 60000: # 6% de mineral é letal/impossível
                print(f"[BIOLOGICAL AUDIT] Nível tóxico/impossível de {mineral} ({val} mg/kg) no produto {product_id}. Anulando.")
                df.at[index, mineral] = None


    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        product_id_column: str = "product_id",
    ) -> tuple[pd.DataFrame, DatasetNormalizationReport]:

        df = df.copy()
        report = DatasetNormalizationReport()

        fields = [
            field
            for field
            in NORMALIZABLE_FIELDS
            if field in df.columns
        ]

        for index, row in df.iterrows():
            report.processed_records += 1
            self._normalize_fields(
                df=df,
                index=index,
                row=row,
                fields=fields,
                report=report,
                product_id_column=product_id_column,
            )

        return df, report

    def normalize_columns(
        self,
        df: pd.DataFrame,
        columns: Iterable[str] | None = None,
        product_id_column: str = "product_id",
    ) -> tuple[pd.DataFrame, DatasetNormalizationReport]:

        df = df.copy()
        report = DatasetNormalizationReport()

        if columns is None:
            fields = [
                field
                for field
                in NORMALIZABLE_FIELDS
                if field in df.columns
            ]
        else:
            fields = [
                field
                for field
                in columns
                if field in df.columns
            ]

        for index, row in df.iterrows():
            report.processed_records += 1
            self._normalize_fields(
                df=df,
                index=index,
                row=row,
                fields=fields,
                report=report,
                product_id_column=product_id_column,
            )

        return df, report

    def normalize_series(
        self,
        series: pd.Series,
        field: str,
    ) -> pd.Series:

        rule = get_rule(field)
        if rule is None:
            return series.copy()

        return pd.Series(
            [
                self.resolver.resolve_value(
                    value=value,
                    rule=rule,
                ).normalized_value
                for value
                in series
            ],
            index=series.index,
            dtype=series.dtype,
        )

    @staticmethod
    def _update_statistics(
        report: DatasetNormalizationReport,
        status: ValidationStatus,
    ) -> None:

        if status == ValidationStatus.NORMALIZED:
            return

        if status == ValidationStatus.AUTO_CORRECTED:
            report.auto_corrected_records += 1
        elif status == ValidationStatus.REVIEW:
            report.manual_review_records += 1
        elif status == ValidationStatus.AMBIGUOUS:
            report.ambiguous_records += 1
        elif status == ValidationStatus.IMPLAUSIBLE:
            report.implausible_records += 1

    @staticmethod
    def generate_logs_dataframe(
        report: DatasetNormalizationReport,
    ) -> pd.DataFrame:

        if not report.logs:
            return pd.DataFrame()

        return pd.DataFrame(
            [
                {
                    "product_id": log.product_id,
                    "field": log.field,
                    "original_value": log.original_value,
                    "normalized_value": log.normalized_value,
                    "rule_applied": log.rule_applied,
                    "status": log.status.value,
                    "confidence_score": log.confidence_score,
                }
                for log
                in report.logs
            ]
        )

    @staticmethod
    def generate_summary(
        report: DatasetNormalizationReport,
    ) -> dict[str, Any]:

        summary = {
            "processed_records": report.processed_records,
            "changed_records": report.changed_records,
            "unchanged_records": report.unchanged_records,
            "auto_corrected_records": report.auto_corrected_records,
            "nullified_records": report.nullified_records,
            "manual_review_records": report.manual_review_records,
            "ambiguous_records": report.ambiguous_records,
            "implausible_records": report.implausible_records,
            "success_rate": report.success_rate,
            "nutrient_nullification_rates": {}
        }
        
        for nutrient, stats in report.nutrient_stats.items():
            if stats["processed"] > 0:
                rate = round((stats["nullified"] / stats["processed"]) * 100, 2)
                summary["nutrient_nullification_rates"][nutrient] = f"{rate}%"
                
        return summary
