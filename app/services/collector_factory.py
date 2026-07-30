"""
CollectorFactory — Fábrica de coletores de marketplace.

Cada marketplace é representado por uma classe que implementa a interface
CollectorProtocol. A fábrica registra e instancia coletores por nome,
eliminando os blocos `if marketplace == "X"` do pipeline principal.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.collectors.cobasi_api import CobasiAPICollector
from app.collectors.models import ProductCollection
from app.collectors.petlove_crawler import PetloveCrawlerCollector
from app.collectors.petz_collector import PetzCollector as PetzSourceCollector
from app.core.config_loader import ConfigLoader
from app.core.logging import logger


class BaseCollector(ABC):
    """Interface comum para todos os coletores de marketplace."""

    @property
    @abstractmethod
    def marketplace(self) -> str:
        ...

    @abstractmethod
    def fetch_all(self, *args: Any, **kwargs: Any) -> list[ProductCollection]:
        ...

    def extract_sku_variations(self, api_payload: dict) -> list[dict]:
        """
        Extrai variações de SKU a partir do payload bruto da API.
        Deve ser sobrescrito por coletores que possuem múltiplas variações
        (ex: Cobasi, Petlove). Por padrão, retorna uma variação genérica.
        """
        return [
            {
                "sku_id": None,
                "sku_name": None,
                "ean": None,
                "package_weight_kg": None,
                "price": None,
                "list_price": None,
                "subscriber_price": None,
                "price_per_kg": None,
                "available": False,
                "marketplace": self.marketplace,
            }
        ]


# ----------------------------------------------------------
# Implementações específicas por marketplace
# ----------------------------------------------------------


class CobasiCollector(BaseCollector):
    """Coletor da Cobasi via API VTEX."""

    @property
    def marketplace(self) -> str:
        return "Cobasi"

    def fetch_all(self, *args: Any, **kwargs: Any) -> list[ProductCollection]:
        collector = CobasiAPICollector()
        return collector.fetch_all()

    def extract_sku_variations(self, api_payload: dict) -> list[dict]:
        """Extrai SKUs do payload VTEX da Cobasi."""
        from app.services._sku_parsers import cobasi_parse_weight
        variations = []
        items = api_payload.get("items", [])
        for item in items:
            sku_id = item.get("itemId")
            sku_name = item.get("name")
            package_weight_kg = cobasi_parse_weight(sku_name)
            ean = item.get("ean")

            price = None
            list_price = None
            available = False

            sellers = item.get("sellers", [])
            if sellers:
                comm = sellers[0].get("commertialOffer", {})
                price = comm.get("Price")
                list_price = comm.get("ListPrice")
                available = comm.get("AvailableQuantity", 0) > 0

            price_per_kg = None
            if price is not None and package_weight_kg and package_weight_kg > 0:
                price_per_kg = round(price / package_weight_kg, 4)

            variations.append({
                "sku_id": sku_id,
                "sku_name": sku_name,
                "ean": ean,
                "package_weight_kg": package_weight_kg,
                "price": price,
                "list_price": list_price,
                "subscriber_price": round(price * 0.9, 2) if price else None,
                "price_per_kg": price_per_kg,
                "available": available,
                "marketplace": self.marketplace,
            })
        return variations


class PetloveCollector(BaseCollector):
    """Coletor da Petlove via scraping de __NEXT_DATA__."""

    @property
    def marketplace(self) -> str:
        return "Petlove"

    def fetch_all(self, *args: Any, **kwargs: Any) -> list[ProductCollection]:
        config = ConfigLoader.load()
        queries = kwargs.get("queries") or config.collectors.petlove.default_queries
        collector = PetloveCrawlerCollector()
        return collector.fetch_all(queries)

    def extract_sku_variations(self, api_payload: dict) -> list[dict]:
        """Extrai SKUs do payload da Petlove."""
        from app.services._sku_parsers import cobasi_parse_weight
        variations = []
        items = api_payload.get("variants", [])
        for item in items:
            sku_name = item.get("name")
            package_weight_kg = cobasi_parse_weight(sku_name)
            price = item.get("price")
            price_per_kg = None
            if price is not None and package_weight_kg and package_weight_kg > 0:
                price_per_kg = round(price / package_weight_kg, 4)
            variations.append({
                "sku_id": str(item.get("id")),
                "sku_name": sku_name,
                "ean": item.get("ean"),
                "package_weight_kg": package_weight_kg,
                "price": price,
                "list_price": item.get("listPrice"),
                "subscriber_price": item.get("subscriptionPrice"),
                "price_per_kg": price_per_kg,
                "available": item.get("stock", 0) > 0,
                "marketplace": self.marketplace,
            })
        return variations


class PetzCollector(BaseCollector):
    """Coletor da Petz integrado ao fluxo principal."""

    @property
    def marketplace(self) -> str:
        return "Petz"

    def fetch_all(self, *args: Any, **kwargs: Any) -> list[ProductCollection]:
        config = ConfigLoader.load()
        queries = kwargs.get("queries") or config.collectors.petz.default_queries
        categories = kwargs.get("categories") or []
        collector = PetzSourceCollector()
        return collector.fetch_all(queries=queries, categories=categories)


# ----------------------------------------------------------
# Fábrica
# ----------------------------------------------------------

_REGISTRY: dict[str, type[BaseCollector]] = {}


def _register(name: str) -> type[BaseCollector]:
    """Decorator para registrar um coletor na fábrica."""
    def decorator(cls: type[BaseCollector]) -> type[BaseCollector]:
        _REGISTRY[name] = cls
        return cls
    return decorator


# Registra os coletores built-in
_register("Cobasi")(CobasiCollector)
_register("Petlove")(PetloveCollector)
_register("Petz")(PetzCollector)


class CollectorFactory:
    """
    Fábrica de coletores de marketplace.

    Uso:
        factory = CollectorFactory()
        collector = factory.create("Cobasi")
        products = collector.fetch_all()
    """

    def create(self, marketplace: str) -> BaseCollector:
        """Instancia o coletor registrado para o marketplace informado."""
        cls = _REGISTRY.get(marketplace)
        if cls is None:
            raise ValueError(
                f"Marketplace '{marketplace}' não registrado. "
                f"Marketplaces disponíveis: {list(_REGISTRY.keys())}"
            )
        return cls()

    @classmethod
    def available_marketplaces(cls) -> list[str]:
        """Retorna a lista de marketplaces registrados."""
        return list(_REGISTRY.keys())
