from __future__ import annotations

import time

from app.collectors.http_client import HttpClient
from app.collectors.models import ProductCollection
from app.core.config import settings
from app.core.constants import API_URL
from app.core.logging import logger

CATEGORY_IDS = [

    1000001,
    1000002,
    1000010,
    1000011,
    1000012,
    1000013,

]


class CobasiAPICollector:

    def __init__(self):

        self.client = HttpClient()

    def fetch_category(
        self,
        category_id: int,
    ) -> list[ProductCollection]:

        logger.info(
            "Coletando categoria %s",
            category_id,
        )

        start = 0

        results = []

        while True:

            end = start + settings.page_size - 1

            url = (
                f"{API_URL}"
                f"?fq=C:{category_id}"
                f"&_from={start}"
                f"&_to={end}"
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
                "%s produtos coletados",
                len(results),
            )

            start += settings.page_size

            time.sleep(settings.request_delay)

        return results

    def fetch_all(self) -> list[ProductCollection]:

        products = []

        for category in CATEGORY_IDS:

            products.extend(
                self.fetch_category(category)
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