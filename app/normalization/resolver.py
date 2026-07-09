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
        # Log de Auditoria para depuração do usuário
        if nutrient.name == "sodium_mgkg" and nutrient.value is not None and (nutrient.value > 100000 or nutrient.value < 1):
             print(f"[AUDIT] Resolvendo {nutrient.name}: valor_entrada={nutrient.value}, unidade={nutrient.original_unit}")

        if nutrient.value is None:
            nutrient.status = ValidationStatus.MISSING
            nutrient.confidence = 0.0
            return nutrient

        # Proteção e Auto-Correção de valores astronômicos
        # Se o valor for > 100.000, provavelmente sofreu múltiplas multiplicações indevidas
        if nutrient.value > 100_000:
            temp_value = nutrient.value
            # Tenta divisões sucessivas por 10.000 (%), 1.000 (g/kg) e 10 (overscale)
            for factor in [10000.0, 1000.0, 10.0]:
                test_val = nutrient.value
                for _ in range(4): # Tenta até 4 níveis de escala acumulada
                    test_val /= factor
                    if self.validator.is_valid(test_val, rule):
                        nutrient.original_value = nutrient.value
                        nutrient.value = round(float(test_val), 2)
                        nutrient.status = ValidationStatus.AUTO_CORRECTED
                        nutrient.rule_applied = f"fix_accumulated_scale_{int(factor)}"
                        nutrient.confidence = 1.0
                        print(f"[AUDIT] Valor corrigido recursivamente ({factor}): {nutrient.value}")
                        return nutrient
            
            # Se não conseguiu corrigir, anula o valor para não poluir o dataset
            print(f"[AUDIT] VALOR ANULADO (IMPOSSÍVEL CORRIGIR): {nutrient.value}")
            nutrient.original_value = nutrient.value
            nutrient.value = None
            nutrient.status = ValidationStatus.IMPLAUSIBLE
            nutrient.rule_applied = "nullified_extreme_value"
            nutrient.confidence = 0.0
            return nutrient

        if rule is None:
            return nutrient

        # 1. Se o valor já está no range e parece plausível, aceitamos IMEDIATAMENTE.
        # Isso evita re-normalização de valores que já estão corretos (ex: 1700 mg/kg ou 3500 kcal/kg).
        if self.validator.is_valid(nutrient.value, rule):
            nutrient.status = ValidationStatus.NORMALIZED
            nutrient.rule_applied = "already_normalized"
            nutrient.confidence = get_confidence("already_normalized")
            return nutrient

        # 2. Prioridade: Unidade original detectada pelo parser
        if nutrient.original_unit:
            converted_value, rule_name = self._resolve_by_unit(
                nutrient.value, 
                nutrient.original_unit, 
                rule
            )
            if converted_value is not None and self.validator.is_valid(converted_value, rule):
                nutrient.original_value = nutrient.value
                nutrient.value = round(float(converted_value), 2)
                nutrient.status = ValidationStatus.AUTO_CORRECTED
                nutrient.rule_applied = f"unit_direct_{rule_name}"
                nutrient.confidence = 1.0  # Confiança máxima com unidade explícita
                return nutrient

        # 3. Fallback: Busca exaustiva por candidatos válidos
        candidates = self._build_candidates(nutrient.value, rule)
        candidates = self.validator.validate_candidates(candidates, rule)

        if self.validator.has_single_candidate(candidates):
            value, applied_rule = candidates[0]
            nutrient.original_value = nutrient.value
            nutrient.value = round(float(value), 2)
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
        
        target_unit = "g/kg"
        if rule.field.endswith("_mgkg"):
            target_unit = "mg/kg"
        elif rule.field.endswith("_kcalkg"):
            target_unit = "kcal/kg"
            
        nutrient = NormalizedNutrient(
            name=rule.field,
            value=value,
            unit=target_unit,
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
            
        if unit == "kcal/kg":
            if rule.field.endswith("_kcalkg"):
                return value, "already_kcalkg"
            
        return None, None

    def _build_candidates(
        self,
        value: float,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:
        """
        Gera candidatos baseados apenas em fatores de escala e conversão seguros.
        Removidas heurísticas de multiplicação agressivas para evitar instabilidade biológica.
        """
        candidates: list[tuple[float, str]] = []

        # 1. Overscale (Divisão por 10) - Comum em rótulos que preservam decimais
        if rule.overscale_factor:
            candidates.append((value / rule.overscale_factor, "overscale"))

        # 2. Conversão de Porcentagem (Multiplicação por 10 ou 10.000)
        if rule.percent_factor:
            candidates.append((value * rule.percent_factor, "percent_conversion"))

        # 3. Conversão g/kg para mg/kg (Multiplicação por 1000)
        if rule.gkg_to_mgkg:
            candidates.append((value * GKG_TO_MGKG_FACTOR, "gkg_to_mgkg"))

        # 4. Deslocamento Decimal descendente (Heurística de segurança para valores altos)
        if value > rule.target_max:
            candidates.append((value / 10.0, "fix_10x_scale"))
            candidates.append((value / 100.0, "fix_100x_scale"))

        return candidates


NormalizationResolver = Resolver
