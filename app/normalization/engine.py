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
