import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.collectors.models import ProductCollection
from app.collectors.petlove_crawler import PetloveCrawlerCollector
from app.services import collector_factory


def test_petlove_parser_recovers_products_from_nested_payload():
    collector = PetloveCrawlerCollector()
    payload = {
        "props": {
            "pageProps": {
                "initialData": {
                    "products": [
                        {
                            "id": 123,
                            "name": "Ração Premium",
                            "brand": {"name": "Marca Teste"},
                            "url": "/produto/123",
                        }
                    ]
                }
            }
        }
    }

    products = collector._extract_products_from_payload(payload)

    assert len(products) == 1
    assert products[0].product_name == "Ração Premium"
    assert products[0].marketplace == "Petlove"


def test_petz_factory_uses_backend_collector(monkeypatch):
    class StubSourceCollector:
        def fetch_all(self, queries=None, categories=None):
            return [
                ProductCollection(
                    product_id=999,
                    product_name="Ração Petz",
                    brand="Petz",
                    url="https://petz.test/produto/999",
                    category_id=None,
                    marketplace="Petz",
                    ean=None,
                    api_payload={},
                )
            ]

    monkeypatch.setattr(collector_factory, "PetzSourceCollector", StubSourceCollector)

    petz_collector = collector_factory.PetzCollector()
    products = petz_collector.fetch_all(queries=["ração"], categories=["cachorro"])

    assert len(products) == 1
    assert products[0].product_name == "Ração Petz"
