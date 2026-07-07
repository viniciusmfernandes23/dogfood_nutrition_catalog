from __future__ import annotations

from app.normalization.models import (
    NormalizationResult,
    NormalizationRule,
    NormalizedNutrient,
    ValidationStatus,
)
from app.normalization.rules import (
    GKG_TO_MGKG_FACTOR,
    PERCENT_TO_GKG_FACTOR,
    PERCENT_TO_MGKG_FACTOR,
    get_confidence,
)
from app.normalization.validator import Validator


class Resolver:
    """
    Resolve automaticamente problemas de escala
    utilizando as regras definidas para cada nutriente.
    """

    def __init__(self) -> None:
        self.validator = Validator()

    def resolve(
        self,
        nutrient: NormalizedNutrient,
        rule: NormalizationRule | None = None,
    ) -> NormalizedNutrient:

        if nutrient.value is None:
            nutrient.status = ValidationStatus.MISSING
            nutrient.confidence = 0.0
            return nutrient

        if rule is None:
            return nutrient

        # 1. Prioridade absoluta: Unidade original detectada pelo parser
        if nutrient.original_unit:
            converted_value, rule_name = self._resolve_by_unit(
                nutrient.value, 
                nutrient.original_unit, 
                rule
            )
            if converted_value is not None and self.validator.is_valid(converted_value, rule):
                nutrient.original_value = nutrient.value
                nutrient.value = converted_value
                nutrient.status = ValidationStatus.AUTO_CORRECTED
                nutrient.rule_applied = f"unit_direct_{rule_name}"
                nutrient.confidence = 1.0  # Confiança máxima com unidade explícita
                return nutrient

        # 2. Se o valor já está no range, aceitamos (mas só se não houver unidade contraditória)
        if self.validator.is_valid(nutrient.value, rule):
            nutrient.status = ValidationStatus.NORMALIZED
            nutrient.rule_applied = "already_normalized"
            nutrient.confidence = get_confidence("already_normalized")
            return nutrient

        # 3. Fallback: Busca exaustiva por candidatos válidos
        candidates = self._build_candidates(nutrient.value, rule)
        candidates = self.validator.validate_candidates(candidates, rule)

        if self.validator.has_single_candidate(candidates):
            value, applied_rule = candidates[0]
            nutrient.original_value = nutrient.value
            nutrient.value = value
            nutrient.status = ValidationStatus.AUTO_CORRECTED
            nutrient.rule_applied = applied_rule
            nutrient.confidence = get_confidence(applied_rule)
            return nutrient

        if self.validator.has_multiple_candidates(candidates):
            # Se temos múltiplos candidatos e o valor original é MUITO baixo para minerais (ex: 2.0 mg/kg)
            # Provavelmente é g/kg ou %
            if rule.field.endswith("_mgkg") and nutrient.value < 50:
                # Prioriza g/kg para mg/kg (fator 1000) pois é o mais comum em rótulos brasileiros para minerais
                for val, rule_name in candidates:
                    if rule_name == "gkg_to_mgkg":
                        nutrient.original_value = nutrient.value
                        nutrient.value = val
                        nutrient.status = ValidationStatus.AUTO_CORRECTED
                        nutrient.rule_applied = "heuristic_low_mineral_gkg"
                        nutrient.confidence = 0.9
                        return nutrient

            nutrient.status = ValidationStatus.AMBIGUOUS
            nutrient.rule_applied = "ambiguous"
            nutrient.confidence = get_confidence("ambiguous")
            return nutrient

        nutrient.status = ValidationStatus.IMPLAUSIBLE
        nutrient.rule_applied = "implausible"
        nutrient.confidence = get_confidence("implausible")
        return nutrient

    def resolve_value(
        self,
        value: float | None,
        rule: NormalizationRule,
        original_unit: str | None = None,
    ) -> NormalizationResult:
        nutrient = NormalizedNutrient(
            name=rule.field,
            value=value,
            unit="mg/kg" if rule.field.endswith("_mgkg") else "g/kg",
            original_unit=original_unit
        )

        nutrient = self.resolve(nutrient, rule)

        return NormalizationResult(
            field=rule.field,
            original_value=nutrient.original_value,
            normalized_value=nutrient.value,
            rule_applied=nutrient.rule_applied,
            status=nutrient.status,
            confidence=nutrient.confidence,
            changed=(
                nutrient.original_value != nutrient.value
                if nutrient.original_value is not None
                else False
            ),
        )

    def _resolve_by_unit(
        self, 
        value: float, 
        unit: str, 
        rule: NormalizationRule
    ) -> tuple[float | None, str | None]:
        target_is_mgkg = rule.field.endswith("_mgkg")
        
        if unit == "%":
            if target_is_mgkg:
                return value * PERCENT_TO_MGKG_FACTOR, "percent_to_mgkg"
            return value * PERCENT_TO_GKG_FACTOR, "percent_to_gkg"
            
        if unit == "g/kg":
            if target_is_mgkg:
                return value * GKG_TO_MGKG_FACTOR, "gkg_to_mgkg"
            return value, "already_gkg"
            
        if unit == "mg/kg":
            if target_is_mgkg:
                return value, "already_mgkg"
            return value / GKG_TO_MGKG_FACTOR, "mgkg_to_gkg"
            
        return None, None

    def _build_candidates(
        self,
        value: float,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:
        candidates: list[tuple[float, str]] = []

        if rule.overscale_factor:
            candidates.append((value / rule.overscale_factor, "overscale"))

        if rule.decimal_shift_factor:
            candidates.append((value * rule.decimal_shift_factor, "decimal_shift"))

        if rule.percent_factor:
            candidates.append((value * rule.percent_factor, "percent_conversion"))

        if rule.gkg_to_mgkg:
            candidates.append((value * GKG_TO_MGKG_FACTOR, "gkg_to_mgkg"))

        return candidates


NormalizationResolver = Resolver
