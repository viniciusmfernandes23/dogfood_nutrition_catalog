from __future__ import annotations

import time

from app.collectors.http_client import HttpClient
from app.collectors.models import ProductCollection
from app.core.config import settings
from app.core.constants import API_URL
from app.core.logging import logger

# Categorias de ração e petiscos para cães na Cobasi.
# Formato: (path_da_url, map_vtex, id_categoria, nome_legivel)
# A API VTEX da Cobasi exige o path de navegação + parâmetro map=c,c[,c]
# para filtrar por subcategoria. O fq=C:ID isolado não funciona para
# subcategorias — apenas para o departamento raiz.
CATEGORY_PATHS = [
    ("cachorro/racao/racao-seca",          "c,c,c", 1001436, "Ração Seca"),
    ("cachorro/racao/racao-umida",         "c,c,c", 1001437, "Ração Úmida"),
    ("cachorro/racao/racao-medicamentosa", "c,c,c", 1001438, "Ração Medicamentosa"),
    ("cachorro/racao/racao-natural",       "c,c,c", 1001617, "Ração Natural"),
    ("cachorro/petiscos",                  "c,c",   1001427, "Petiscos"),
]


class CobasiAPICollector:

    def __init__(self):

        self.client = HttpClient()

    def fetch_category(
        self,
        path: str,
        map_param: str,
        category_id: int,
    ) -> list[ProductCollection]:

        logger.info(
            "Coletando categoria %s (%s)",
            category_id,
            path,
        )

        start = 0

        results = []

        while True:

            end = start + settings.page_size - 1

            url = (
                f"{API_URL}/{path}"
                f"?_from={start}"
                f"&_to={end}"
                f"&map={map_param}"
            )

            response = self.client.get(url)

            data = response.json()

            if not data:
                break

            for product in data:

                results.append(
                    ProductCollection(
                        product_id=int(product["productId"]),
                        product_name=product["productName"],
                        brand=product.get("brand"),
                        url=product.get("link"),
                        category_id=category_id,
                        api_payload=product,
                    )
                )

            logger.info(
                "%s produtos coletados em %s",
                len(results),
                path,
            )

            if len(data) < settings.page_size:
                break

            start += settings.page_size

            time.sleep(settings.request_delay)

        return results

    def fetch_all(self) -> list[ProductCollection]:

        products = []

        for path, map_param, category_id, _ in CATEGORY_PATHS:

            products.extend(
                self.fetch_category(path, map_param, category_id)
            )

        return self.remove_duplicates(products)

    @staticmethod
    def remove_duplicates(
        products: list[ProductCollection],
    ) -> list[ProductCollection]:

        unique = {}

        for product in products:

            unique[product.product_id] = product

        logger.info(
            "%s produtos únicos",
            len(unique),
        )

        return list(unique.values())
