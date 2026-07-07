from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ValidationStatus(str, Enum):
    NORMALIZED = "normalized"
    AUTO_CORRECTED = "auto_corrected"
    REVIEW = "review"
    AMBIGUOUS = "ambiguous"
    IMPLAUSIBLE = "implausible"
    MISSING = "missing"


@dataclass(slots=True, frozen=True)
class NormalizationRule:
    """
    Regra utilizada durante a normalização.
    """

    field: str

    target_min: float

    target_max: float

    overscale_factor: float | None = None

    percent_factor: float | None = None

    decimal_shift_factor: float | None = None

    gkg_to_mgkg: bool = False


@dataclass(slots=True)
class NormalizedNutrient:
    """
    Nutriente normalizado utilizado pelo Validator,
    Resolver e testes.
    """

    name: str

    value: float | None

    unit: str

    original_value: float | None = None

    original_unit: str | None = None

    status: ValidationStatus = ValidationStatus.NORMALIZED

    confidence: float = 1.0

    rule_applied: str | None = None


@dataclass(slots=True)
class NormalizationResult:
    """
    Resultado da normalização de um único valor.
    """

    field: str

    original_value: float | None

    normalized_value: float | None

    rule_applied: str | None

    status: ValidationStatus

    confidence: float

    changed: bool


@dataclass(slots=True)
class NormalizationLog:
    """
    Registro de alteração aplicada.
    """

    product_id: int

    field: str

    original_value: float | None

    normalized_value: float | None

    rule_applied: str | None

    status: ValidationStatus


@dataclass(slots=True)
class DatasetNormalizationReport:
    """
    Estatísticas consolidadas da normalização.
    """

    processed_records: int = 0

    changed_records: int = 0

    unchanged_records: int = 0

    ambiguous_records: int = 0

    implausible_records: int = 0

    manual_review_records: int = 0

    auto_corrected_records: int = 0

    logs: list[NormalizationLog] = field(
        default_factory=list,
    )

    def add_log(
        self,
        log: NormalizationLog,
    ) -> None:

        self.logs.append(log)

    @property
    def success_rate(
        self,
    ) -> float:

        if self.processed_records == 0:
            return 0.0

        return round(
            (
                self.auto_corrected_records
                / self.processed_records
            )
            * 100,
            2,
        )