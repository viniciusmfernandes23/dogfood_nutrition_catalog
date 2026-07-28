"""
Modelos de dados centralizados para o pipeline de nutrição canina.

Estes modelos substituem o tráfego de dicionários ``dict`` entre serviços,
fornecendo:
  - Autocomplete em IDEs
  - Validação de tipos
  - Documentação implícita
  - Serialização JSON/dataclass nativa
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class SKUVariation:
    """Representa uma variação de SKU (embalagem/tamanho) de um produto."""

    sku_id: str | None = None
    sku_name: str | None = None
    ean: str | None = None
    package_weight_kg: float | None = None
    price: float | None = None
    list_price: float | None = None
    subscriber_price: float | None = None
    price_per_kg: float | None = None
    available: bool = False
    marketplace: str = "Cobasi"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TechnicalSpecification:
    """Representa as especificações técnicas (Ficha Técnica) de um produto."""

    breed_size: str | None = None
    product_type: str | None = None
    package_weight: str | None = None
    life_stage: str | None = None
    contains_coloring: str | None = None
    target_breeds: str | None = None
    indication: str | None = None
    product_line: str | None = None
    is_transgenic: str | None = None
    product_category: str | None = None
    product_dept: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            k: v for k, v in asdict(self).items()
            if v is not None
        }


@dataclass(slots=True)
class NutritionMatch:
    """Representa um nutriente extraído com sua prioridade de matching."""

    nutrient_key: str  # ex: "protein_gkg"
    value: float
    unit: str | None = None
    priority: int = 1  # 1 = padrão, 2 = com "mín/max"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EnrichedProduct:
    """
    Representa um produto completo com todas as informações enriquecidas.

    Substitui o dicionário ``product_list`` que era trafegado
    entre as etapas do pipeline.
    """

    product_id: int
    marketplace: str = "Cobasi"
    ean: str | None = None
    product_name: str | None = None
    brand: str | None = None
    url: str | None = None
    category_id: int | None = None
    sku_variations: list[SKUVariation] = field(default_factory=list)
    price: float | None = None
    available: bool = False
    image_url: str | None = None
    specifications: TechnicalSpecification = field(default_factory=TechnicalSpecification)
    # Nutrientes extraídos (modo full)
    nutrients: dict[str, NutritionMatch] = field(default_factory=dict)
    raw_guarantee: str | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dataframe_row(self) -> dict[str, Any]:
        """
        Converte para o formato de dicionário compatível com o DataFrame
        que o PipelineOrchestrator espera.
        """
        row: dict[str, Any] = {
            "product_id": self.product_id,
            "marketplace": self.marketplace,
            "ean": self.ean,
            "product_name": self.product_name,
            "brand": self.brand,
            "url": self.url,
            "category_id": self.category_id,
            "price": self.price,
            "available": self.available,
            "image_url": self.image_url,
            "raw_guarantee": self.raw_guarantee,
        }

        # Variações de SKU como lista de dicts
        row["sku_variations"] = [v.to_dict() for v in self.sku_variations]

        # Especificações flat (compatível com o formato anterior)
        row.update(self.specifications.to_dict())

        # Nutrientes (colunas canônicas)
        for match in self.nutrients.values():
            row[match.nutrient_key] = match.value
            row[f"{match.nutrient_key}_unit"] = match.unit

        return row
