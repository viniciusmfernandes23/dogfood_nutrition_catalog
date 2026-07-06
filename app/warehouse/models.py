from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ProductDimension:
    product_id: int

    sku: str | None = None

    brand: str | None = None

    manufacturer: str | None = None

    product_name: str | None = None

    product_url: str | None = None

    image_url: str | None = None

    category: str | None = None

    product_category: str | None = None

    product_tier: str | None = None

    life_stage: str | None = None

    breed_size: str | None = None

    protein_source: str | None = None

    clinical_category: str | None = None

    package_size: float | None = None

    package_unit: str | None = None

    has_guarantee_levels: bool = False

    created_at: datetime | None = None

    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class NutrientFact:
    product_id: int

    nutrient: str

    value: float | None

    unit: str | None

    normalization_status: str | None = None

    rule_applied: str | None = None

    confidence: float | None = None

    snapshot_date: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PriceSnapshotFact:
    product_id: int

    snapshot_date: datetime

    price: float | None = None

    subscriber_price: float | None = None

    price_per_kg: float | None = None

    currency: str = "BRL"

    in_stock: bool = False

    has_price: bool = False

    has_price_per_kg: bool = False

    has_subscriber_price: bool = False

    seller: str | None = None

    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)