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
    Componente responsável pela resolução lógica de valores nutricionais.
    
    Aplica heurísticas de escala, conversões de unidades e barreiras sanitárias 
    iniciais para garantir que os valores estejam em conformidade com as unidades 
    alvo (g/kg, mg/kg, kcal/kg ou UI/kg).
    """

    def __init__(self) -> None:
        self.validator = Validator()

    def resolve(
        self,
        nutrient: NormalizedNutrient,
        rule: NormalizationRule | None = None,
    ) -> NormalizedNutrient:
        """
        Aplica a lógica de resolução em um objeto NormalizedNutrient.
        """
        if nutrient.value is None:
            nutrient.status = ValidationStatus.MISSING
            nutrient.confidence = 0.0
            return nutrient

        # Barreira 1: Validação de percentuais antes da conversão
        if nutrient.original_unit == "%":
            if nutrient.value < 0 or nutrient.value > 100:
                nutrient.original_value = nutrient.value
                nutrient.value = None
                nutrient.status = ValidationStatus.BIOLOGICALLY_IMPLAUSIBLE_SOURCE
                nutrient.rule_applied = "invalid_percent_range"
                nutrient.confidence = 0.0
                return nutrient

        # Barreira 2: Proteção contra valores astronômicos (outliers extremos)
        # v1.5.0: Endurecido para evitar falsos positivos de escala.
        if nutrient.value > 1_000_000:
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

        # Fluxo Determinístico para Energia Metabolizável
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
                # v1.5.1: Tratamento de erro de escala 10x na energia (ex: 13780 -> 1378)
                if converted_value > 9000:
                    for factor in [10.0, 100.0]:
                        test_val = converted_value / factor
                        if 500 <= test_val <= 9000:
                            nutrient.original_value = nutrient.value
                            nutrient.value = round(float(test_val), 2)
                            nutrient.status = ValidationStatus.AUTO_CORRECTED
                            nutrient.rule_applied = f"fix_energy_scale_{int(factor)}x"
                            nutrient.confidence = 0.9
                            return nutrient

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

        # Barreira 3: Unidades Impossíveis para Minerais/Macronutrientes
        if nutrient.original_unit in ["kcal/kg", "ui/kg", "kcal/100g", "mj/kg"]:
             if not (target_is_kcalkg or target_is_uikg):
                nutrient.original_value = nutrient.value
                nutrient.value = None
                nutrient.status = ValidationStatus.IMPLAUSIBLE
                nutrient.rule_applied = f"invalid_unit_{nutrient.original_unit.replace('/', '')}"
                nutrient.confidence = 0.0
                return nutrient

        # Fluxo de Conversão por Unidade Explícita
        if nutrient.original_unit:
            converted_value, rule_name = self._resolve_by_unit(
                nutrient.value, 
                nutrient.original_unit, 
                rule
            )

            if converted_value is not None:
                if self.validator.is_valid(converted_value, rule):
                    nutrient.original_value = nutrient.value
                    nutrient.value = round(float(converted_value), 5)
                    nutrient.status = ValidationStatus.NORMALIZED
                    nutrient.rule_applied = f"unit_direct_{rule_name}"
                    nutrient.confidence = 1.0
                    return nutrient
                
                # v1.5.0: Se a unidade explícita resulta em valor inválido,
                # tentamos heurísticas de escala APENAS se o valor original for plausível de erro 10x/100x.
                # Caso contrário, o dado é considerado incoerente.

        # Fallback 1: Valor sem unidade mas já válido
        if self.validator.is_valid(nutrient.value, rule):
            nutrient.status = ValidationStatus.NORMALIZED
            nutrient.rule_applied = "already_normalized"
            nutrient.confidence = get_confidence("already_normalized")
            return nutrient

        # Fallback 2: Busca por heurísticas de escala (decimal shift, overscale)
        # v1.5.0: Heurísticas agora são aplicadas com critério de unicidade e limites biológicos estritos.
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
            nutrient.rule_applied = "ambiguous_heuristics"
            nutrient.confidence = get_confidence("ambiguous")
            return nutrient

        # Se nenhuma regra se aplicar, anula por implausibilidade
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
        """
        Interface simplificada para resolver um valor bruto.
        """
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
            # Flexibiliza limites biológicos para petiscos e suplementos
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
        """
        Realiza conversões baseadas em unidades de medida conhecidas.
        """
        target_is_mgkg = rule.field.endswith("_mgkg")
        target_is_kcalkg = rule.field.endswith("_kcalkg")
        target_is_uikg = rule.field.endswith("_uikg")

        # v1.5.0: Normalização de UI (Vitamina A, D, E)
        if target_is_uikg:
            if unit in ["ui/kg", "ui", "u.i.", "u.i"]:
                return value, "already_uikg"
            return None, "invalid_unit_for_uikg"

        if target_is_kcalkg:
            if unit == "kcal/kg":
                return value, "already_kcalkg"
            elif unit == "kcal/100g":
                return round(value * 10.0, 2), "kcal100g_to_kcalkg"
            elif unit == "mj/kg":
                return round(value * 239.006, 2), "mjkg_to_kcalkg"
            elif unit == "kcal/sache":
                return round((value / 85.0) * 1000.0, 2), "kcalsache_to_kcalkg"
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
            
        if unit == "mcg":
            # mcg -> mg/kg (dividir por 1000)
            if target_is_mgkg:
                return value * 0.001, "mcg_to_mgkg"
            # mcg -> g/kg (dividir por 1.000.000)
            return value * 0.000001, "mcg_to_gkg"

        if unit == "ppm":
            # ppm = mg/kg
            if target_is_mgkg:
                return value, "ppm_to_mgkg"
            return value / 1000.0, "ppm_to_gkg"

        return None, None

    def _build_candidates(
        self,
        nutrient: NormalizedNutrient,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:
        """
        Gera candidatos de valores normalizados através de heurísticas de escala.
        """
        value = nutrient.value
        candidates: list[tuple[float, str]] = []

        # v1.5.0: Heurísticas agora só são geradas se o valor estiver fora do limite biológico.
        # Se o valor já é válido, não tentamos "melhorá-lo" para evitar falsos positivos.
        if self.validator.is_valid(value, rule):
            return []

        # Divisão por potências de 10 (Erros de escala/deslocamento de vírgula)
        if value > rule.target_max:
            for factor in [10.0, 100.0, 1000.0]:
                test_val = value / factor
                if self.validator.is_valid(test_val, rule):
                    candidates.append((test_val, f"fix_{int(factor)}x_scale_down"))

        # Multiplicação por potências de 10 (Erros de escala/deslocamento de vírgula)
        if value < rule.target_min:
            for factor in [10.0, 100.0, 1000.0]:
                test_val = value * factor
                if self.validator.is_valid(test_val, rule):
                    candidates.append((test_val, f"fix_{int(factor)}x_scale_up"))

        # Heurísticas específicas da regra (overscale, percent, gkg_to_mgkg)
        if rule.overscale_factor:
            test_val = value / rule.overscale_factor
            if self.validator.is_valid(test_val, rule):
                candidates.append((test_val, "rule_overscale"))

        if rule.percent_factor:
            test_val = value * rule.percent_factor
            if self.validator.is_valid(test_val, rule):
                candidates.append((test_val, "rule_percent_conv"))

        if rule.gkg_to_mgkg:
            test_val = value * GKG_TO_MGKG_FACTOR
            if self.validator.is_valid(test_val, rule):
                candidates.append((test_val, "rule_gkg_to_mgkg"))

        return candidates


NormalizationResolver = Resolver
