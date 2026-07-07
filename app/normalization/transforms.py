from __future__ import annotations

from abc import ABC, abstractmethod

from app.normalization.models import NormalizationRule
from app.normalization.rules import GKG_TO_MGKG_FACTOR


class BaseTransform(ABC):
    """
    Classe base para todas as transformações de normalização.
    """

    name: str

    @abstractmethod
    def apply(
        self,
        value: float,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:
        """
        Retorna uma lista de candidatos para normalização.
        """
        raise NotImplementedError


class OverscaleTransform(BaseTransform):

    name = "overscale"

    def apply(
        self,
        value: float,
        rule: NormalizationRule,
    ) -> list[tuple[float, str]]:

        factor = rule.overscale_factor

        if factor is None:
            return []

        return [
            (
                value / factor,
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

        factor = rule.decimal_shift_factor

        if factor is None:
            return []

        return [
            (
                value * factor,
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

        factor = rule.percent_factor

        if factor is None:
            return []

        return [
            (
                value * factor,
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


TRANSFORMS: tuple[BaseTransform, ...] = (
    OverscaleTransform(),
    DecimalShiftTransform(),
    PercentTransform(),
    GkgToMgkgTransform(),
)