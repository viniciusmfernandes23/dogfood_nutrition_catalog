from __future__ import annotations
from typing import Iterable, Sequence

import pandas as pd

from app.normalization.models import DatasetNormalizationReport, NormalizationLog
from app.normalization.resolver import NormalizationResolver
from app.normalization.rules import NORMALIZABLE_FIELDS, get_rule


class NormalizationEngine:
    """
    Aplica a Rule Engine de normalização em DataFrames e Series.
    """

    def __init__(self) -> None:
        self.resolver = NormalizationResolver()

    # ============================================================
    # Core interno reutilizável
    # ============================================================

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
            result = self.resolver.resolve(value=row[field], rule=rule)

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

    # ============================================================
    # Normalização de DataFrame completo
    # ============================================================

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        product_id_column: str = "product_id",
    ) -> tuple[pd.DataFrame, DatasetNormalizationReport]:

        df = df.copy()
        report = DatasetNormalizationReport()

        fields = [f for f in NORMALIZABLE_FIELDS if f in df.columns]

        for index, row in df.iterrows():
            report.processed_records += 1
            self._normalize_fields(
                df,
                index,
                row,
                fields,
                report,
                product_id_column,
            )

        return df, report

    # ============================================================
    # Normalização de colunas específicas
    # ============================================================

    def normalize_columns(
        self,
        df: pd.DataFrame,
        columns: Iterable[str] | None = None,
        product_id_column: str = "product_id",
    ) -> tuple[pd.DataFrame, DatasetNormalizationReport]:

        df = df.copy()
        report = DatasetNormalizationReport()

        fields = (
            [c for c in columns if c in df.columns]
            if columns is not None
            else [f for f in NORMALIZABLE_FIELDS if f in df.columns]
        )

        for index, row in df.iterrows():
            report.processed_records += 1
            self._normalize_fields(
                df,
                index,
                row,
                fields,
                report,
                product_id_column,
            )

        return df, report

    # ============================================================
    # Normalização de Series
    # ============================================================

    def normalize_series(self, series: pd.Series, field: str) -> pd.Series:
        rule = get_rule(field)
        return pd.Series(
            [
                self.resolver.resolve(value=v, rule=rule).normalized_value
                for v in series
            ],
            index=series.index,
        )

    # ============================================================
    # Estatísticas
    # ============================================================

    @staticmethod
    def _update_statistics(report: DatasetNormalizationReport, status: str) -> None:
        if status == "normalized":
            return

        if status == "auto_corrected":
            report.auto_corrected_records += 1
        elif status == "manual_review":
            report.manual_review_records += 1
        elif status == "ambiguous":
            report.ambiguous_records += 1
        elif status == "implausible":
            report.implausible_records += 1

    # ============================================================
    # Logs e resumo
    # ============================================================

    def generate_logs_dataframe(self, report: DatasetNormalizationReport) -> pd.DataFrame:
        return pd.DataFrame([vars(log) for log in report.logs])

    def generate_summary(self, report: DatasetNormalizationReport) -> dict:
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
