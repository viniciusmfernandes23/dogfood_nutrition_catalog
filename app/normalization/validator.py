from __future__ import annotations

from typing import Iterable

import pandas as pd

from app.normalization.models import NormalizationRule


class NormalizationValidator:
    """
    Responsável apenas por validar valores.

    Não realiza nenhuma alteração nos dados.
    """

    @staticmethod
    def is_null(value: float | None) -> bool:
        """
        Verifica se um valor é nulo.
        """
        return value is None or pd.isna(value)

    @classmethod
    def is_valid(
        cls,
        value: float | None,
        rule: NormalizationRule,
    ) -> bool:
        """
        Verifica se o valor já está
        dentro da faixa esperada.
        """

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
        """
        Alias para is_valid().
        Mantido para facilitar leitura
        no resolver.
        """

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
        """
        Verifica se um candidato de
        normalização é válido.
        """

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
    ) -> list[tuple[float, str]]:
        """
        Remove candidatos inválidos.
        """

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
        """
        Remove candidatos duplicados.

        Dois candidatos são considerados
        iguais se produzirem o mesmo valor.
        """

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
        """
        Pipeline completo de validação.

        1. Remove candidatos fora da faixa.

        2. Remove duplicados.

        3. Retorna somente candidatos válidos.
        """

        candidates = cls.filter_valid_candidates(
            candidates,
            rule,
        )

        candidates = cls.remove_duplicate_candidates(
            candidates,
        )

        return candidates