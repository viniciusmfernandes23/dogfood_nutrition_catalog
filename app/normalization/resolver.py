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

        # Prioridade 1.1: Validar percentuais antes da conversão
        if nutrient.original_unit == "%":
            if nutrient.value < 0 or nutrient.value > 100:
                print(f"[AUDIT] Valor percentual implausível: {nutrient.value}%")
                nutrient.original_value = nutrient.value
                nutrient.value = None
                nutrient.status = ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_SOURCE
                nutrient.rule_applied = "invalid_percent_range"
                nutrient.confidence = 0.0
                return nutrient

        # Proteção e Auto-Correção de valores astronômicos
        if nutrient.value > 100_000:
            temp_value = nutrient.value
            for factor in [10000.0, 1000.0, 10.0]:
                test_val = nutrient.value
                for _ in range(4):
                    test_val /= factor
                    if self.validator.is_valid(test_val, rule):
                        nutrient.original_value = nutrient.value
                        nutrient.value = round(float(test_val), 2)
                        nutrient.status = ValidationStatus.AUTO_CORRECTED
                        nutrient.rule_applied = f"fix_accumulated_scale_{int(factor)}"
                        nutrient.confidence = 1.0
                        return nutrient
            
            nutrient.original_value = nutrient.value
            nutrient.value = None
            nutrient.status = ValidationStatus.IMPLAUSIBLE
            nutrient.rule_applied = "nullified_extreme_value"
            nutrient.confidence = 0.0
            return nutrient

        if rule is None:
            return nutrient

        target_is_kcalkg = rule.field.endswith("_kcalkg")
        target_is_uikg = rule.field.endswith("_uikg")

        # 1. Fluxo Determinístico para Energia Metabolizável
        if target_is_kcalkg:
            if not nutrient.original_unit:
                nutrient.original_value = nutrient.value
                nutrient.value = None
                nutrient.status = ValidationStatus.IMPLAUSIBLE
                nutrient.rule_applied = "missing_energy_unit"
                nutrient.confidence = 0.0
                return nutrient

            converted_value, rule_name = self._resolve_by_unit(
                nutrient.value, 
                nutrient.original_unit, 
                rule
            )

            if rule_name and "invalid" in rule_name:
                nutrient.original_value = nutrient.value
                nutrient.value = None
                nutrient.status = ValidationStatus.IMPLAUSIBLE
                nutrient.rule_applied = rule_name
                nutrient.confidence = 0.0
                return nutrient

            if converted_value is not None:
                if 500 <= converted_value <= 9000:
                    nutrient.original_value = nutrient.value
                    nutrient.value = round(float(converted_value), 5)
                    nutrient.status = ValidationStatus.NORMALIZED
                    nutrient.rule_applied = f"unit_conv_{rule_name}"
                    nutrient.confidence = 1.0
                else:
                    nutrient.original_value = nutrient.value
                    nutrient.value = None
                    nutrient.status = ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_ENERGY
                    nutrient.rule_applied = "biologically_implausible_energy"
                    nutrient.confidence = 0.0
                return nutrient

        # 2. Fluxo Padrão para outros nutrientes
        # Se a unidade original for impossível para este nutriente (ex: Magnésio em kcal/kg ou ui/kg)
        # devemos anular IMEDIATAMENTE antes de qualquer outra lógica.
        if nutrient.original_unit in ["kcal/kg", "ui/kg", "kcal/100g", "mj/kg"]:
             if not (target_is_kcalkg or target_is_uikg):
                print(f"[AUDIT] Unidade impossível ({nutrient.original_unit}) para {rule.field}. Anulando.")
                nutrient.original_value = nutrient.value
                nutrient.value = None
                nutrient.status = ValidationStatus.IMPLAUSIBLE
                nutrient.rule_applied = f"invalid_unit_{nutrient.original_unit.replace('/', '')}"
                nutrient.confidence = 0.0
                return nutrient

        # Se a unidade original for igual à unidade alvo e o valor é válido
        if nutrient.original_unit == nutrient.unit and self.validator.is_valid(nutrient.value, rule):
            nutrient.status = ValidationStatus.NORMALIZED
            nutrient.rule_applied = "already_normalized"
            nutrient.confidence = get_confidence("already_normalized")
            return nutrient

        # 3. Prioridade: Unidade original detectada pelo parser
        if nutrient.original_unit:
            converted_value, rule_name = self._resolve_by_unit(
                nutrient.value, 
                nutrient.original_unit, 
                rule
            )

            if converted_value is not None:
                # Se a unidade é explícita, a conversão DEVE ser válida.
                # Não existe mais "already_normalized_despite_unit_conflict".
                if self.validator.is_valid(converted_value, rule):
                    nutrient.original_value = nutrient.value
                    nutrient.value = round(float(converted_value), 5)
                    nutrient.status = ValidationStatus.AUTO_CORRECTED
                    nutrient.rule_applied = f"unit_direct_{rule_name}"
                    nutrient.confidence = 1.0
                    return nutrient
                else:
                    # Se a conversão por unidade falhou, o dado é incoerente.
                    print(f"[AUDIT] Conflito de unidade em {rule.field}: {nutrient.value} {nutrient.original_unit} -> {converted_value} {nutrient.unit} (INVÁLIDO)")
                    nutrient.original_value = nutrient.value
                    nutrient.value = None
                    nutrient.status = ValidationStatus.IMPLAUSIBLE
                    nutrient.rule_applied = f"invalid_conversion_{rule_name}"
                    nutrient.confidence = 0.0
                    return nutrient

        # 4. Fallback: Se não houver unidade ou unidade falhou, tenta heurísticas apenas se o valor for válido
        if self.validator.is_valid(nutrient.value, rule):
            nutrient.status = ValidationStatus.NORMALIZED
            nutrient.rule_applied = "already_normalized"
            nutrient.confidence = get_confidence("already_normalized")
            return nutrient

        # 5. Busca exaustiva por candidatos válidos (Heurísticas de escala)
        candidates = self._build_candidates(nutrient, rule)
        candidates = self.validator.validate_candidates(candidates, rule)

        if self.validator.has_single_candidate(candidates):
            value, applied_rule = candidates[0]
            nutrient.original_value = nutrient.value
            nutrient.value = round(float(value), 5)
            nutrient.status = ValidationStatus.AUTO_CORRECTED
            nutrient.rule_applied = applied_rule
            nutrient.confidence = get_confidence(applied_rule)
            return nutrient

        if self.validator.has_multiple_candidates(candidates):
            nutrient.status = ValidationStatus.AMBIGUOUS
            nutrient.rule_applied = "ambiguous"
            nutrient.confidence = get_confidence("ambiguous")
            return nutrient

        # Se não houver candidatos válidos, anula
        nutrient.original_value = nutrient.value
        nutrient.value = None
        nutrient.status = ValidationStatus.IMPLAUSIBLE
        nutrient.rule_applied = "implausible"
        nutrient.confidence = get_confidence("implausible")
        return nutrient

    def resolve_value(
        self,
        value: float | None,
        rule: NormalizationRule,
        original_unit: str | None = None,
        is_treat_or_supp: bool = False,
    ) -> NormalizationResult:
        
        target_unit = "g/kg"
        if rule.field.endswith("_mgkg"):
            target_unit = "mg/kg"
        elif rule.field.endswith("_kcalkg"):
            target_unit = "kcal/kg"
        elif rule.field.endswith("_uikg"):
            target_unit = "UI/kg"
            
        nutrient = NormalizedNutrient(
            name=rule.field,
            value=value,
            unit=target_unit,
            original_unit=original_unit
        )

        if is_treat_or_supp:
            from dataclasses import replace as dc_replace
            # Flexibiliza limites para petiscos/suplementos
            modified_rule = dc_replace(rule, target_max=rule.target_max * 3.0)
            nutrient = self.resolve(nutrient, modified_rule)
        else:
            nutrient = self.resolve(nutrient, rule)

        return NormalizationResult(
            field=rule.field,
            original_value=nutrient.original_value if nutrient.original_value is not None else value,
            original_unit=original_unit,
            normalized_value=nutrient.value,
            normalized_unit=target_unit,
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
        target_is_kcalkg = rule.field.endswith("_kcalkg")
        target_is_uikg = rule.field.endswith("_uikg")

        if target_is_kcalkg:
            if unit == "kcal/kg":
                return value, "already_kcalkg"
            elif unit == "kcal/100g":
                return round(value * 10.0, 2), "kcal100g_to_kcalkg"
            elif unit == "mj/kg":
                return round(value * 239.006, 2), "mjkg_to_kcalkg"
            else:
                return None, "invalid_energy_unit"

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
            
        if unit == "ui/kg":
            if target_is_uikg:
                return value, "already_uikg"
            return None, "invalid_unit_uikg"

        if unit == "mcg":
            return value * 0.001, "mcg_to_mgkg"

        return None, None

    def _build_candidates(
        self,
        nutrient: NormalizedNutrient,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:
        value = nutrient.value
        candidates: list[tuple[float, str]] = []

        if rule.overscale_factor:
            candidates.append((value / rule.overscale_factor, "overscale"))

        if rule.percent_factor:
            candidates.append((value * rule.percent_factor, "percent_conversion"))

        if rule.gkg_to_mgkg:
            candidates.append((value * GKG_TO_MGKG_FACTOR, "gkg_to_mgkg"))
            
        if rule.decimal_shift_factor:
            if nutrient.original_unit != nutrient.unit:
                candidates.append((value * rule.decimal_shift_factor, "decimal_shift"))
        
        if rule.decimal_shift_up:
            candidates.append((value * rule.decimal_shift_up, "decimal_shift_up"))

        if value > rule.target_max:
            candidates.append((value / 10.0, "fix_10x_scale"))
            candidates.append((value / 100.0, "fix_100x_scale"))

        return candidates


NormalizationResolver = Resolver
