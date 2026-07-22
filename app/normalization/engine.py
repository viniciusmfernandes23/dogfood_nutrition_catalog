from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np
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
    Motor principal de normalização nutricional.
    
    Responsável por coordenar a resolução de escalas, conversão de unidades 
    e aplicação de auditorias biológicas em conjuntos de dados de produtos.
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
        """
        Normaliza individualmente cada campo nutricional de uma linha do DataFrame.
        """
        product_id = row.get(product_id_column, -1)
        row_changed = False

        # Identifica categorias especiais que possuem limites biológicos diferenciados
        product_category = str(row.get("product_category", "")).lower()
        is_treat_or_supp = any(x in product_category for x in ["petisco", "snack", "suplemento", "complementar"])

        for field in fields:
            rule = get_rule(field)
            if rule is None:
                continue

            # Mapeamento dinâmico da coluna de unidade original
            original_unit = None
            unit_col_full = f"{field}_unit"
            base_name = field.split('_')[0]
            unit_col_base = f"{base_name}_unit"
            unit_col_special = None
            
            if "_min_" in field:
                unit_col_special = f"{base_name}_min_unit"
            elif "_max_" in field:
                unit_col_special = f"{base_name}_max_unit"
            elif "metabolizable_energy" in field:
                unit_col_special = "metabolizable_energy_unit"
            
            if unit_col_special and unit_col_special in row and pd.notna(row.get(unit_col_special)):
                original_unit = row.get(unit_col_special)
            elif unit_col_full in row and pd.notna(row.get(unit_col_full)):
                original_unit = row.get(unit_col_full)
            elif unit_col_base in row and pd.notna(row.get(unit_col_base)):
                original_unit = row.get(unit_col_base)

            current_value = row.get(field)
            
            # Executa a resolução lógica do valor (unidade + escala)
            result = self.resolver.resolve_value(
                value=current_value,
                rule=rule,
                original_unit=original_unit,
                is_treat_or_supp=is_treat_or_supp
            )

            # Atualiza o DataFrame com os resultados da normalização e auditoria
            df.at[index, field] = result.normalized_value
            df.at[index, f"{field}_original"] = result.original_value
            df.at[index, f"{field}_unit"] = result.original_unit
            df.at[index, f"{field}_status"] = result.status
            df.at[index, f"{field}_rule"] = result.rule_applied
            df.at[index, f"{field}_reason"] = result.status if result.status in [
                ValidationStatus.IMPLAUSIBLE, 
                ValidationStatus.AMBIGUOUS,
                ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_SOURCE,
                ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_ENERGY
            ] else None

            # Registra no relatório de execução
            report.add_log(
                NormalizationLog(
                    product_id=product_id,
                    field=field,
                    original_value=result.original_value,
                    original_unit=result.original_unit,
                    normalized_value=result.normalized_value,
                    normalized_unit=result.normalized_unit,
                    rule_applied=result.rule_applied,
                    status=result.status,
                    reason=result.reason,
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
            
        # Após normalizar campos individuais, aplica validações cruzadas (Balanço de Massa, Ca:P)
        self._audit_biological_coherence(df, index, product_id)

    def _audit_biological_coherence(self, df: pd.DataFrame, index: int, product_id: Any) -> None:
        """
        Validações biológicas cruzadas:
        1. Consistência de limites (Min vs Max).
        2. Balanço de Massa (Soma de proximais entre 800-1050 g/kg).
        3. Razão Cálcio:Fósforo (Idealmente entre 1:1 e 2:1).
        4. Verificação de toxicidade/insignificância para microminerais.
        """
        product_category = str(df.at[index, "product_category"]).lower() if "product_category" in df.columns else ""
        is_treat_or_supp = any(x in product_category for x in ["petisco", "snack", "suplemento", "complementar"])

        # Garante existência das colunas necessárias para o cálculo
        required_cols = [
            "protein_gkg", "fat_gkg", "fiber_gkg", "ash_gkg", "moisture_gkg",
            "calcium_min_mgkg", "calcium_max_mgkg", "phosphorus_mgkg",
            "sodium_mgkg", "potassium_mgkg", "metabolizable_energy_kcalkg"
        ]
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        # 1. Inversão Mínimo vs Máximo
        ca_min = df.at[index, "calcium_min_mgkg"]
        ca_max = df.at[index, "calcium_max_mgkg"]
        if pd.notna(ca_min) and pd.notna(ca_max) and ca_min > ca_max:
            df.at[index, "calcium_min_mgkg"], df.at[index, "calcium_max_mgkg"] = ca_max, ca_min

        # 2. Balanço de Massa (Ignorado para Petiscos/Suplementos)
        if not is_treat_or_supp:
            macros_all = ["protein_gkg", "fat_gkg", "fiber_gkg", "ash_gkg", "moisture_gkg"]
            present_macros = [m for m in macros_all if pd.notna(df.at[index, m])]
            
            # Aplica barreira se houver dados suficientes (>= 4 macros)
            if len(present_macros) >= 4:
                macro_sum = sum(float(df.at[index, m]) for m in present_macros)
                min_sum = 800 if len(present_macros) == 5 else 600 
                
                if macro_sum < min_sum or macro_sum > 1050:
                    print(f"[BIOLOGICAL AUDIT] Falha no balanço de massa ({macro_sum}g/kg) no produto {product_id}.")
                    for m in macros_all:
                        df.at[index, m] = np.nan
                        df.at[index, f"{m}_status"] = ValidationStatus.PRODUCT_MASS_BALANCE_FAILED
                        df.at[index, f"{m}_reason"] = f"Mass balance failed: {macro_sum}g/kg"
                    
                    # Anula energia em caso de falha grave no balanço de massa
                    df.at[index, "metabolizable_energy_kcalkg"] = None
                    df.at[index, "metabolizable_energy_kcalkg_status"] = ValidationStatus.PRODUCT_MASS_BALANCE_FAILED
                    df.at[index, "metabolizable_energy_kcalkg_reason"] = f"Mass balance failed: {macro_sum}g/kg"
                    return 

        # 3. Razão Cálcio:Fósforo
        p = df.at[index, "phosphorus_mgkg"]
        ca_min_val = df.at[index, "calcium_min_mgkg"]
        ca_max_val = df.at[index, "calcium_max_mgkg"]
        
        if pd.notna(p) and (pd.notna(ca_min_val) or pd.notna(ca_max_val)) and p > 0:
            ca = ca_min_val if pd.notna(ca_min_val) else ca_max_val
            ratio = ca / p
            if ratio < 1.0 or ratio > 2.0:
                print(f"[BIOLOGICAL AUDIT] Razão Ca:P inválida ({ratio:.2f}) no produto {product_id}.")
                reason = f"Invalid Ca:P ratio: {ratio:.2f}"
                for field in ["calcium_min_mgkg", "calcium_max_mgkg", "phosphorus_mgkg"]:
                    df.at[index, f"{field}_status"] = ValidationStatus.INVALID_CA_P_RATIO
                    df.at[index, f"{field}_reason"] = reason
                    df.at[index, field] = None

        # 4. Limites Biológicos para Microminerais
        multiplier = 3.0 if is_treat_or_supp else 1.0
        minerals = ["sodium_mgkg", "potassium_mgkg", "magnesium_mgkg", "zinc_mgkg", "copper_mgkg", "selenium_mgkg", "iodine_mgkg", "manganese_mgkg"]
        
        for mineral in minerals:
            if mineral in df.columns:
                val = df.at[index, mineral]
                if pd.notna(val):
                    rule = get_rule(mineral)
                    if rule and (val < rule.target_min or val > (rule.target_max * multiplier)):
                        print(f"[BIOLOGICAL AUDIT] Mineral fora da faixa: {mineral}={val}")
                        df.at[index, f"{mineral}_status"] = ValidationStatus.IMPLAUSIBLE
                        df.at[index, f"{mineral}_reason"] = f"Biological limit exceeded: {val}"
                        df.at[index, mineral] = None

    def normalize_dataframe(
        self,
        df: pd.DataFrame,
        product_id_column: str = "product_id",
    ) -> tuple[pd.DataFrame, DatasetNormalizationReport]:
        """
        Normaliza um DataFrame completo.
        """
        df = df.copy()
        report = DatasetNormalizationReport()

        fields = [field for field in NORMALIZABLE_FIELDS if field in df.columns]

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
        """
        Normaliza apenas colunas específicas de um DataFrame.
        """
        df = df.copy()
        report = DatasetNormalizationReport()

        if columns is None:
            fields = [field for field in NORMALIZABLE_FIELDS if field in df.columns]
        else:
            fields = [field for field in columns if field in df.columns]

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
        """
        Normaliza uma Series individual.
        """
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
        """
        Atualiza as métricas de execução no relatório.
        """
        if status == ValidationStatus.NORMALIZED:
            return

        if status == ValidationStatus.AUTO_CORRECTED:
            report.auto_corrected_records += 1
        elif status == ValidationStatus.REVIEW:
            report.manual_review_records += 1
        elif status == ValidationStatus.AMBIGUOUS:
            report.ambiguous_records += 1
        elif status in [
            ValidationStatus.IMPLAUSIBLE, 
            ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_SOURCE, 
            ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_ENERGY,
            ValidationStatus.PRODUCT_MASS_BALANCE_FAILED,
            ValidationStatus.INVALID_CA_P_RATIO
        ]:
            report.implausible_records += 1

    @staticmethod
    def generate_logs_dataframe(
        report: DatasetNormalizationReport,
    ) -> pd.DataFrame:
        """
        Converte os logs do relatório em um DataFrame para exportação.
        """
        if not report.logs:
            return pd.DataFrame()

        return pd.DataFrame(
            [
                {
                    "product_id": log.product_id,
                    "field": log.field,
                    "original_value": log.original_value,
                    "original_unit": log.original_unit,
                    "normalized_value": log.normalized_value,
                    "normalized_unit": log.normalized_unit,
                    "rule_applied": log.rule_applied,
                    "status": log.status,
                    "reason": log.reason,
                    "confidence_score": log.confidence_score,
                }
                for log in report.logs
            ]
        )
