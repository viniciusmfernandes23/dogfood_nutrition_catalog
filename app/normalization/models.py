from dataclasses import dataclass


@dataclass(slots=True)
class NormalizationResult:

    value: float | None

    original_value: float | None

    field: str

    rule: str | None

    status: str