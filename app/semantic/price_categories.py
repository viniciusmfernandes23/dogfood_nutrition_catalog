from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class PriceCategory:
    """
    Categorias semânticas relacionadas ao preço do produto.
    """

    availability: str

    price_status: str

    price_per_kg_status: str

    subscriber_status: str

    @property
    def in_stock(self) -> bool:
        return self.availability == "in_stock"

    @property
    def has_price(self) -> bool:
        return self.price_status == "tem preço"

    @property
    def has_price_per_kg(self) -> bool:
        return self.price_per_kg_status == "tem preço por kg"

    @property
    def has_subscriber_price(self) -> bool:
        return (
            self.subscriber_status
            == "preço assinante disponível"
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "availability": self.availability,
            "price_status": self.price_status,
            "price_per_kg_status": self.price_per_kg_status,
            "subscriber_status": self.subscriber_status,
        }