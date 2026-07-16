from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ProductCollection:

    product_id: int

    product_name: str

    brand: str | None

    url: str | None

    category_id: int | None
    marketplace: str = "Cobasi"
    ean: str | None = None
    api_payload: dict[str, Any] | None = None