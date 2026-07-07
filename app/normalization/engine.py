from __future__ import annotations

from collections.abc import Iterable, Sequence

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

    # ==========================================================
    # Core
    # ==========================================================

    def _normalize_fields(
        self,
        df: pd.DataFrame,
        index: int,
        row: pd.Series,
        fields: Sequence[str],
        report: DatasetNormalizationReport,
        product_id_column: str,
    ) -> None:

        product_id = row.get(
            product_id_column,
            -1,
        )

        row_changed = False

        for field in fields:

            rule = get_rule(field)

            if rule is None:
                continue

            result = self.resolver.resolve_value(
                value=row.get(field),
                rule=rule,
            )

            df.at[
                index,
                field,
            ] = result.normalized_value

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

            self._update_statistics(
                report,
                result.status,
            )

            if result.changed:
                row_changed = True

        if row_changed:

            report.changed_records += 1

        else:

            report.unchanged_records += 1

    # ==========================================================
    # DataFrame
    # ==========================================================

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        product_id_column: str = "product_id",
    ) -> tuple[
        pd.DataFrame,
        DatasetNormalizationReport,
    ]:

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

        return (

            df,

            report,

        )

    # ==========================================================
    # Colunas específicas
    # ==========================================================

    def normalize_columns(
        self,
        df: pd.DataFrame,
        columns: Iterable[str] | None = None,
        product_id_column: str = "product_id",
    ) -> tuple[
        pd.DataFrame,
        DatasetNormalizationReport,
    ]:

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

        return (

            df,

            report,

        )

    # ==========================================================
    # Series
    # ==========================================================

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

    # ==========================================================
    # Estatísticas
    # ==========================================================

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

    # ==========================================================
    # Exportações
    # ==========================================================

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