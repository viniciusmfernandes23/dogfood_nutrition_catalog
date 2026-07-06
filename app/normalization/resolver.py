from __future__ import annotations

from app.normalization.models import (
    NormalizationResult,
    NormalizationRule,
)
from app.normalization.rules import (
    GKG_TO_MGKG_FACTOR,
    RULE_CONFIDENCE,
    STATUS_AMBIGUOUS,
    STATUS_AUTO_CORRECTED,
    STATUS_IMPLAUSIBLE,
    STATUS_MANUAL_REVIEW,
    STATUS_NORMALIZED,
)
from app.normalization.validator import (
    NormalizationValidator,
)


class NormalizationResolver:
    """
    Resolve automaticamente problemas de escala
    utilizando as regras definidas para cada nutriente.
    """

    def __init__(self) -> None:

        self.validator = NormalizationValidator()

    def resolve(
        self,
        value: float | None,
        rule: NormalizationRule,
    ) -> NormalizationResult:

        if self.validator.is_null(value):

            return self._null_result(rule)

        if self.validator.is_valid(value, rule):

            return NormalizationResult(
                field=rule.field,
                original_value=value,
                normalized_value=value,
                rule_applied="already_normalized",
                status=STATUS_NORMALIZED,
                confidence=RULE_CONFIDENCE["already_normalized"],
                changed=False,
            )

        candidates = self._build_candidates(
            value=value,
            rule=rule,
        )

        candidates = self.validator.validate_candidates(
            candidates,
            rule,
        )

        if self.validator.has_single_candidate(candidates):

            normalized_value, applied_rule = candidates[0]

            return NormalizationResult(
                field=rule.field,
                original_value=value,
                normalized_value=normalized_value,
                rule_applied=applied_rule,
                status=STATUS_AUTO_CORRECTED,
                confidence=RULE_CONFIDENCE[applied_rule],
                changed=True,
            )

        if self.validator.has_multiple_candidates(candidates):

            return NormalizationResult(
                field=rule.field,
                original_value=value,
                normalized_value=value,
                rule_applied="ambiguous",
                status=STATUS_AMBIGUOUS,
                confidence=RULE_CONFIDENCE["ambiguous"],
                changed=False,
            )

        return NormalizationResult(
            field=rule.field,
            original_value=value,
            normalized_value=value,
            rule_applied="implausible",
            status=STATUS_IMPLAUSIBLE,
            confidence=RULE_CONFIDENCE["implausible"],
            changed=False,
        )

    def _build_candidates(
        self,
        value: float,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:

        candidates: list[tuple[float, str]] = []

        # --------------------------------------------------
        # Overscale
        # --------------------------------------------------

        if rule.overscale_factor:

            candidates.append(
                (
                    value / rule.overscale_factor,
                    "overscale",
                )
            )

        # --------------------------------------------------
        # Decimal Shift
        # --------------------------------------------------

        if rule.decimal_shift_factor:

            candidates.append(
                (
                    value * rule.decimal_shift_factor,
                    "decimal_shift",
                )
            )

        # --------------------------------------------------
        # Percent
        # --------------------------------------------------

        if rule.percent_factor:

            candidates.append(
                (
                    value * rule.percent_factor,
                    "percent_conversion",
                )
            )

        # --------------------------------------------------
        # g/kg -> mg/kg
        # --------------------------------------------------

        if rule.gkg_to_mgkg:

            candidates.append(
                (
                    value * GKG_TO_MGKG_FACTOR,
                    "gkg_to_mgkg",
                )
            )

        return candidates

    @staticmethod
    def _null_result(
        rule: NormalizationRule,
    ) -> NormalizationResult:

        return NormalizationResult(
            field=rule.field,
            original_value=None,
            normalized_value=None,
            rule_applied=None,
            status=STATUS_MANUAL_REVIEW,
            confidence=0.0,
            changed=False,
        )