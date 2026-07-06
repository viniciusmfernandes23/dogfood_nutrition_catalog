from __future__ import annotations

from abc import ABC, abstractmethod

from app.normalization.models import NormalizationRule
from app.normalization.rules import GKG_TO_MGKG_FACTOR


class BaseTransform(ABC):
    """
    Classe base para todas as transformações.
    """

    name: str

    @abstractmethod
    def apply(
        self,
        value: float,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:
        ...


class OverscaleTransform(BaseTransform):

    name = "overscale"

    def apply(
        self,
        value: float,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:

        if rule.overscale_factor is None:
            return []

        return [
            (
                value / rule.overscale_factor,
                self.name,
            )
        ]


class DecimalShiftTransform(BaseTransform):

    name = "decimal_shift"

    def apply(
        self,
        value: float,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:

        if rule.decimal_shift_factor is None:
            return []

        return [
            (
                value * rule.decimal_shift_factor,
                self.name,
            )
        ]


class PercentTransform(BaseTransform):

    name = "percent_conversion"

    def apply(
        self,
        value: float,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:

        if rule.percent_factor is None:
            return []

        return [
            (
                value * rule.percent_factor,
                self.name,
            )
        ]


class GkgToMgkgTransform(BaseTransform):

    name = "gkg_to_mgkg"

    def apply(
        self,
        value: float,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:

        if not rule.gkg_to_mgkg:
            return []

        return [
            (
                value * GKG_TO_MGKG_FACTOR,
                self.name,
            )
        ]


TRANSFORMS = (

    OverscaleTransform(),

    DecimalShiftTransform(),

    PercentTransform(),

    GkgToMgkgTransform(),

)