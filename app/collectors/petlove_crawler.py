from __future__ import annotations

import json
import re
from typing import Any

from bs4 import BeautifulSoup

from app.collectors.http_client import HttpClient
from app.collectors.models import ProductCollection
from app.core.logging import logger

class PetloveCrawlerCollector:
    """
    Coletor para a Petlove focado em extrair preços e EAN para comparação.
    """
    
    BASE_URL = "https://www.petlove.com.br"
    SEARCH_URL = "https://www.petlove.com.br/busca?q="

    def __init__(self):
        self.client = HttpClient()

    def fetch_search_results(self, query: str) -> list[ProductCollection]:
        """
        Busca produtos na Petlove e extrai as informações básicas.
        """
        logger.info(f"Buscando na Petlove: {query}")
        url = f"{self.SEARCH_URL}{query.replace(' ', '+')}"

        try:
            try:
                response = self.client.get(url)
                html = response.text
            except Exception as e:
                if "403" in str(e):
                    msg = "BLOQUEIO 403 DETECTADO na Petlove. O site está recusando conexões automatizadas deste ambiente."
                    tip = "DICA: Para coletar dados da Petlove, execute o pipeline em um ambiente com IP residencial ou use um serviço de proxy."
                    logger.error(msg)
                    logger.info(tip)
                    print(f"\n[PETLOVE] {msg}")
                    print(f"[PETLOVE] {tip}\n")
                raise e

            soup = BeautifulSoup(html, 'html.parser')

            data = None
            script = soup.find('script', id='__NEXT_DATA__')
            if script and getattr(script, 'string', None):
                try:
                    data = json.loads(script.string)
                except (TypeError, json.JSONDecodeError):
                    data = None

            if data is None:
                match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
                if match:
                    try:
                        data = json.loads(match.group(1))
                    except json.JSONDecodeError:
                        data = None

            if data is None:
                logger.warning("Script __NEXT_DATA__ não encontrado ou inválido na Petlove.")
                return []

            products = self._extract_products_from_payload(data)
            logger.info(f"Encontrados {len(products)} produtos na Petlove para '{query}'")
            return products

        except Exception as e:
            logger.error(f"Erro ao coletar Petlove: {e}")
            return []

    def _extract_products_from_payload(self, data: Any) -> list[ProductCollection]:
        """Extrai produtos a partir de um payload JSON ou de uma estrutura de dicionários aninhada."""
        if isinstance(data, dict):
            candidates = []
            for path in [
                ['props', 'pageProps', 'initialData', 'products'],
                ['props', 'pageProps', 'products'],
                ['props', 'pageProps', 'data', 'products'],
                ['products'],
            ]:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        current = None
                        break
                if isinstance(current, list):
                    candidates.append(current)

            if candidates:
                products_data = candidates[0]
            else:
                products_data = []
                for value in data.values():
                    if isinstance(value, (dict, list)):
                        products_data.extend(self._extract_products_from_payload(value))
                return products_data
        elif isinstance(data, list):
            products_data = data
        else:
            return []

        results = []
        for raw_product in products_data:
            if not isinstance(raw_product, dict):
                continue
            if not any(key in raw_product for key in ("id", "name", "url", "slug")):
                continue
            results.append(self._build_product_collection(raw_product))
        return results

    def _build_product_collection(self, product_data: dict[str, Any]) -> ProductCollection:
        brand = product_data.get("brand")
        brand_name = None
        if isinstance(brand, dict):
            brand_name = brand.get("name")
        elif isinstance(brand, str):
            brand_name = brand

        ean = None
        variants = product_data.get("variants", [])
        if isinstance(variants, list) and variants:
            first_variant = variants[0]
            if isinstance(first_variant, dict):
                ean = first_variant.get("ean")

        return ProductCollection(
            product_id=product_data.get("id"),
            product_name=product_data.get("name"),
            brand=brand_name,
            url=f"{self.BASE_URL}{product_data.get('url', '')}" if product_data.get("url") else None,
            category_id=None,
            marketplace="Petlove",
            ean=ean,
            api_payload=product_data,
        )

    def fetch_all(self, queries: list[str]) -> list[ProductCollection]:
        """
        Executa a busca para uma lista de termos (ex: marcas de ração).
        """
        all_products = []
        for q in queries:
            all_products.extend(self.fetch_search_results(q))
        
        return self.remove_duplicates(all_products)

    @staticmethod
    def remove_duplicates(products: list[ProductCollection]) -> list[ProductCollection]:
        unique = {}
        for p in products:
            unique[p.product_id] = p
        return list(unique.values())
