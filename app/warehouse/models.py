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
    """
    Representa um snapshot de preço para uma variação específica (SKU) de produto.

    Cada linha corresponde a uma combinação única de produto + SKU + data de coleta,
    permitindo rastrear o histórico de preços por embalagem/tamanho.

    Campos:
        product_id      : Identificador do produto pai (agrupa todas as variações).
        sku_id          : Identificador único do SKU/item (variação específica, ex: 915700).
        sku_name        : Descrição da variação (ex: "15kg", "Frango e Carne 15kg").
        package_weight_kg: Peso da embalagem em kg, extraído do nome do SKU quando disponível.
        price           : Preço de venda atual da variação.
        list_price      : Preço de tabela (sem desconto), quando disponível.
        subscriber_price: Preço para assinantes/compra programada, quando disponível.
        price_per_kg    : Preço por kg calculado (price / package_weight_kg).
        available       : Indica se a variação está disponível em estoque.
        collected_at    : Data/hora da coleta (truncada ao dia para snapshots diários).
    """

    product_id: int | None
    marketplace: str | None
    ean: str | None
    sku_id: str | None

    sku_name: str | None

    package_weight_kg: float | None

    price: float | None

    list_price: float | None

    subscriber_price: float | None

    price_per_kg: float | None

    available: bool | None

    collected_at: datetime
