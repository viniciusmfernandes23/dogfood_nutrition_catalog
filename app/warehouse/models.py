from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


# ==========================================================
# Base
# ==========================================================


@dataclass(slots=True)
class WarehouseModel:

    def to_dict(self) -> dict:

        return asdict(self)


# ==========================================================
# Dimensão Produto
# ==========================================================


@dataclass(slots=True)
class ProductDimension(WarehouseModel):

    product_id: int | None

    sku: str | None

    brand: str | None

    product_name: str | None

    product_url: str | None

    product_category: str | None

    product_tier: str | None

    life_stage: str | None

    breed_size: str | None

    protein_source: str | None

    clinical_category: str | None

    has_guarantee_levels: bool

    created_at: datetime

    updated_at: datetime


# ==========================================================
# Fato Nutrientes
# ==========================================================


@dataclass(slots=True)
class NutrientFact(WarehouseModel):

    product_id: int | None

    nutrient_name: str

    nutrient_value: float

    collected_at: datetime


# ==========================================================
# Fato Preços
# ==========================================================


@dataclass(slots=True)
class PriceSnapshotFact(WarehouseModel):

    product_id: int | None

    price: float | None

    available: bool | None

    collected_at: datetime