from __future__ import annotations

from enum import Enum


class NutritionStatus(str, Enum):
    """
    Categorias de qualidade dos dados nutricionais.
    """

    HAS_GUARANTEE = "Tem níveis de garantia"

    NO_GUARANTEE = "Não tem níveis de garantia"

    NORMALIZED = "Normalizado"

    AUTO_CORRECTED = "Corrigido automaticamente"

    MANUAL_REVIEW = "Requer revisão manual"

    AMBIGUOUS = "Ambíguo"

    IMPLAUSIBLE = "Implausível"

    MISSING = "Sem informação"

    @classmethod
    def values(cls) -> list[str]:
        return [status.value for status in cls]

    @classmethod
    def contains(cls, value: str | None) -> bool:
        if value is None:
            return False
        return value in cls.values()

    @classmethod
    def from_bool(cls, has_guarantee: bool) -> "NutritionStatus":
        return (
            cls.HAS_GUARANTEE
            if has_guarantee
            else cls.NO_GUARANTEE
        )