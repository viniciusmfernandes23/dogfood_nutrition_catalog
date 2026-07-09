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
        Realiza validações cruzadas para garantir a integridade biológica do produto.
        """
        # 1. Inversão Mínimo vs Máximo (Cálcio)
        ca_min = df.at[index, "calcium_min_mgkg"]
        ca_max = df.at[index, "calcium_max_mgkg"]
        if pd.notna(ca_min) and pd.notna(ca_max) and ca_min > ca_max:
            print(f"[BIOLOGICAL AUDIT] Inversão Ca Min/Max detectada no produto {product_id}. Trocando valores.")
            df.at[index, "calcium_min_mgkg"], df.at[index, "calcium_max_mgkg"] = ca_max, ca_min

        # 2. Soma de Macronutrientes (Proteína + Gordura + Fibra + Cinzas <= 1000 g/kg)
        macros = ["protein_gkg", "fat_gkg", "fiber_gkg", "ash_gkg"]
        macro_sum = sum(df.at[index, m] for m in macros if pd.notna(df.at[index, m]))
        if macro_sum > 1000:
            print(f"[BIOLOGICAL AUDIT] Soma de macros ({macro_sum}g/kg) impossível no produto {product_id}. Anulando valores suspeitos.")
            for m in macros:
                if pd.notna(df.at[index, m]) and df.at[index, m] > 600: # Valor individual bizarro
                    df.at[index, m] = None

        # 3. Razão Cálcio : Fósforo (Ideal 1:1 a 2:1)
        # Se Ca:P < 0.5 ou Ca:P > 3.0, há algo muito errado (exceto dietas específicas)
        p = df.at[index, "phosphorus_mgkg"]
        ca = df.at[index, "calcium_min_mgkg"] or df.at[index, "calcium_max_mgkg"]
        if pd.notna(ca) and pd.notna(p) and p > 0:
            ratio = ca / p
            if ratio < 0.5 or ratio > 4.0:
                print(f"[BIOLOGICAL AUDIT] Razão Ca:P bizarra ({ratio:.2f}) no produto {product_id}. Sinalizando para revisão.")
                # Não anulamos automaticamente aqui para evitar perda de dados legítimos, 
                # mas poderíamos anular se ratio > 10 por exemplo.

        # 4. Coerência Energia vs Umidade
        # Umidade > 70% (700g/kg) -> Energia raramente > 2000 kcal/kg (exceto se for gordura pura)
        moisture = df.at[index, "moisture_gkg"]
        energy = df.at[index, "metabolizable_energy_kcalkg"]
        if pd.notna(moisture) and pd.notna(energy):
            if moisture > 700 and energy > 2500:
                print(f"[BIOLOGICAL AUDIT] Inconsistência Energia/Umidade no produto {product_id} ({moisture}g/kg umidade e {energy}kcal/kg).")
                # Se umidade é 85% e energia é 4000, provavelmente a energia é 400 (por porção) ou 4000 (base seca).
                # Como o padrão do catálogo é base úmida, dividimos por 10 se for > 2500 em ração úmida.
                if energy > 2500:
                    df.at[index, "metabolizable_energy_kcalkg"] = round(energy / 10.0, 2)

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
                }
                for log
                in report.logs
            ]
        )

    @staticmethod
    def generate_summary(
        report: DatasetNormalizationReport,
    ) -> dict[str, int | float]:

        return {
            "processed_records": report.processed_records,
            "changed_records": report.changed_records,
            "unchanged_records": report.unchanged_records,
            "auto_corrected_records": report.auto_corrected_records,
            "manual_review_records": report.manual_review_records,
            "ambiguous_records": report.ambiguous_records,
            "implausible_records": report.implausible_records,
            "success_rate": report.success_rate,
        }
