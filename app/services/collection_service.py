"""
CollectionService — Serviço de coleta de produtos.

Centraliza a coleta de produtos de múltiplos marketplaces através do
CollectorFactory, orquestrando a extração e consolidando os resultados
em uma lista unificada de ProductCollection.
"""

from __future__ import annotations

from typing import Sequence

from app.collectors.models import ProductCollection
from app.core.logging import logger
from app.services.collector_factory import BaseCollector, CollectorFactory


class CollectionService:
    """
    Orquestra a coleta de produtos de um ou mais marketplaces.

    Uso:
        service = CollectionService(["Cobasi", "Petlove"])
        products = service.collect()
    """

    def __init__(
        self,
        marketplaces: Sequence[str] | None = None,
        collector_kwargs: dict[str, dict] | None = None,
    ) -> None:
        self._marketplaces = list(marketplaces or ["Cobasi"])
        self._kwargs = collector_kwargs or {}
        self._factory = CollectorFactory()

    @property
    def marketplaces(self) -> list[str]:
        return list(self._marketplaces)

    def collect(self) -> list[ProductCollection]:
        """
        Coleta produtos de todos os marketplaces configurados.

        Retorna uma lista de ProductCollection sem duplicatas.
        """
        all_products: list[ProductCollection] = []

        for marketplace in self._marketplaces:
            logger.info("Coletando catálogo de %s...", marketplace)
            try:
                collector = self._factory.create(marketplace)
                kwargs = self._kwargs.get(marketplace, {})
                products = collector.fetch_all(**kwargs)

                if products:
                    logger.info(
                        "  Sucesso: %d produtos coletados de %s.",
                        len(products),
                        marketplace,
                    )
                    all_products.extend(products)
                else:
                    logger.warning(
                        "  Nenhum produto retornado de %s.",
                        marketplace,
                    )

            except Exception as exc:
                logger.error(
                    "  ERRO CRÍTICO ao coletar %s: %s",
                    marketplace,
                    exc,
                )
                raise

        # Deduplicação por product_id
        unique: dict[int, ProductCollection] = {}
        for p in all_products:
            unique[p.product_id] = p

        logger.info(
            "Total de produtos únicos coletados: %d",
            len(unique),
        )
        return list(unique.values())

    def get_collector(self, marketplace: str) -> BaseCollector:
        """Retorna o coletor instanciado para um marketplace específico."""
        return self._factory.create(marketplace)
