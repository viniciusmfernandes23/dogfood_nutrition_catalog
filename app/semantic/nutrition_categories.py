from enum import Enum


class NutritionStatus(str, Enum):

    HAS_GUARANTEE = "Tem níveis de garantia"

    NO_GUARANTEE = "Não tem níveis de garantia"

    NORMALIZED = "Normalizado"

    AUTO_CORRECTED = "Corrigido automaticamente"

    MANUAL_REVIEW = "Requer revisão manual"

    AMBIGUOUS = "Ambíguo"

    IMPLAUSIBLE = "Implausível"