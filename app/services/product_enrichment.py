"""
ProductEnrichmentService — Serviço de enriquecimento de produto.

Responsável por extrair especificações (Ficha Técnica), imagem,
marca e campos VTEX do payload bruto da API, além de montar a
lista de variações de SKU via CollectorFactory.
"""

from __future__ import annotations

from typing import Any

from app.collectors.models import ProductCollection
from app.core.logging import logger
from app.services.collector_factory import CollectorFactory


# Mapeamento exaustivo VTEX: chave interna → aliases VTEX
VTX_SPEC_MAP: dict[str, list[str]] = {
    "breed_size": ["Porte", "Porte do Cão"],
    "product_type": ["Tipo da ração", "Tipo da Ração", "customLabel3 Classif Ração"],
    "package_weight": ["Peso da Ração", "Peso"],
    "life_stage": ["Idade", "Fase de Vida"],
    "contains_coloring": ["Corante"],
    "target_breeds": ["Raças de cachorro", "Raças de Cachorro", "Raça"],
    "indication": ["Indicação", "Indicações"],
    "product_line": ["Linha", "Linha do Produto"],
    "is_transgenic": ["Transgênico", "Transgenico"],
    "brand_spec": ["Marca"],
    "product_category": ["Seção", "customLabel2 Subcategoria", "customLabel1 Categoria"],
    "product_dept": ["Departamento", "customLabel0 Departamento"],
    "product_cat_vtex": ["Categoria"],
}


class ProductEnrichmentService:
    """
    Enriquece um ProductCollection extraindo especificações,
    imagem e variações de SKU do payload bruto da API.
    """

    def __init__(self) -> None:
        self._factory = CollectorFactory()

    def enrich(self, product: ProductCollection) -> dict[str, Any] | None:
        """
        Enriquece um produto e retorna o dicionário final pronto para
        o DataFrame do pipeline.

        Retorna None se o produto não tiver product_id válido.
        """
        if not product.product_id:
            logger.warning("  AVISO: Ignorando produto sem ID: %s", product.product_name)
            return None

        api_payload = product.api_payload or {}

        # --- Especificações VTEX ---
        specifications = self._extract_specifications(api_payload)

        # --- Imagem ---
        image_url = self._extract_image_url(api_payload)

        # --- Variações de SKU ---
        sku_variations = self._extract_sku_variations(product)

        # --- Montagem do dicionário ---
        product_dict: dict[str, Any] = {
            "product_id": product.product_id,
            "marketplace": product.marketplace,
            "ean": product.ean or next(
                (v.get("ean") for v in sku_variations if v.get("ean")), None
            ),
            "product_name": product.product_name,
            "brand": specifications.get("brand_spec") or product.brand,
            "url": product.url,
            "category_id": product.category_id,
            "sku_variations": sku_variations,
            "price": next(
                (v["price"] for v in sku_variations if v.get("price") is not None), None
            ),
            "available": any(v.get("available", False) for v in sku_variations),
            "image_url": image_url,
            **specifications,
        }

        return product_dict

    # ----------------------------------------------------------
    # Extração interna
    # ----------------------------------------------------------

    def _extract_specifications(self, api_payload: dict) -> dict[str, str]:
        """Extrai especificações VTEX (Ficha Técnica) do payload bruto."""
        if not api_payload:
            return {}

        specifications: dict[str, str] = {}

        # 1. Campos de primeiro nível
        all_props: dict[str, str] = {}
        for k, v in api_payload.items():
            if isinstance(v, list) and v:
                all_props[k] = str(v[0])
            elif isinstance(v, (str, int, float)):
                all_props[k] = str(v)

        # 2. allSpecifications (VTEX: lista de chaves; valores no payload principal)
        for spec_key in api_payload.get("allSpecifications", []):
            val = api_payload.get(spec_key)
            if isinstance(val, list) and val:
                all_props[spec_key] = str(val[0])

        # 3. Variedades nos items (ex: Peso do SKU)
        for item in api_payload.get("items", []):
            for spec in item.get("variations", []):
                val = item.get(spec)
                if isinstance(val, list) and val:
                    all_props[spec] = str(val[0])

        # Mapeamento para chaves internas
        for internal_key, vtex_keys in VTX_SPEC_MAP.items():
            for vtex_key in vtex_keys:
                if vtex_key in all_props and all_props[vtex_key]:
                    specifications[internal_key] = all_props[vtex_key]
                    break

        # Fallback: product_category via Departamento/Categoria
        if not specifications.get("product_category"):
            specifications["product_category"] = (
                specifications.get("product_dept")
                or specifications.get("product_cat_vtex")
            )

        return specifications

    def _extract_image_url(self, api_payload: dict) -> str | None:
        """Extrai a URL da primeira imagem do produto."""
        if not api_payload:
            return None
        items = api_payload.get("items", [])
        if items:
            images = items[0].get("images", [])
            if images:
                return images[0].get("imageUrl")
        return None

    def _extract_sku_variations(self, product: ProductCollection) -> list[dict]:
        """Extrai variações de SKU usando o coletor específico do marketplace."""
        if not product.api_payload:
            return [
                {
                    "sku_id": None,
                    "sku_name": None,
                    "ean": product.ean,
                    "package_weight_kg": None,
                    "price": None,
                    "list_price": None,
                    "subscriber_price": None,
                    "price_per_kg": None,
                    "available": False,
                    "marketplace": product.marketplace,
                }
            ]

        try:
            collector = self._factory.create(product.marketplace)
            return collector.extract_sku_variations(product.api_payload)
        except ValueError:
            logger.warning(
                "  Coletor não registrado para %s; usando variação genérica.",
                product.marketplace,
            )
            return [
                {
                    "sku_id": None,
                    "sku_name": None,
                    "ean": product.ean,
                    "package_weight_kg": None,
                    "price": None,
                    "list_price": None,
                    "subscriber_price": None,
                    "price_per_kg": None,
                    "available": False,
                    "marketplace": product.marketplace,
                }
            ]

    def enrich_batch(
        self, products: list[ProductCollection]
    ) -> list[dict[str, Any]]:
        """
        Enriquece uma lista de produtos e retorna os dicionários válidos.
        """
        result = []
        for product in products:
            enriched = self.enrich(product)
            if enriched is not None:
                result.append(enriched)
        return result
