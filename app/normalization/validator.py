from __future__ import annotations

from typing import Iterable

import pandas as pd

from app.normalization.models import (
    NormalizationRule,
    NormalizedNutrient,
    NormalizationResult,
    ValidationStatus,
)


class Validator:
    """
    Responsável exclusivamente pela validação
    de valores normalizados.
    """

    @staticmethod
    def is_null(
        value: float | None,
    ) -> bool:

        return value is None or pd.isna(value)

    @classmethod
    def is_valid(
        cls,
        value: float | None,
        rule: NormalizationRule,
    ) -> bool:

        if cls.is_null(value):
            return False

        return (
            rule.target_min
            <= value
            <= rule.target_max
        )

    @classmethod
    def is_below_range(
        cls,
        value: float | None,
        rule: NormalizationRule,
    ) -> bool:

        if cls.is_null(value):
            return False

        return value < rule.target_min

    @classmethod
    def is_above_range(
        cls,
        value: float | None,
        rule: NormalizationRule,
    ) -> bool:

        if cls.is_null(value):
            return False

        return value > rule.target_max

    @classmethod
    def is_plausible(
        cls,
        value: float | None,
        rule: NormalizationRule,
    ) -> bool:

        return cls.is_valid(
            value,
            rule,
        )

    @classmethod
    def candidate_is_valid(
        cls,
        candidate: float | None,
        rule: NormalizationRule,
    ) -> bool:

        return cls.is_valid(
            candidate,
            rule,
        )

    @classmethod
    def filter_valid_candidates(
        cls,
        candidates: Iterable[
            tuple[float, str]
        ],
        rule: NormalizationRule,
    ) -> list[
        tuple[float, str]
    ]:

        valid = []

        for value, reason in candidates:

            if cls.candidate_is_valid(
                value,
                rule,
            ):

                valid.append(
                    (
                        value,
                        reason,
                    )
                )

        return valid

    @staticmethod
    def remove_duplicate_candidates(
        candidates: list[
            tuple[float, str]
        ],
    ) -> list[
        tuple[float, str]
    ]:

        unique: dict[
            float,
            str,
        ] = {}

        for value, reason in candidates:

            unique.setdefault(
                round(value, 6),
                reason,
            )

        return [

            (value, reason)

            for value, reason

            in unique.items()

        ]

    @staticmethod
    def has_single_candidate(
        candidates: list[
            tuple[float, str]
        ],
    ) -> bool:

        return len(candidates) == 1

    @staticmethod
    def has_multiple_candidates(
        candidates: list[
            tuple[float, str]
        ],
    ) -> bool:

        return len(candidates) > 1

    @staticmethod
    def has_no_candidates(
        candidates: list[
            tuple[float, str]
        ],
    ) -> bool:

        return len(candidates) == 0

    @classmethod
    def validate_candidates(
        cls,
        candidates: list[
            tuple[float, str]
        ],
        rule: NormalizationRule,
    ) -> list[
        tuple[float, str]
    ]:

        candidates = cls.filter_valid_candidates(
            candidates,
            rule,
        )

        candidates = cls.remove_duplicate_candidates(
            candidates,
        )

        return candidates

    @classmethod
    def validate(
        cls,
        nutrient: NormalizedNutrient,
        rule: NormalizationRule | None = None,
    ) -> NormalizationResult:

        if cls.is_null(
            nutrient.value,
        ):

            return NormalizationResult(

                field=nutrient.name,

                original_value=nutrient.original_value,

                normalized_value=nutrient.value,

                rule_applied=nutrient.rule_applied,

                status=ValidationStatus.MISSING,

                confidence=0.0,

                changed=False,

            )

        if rule is None:

            return NormalizationResult(

                field=nutrient.name,

                original_value=nutrient.original_value,

                normalized_value=nutrient.value,

                rule_applied=nutrient.rule_applied,

                status=ValidationStatus.NORMALIZED,

                confidence=nutrient.confidence,

                changed=(
                    nutrient.original_value
                    != nutrient.value
                ),

            )

        if cls.is_valid(
            nutrient.value,
            rule,
        ):

            status = (
                nutrient.status
                if nutrient.status
                != ValidationStatus.IMPLAUSIBLE
                else ValidationStatus.NORMALIZED
            )

        else:

            status = ValidationStatus.IMPLAUSIBLE

        return NormalizationResult(

            field=nutrient.name,

            original_value=nutrient.original_value,

            normalized_value=nutrient.value,

            rule_applied=nutrient.rule_applied,

            status=status,

            confidence=nutrient.confidence,

            changed=(
                nutrient.original_value
                != nutrient.value
            ),

        )


NormalizationValidator = Validator