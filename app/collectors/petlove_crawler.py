from __future__ import annotations

import json
import re
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
        url = f"{self.SEARCH_URL}{query}"
        
        try:
            response = self.client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # A Petlove armazena os dados em um script JSON chamado __NEXT_DATA__
            script = soup.find('script', id='__NEXT_DATA__')
            if not script:
                logger.warning("Script __NEXT_DATA__ não encontrado na Petlove.")
                return []

            data = json.loads(script.string)
            
            # Navega no JSON para encontrar os produtos
            # Estrutura: props -> pageProps -> initialData -> products
            try:
                products_data = data['props']['pageProps']['initialData']['products']
            except KeyError:
                logger.warning("Estrutura de produtos não encontrada no JSON da Petlove.")
                return []

            results = []
            for p in products_data:
                # Extrai EAN do primeiro SKU disponível como padrão
                ean = None
                variants = p.get('variants', [])
                if variants:
                    ean = variants[0].get('ean')

                results.append(
                    ProductCollection(
                        product_id=p.get('id'),
                        product_name=p.get('name'),
                        brand=p.get('brand', {}).get('name'),
                        url=f"{self.BASE_URL}{p.get('url')}",
                        category_id=None, # Não capturamos categoria nutricional da Petlove
                        marketplace="Petlove",
                        ean=ean,
                        api_payload=p # Armazena o JSON completo para extração de SKUs posterior
                    )
                )
            
            logger.info(f"Encontrados {len(results)} produtos na Petlove para '{query}'")
            return results

        except Exception as e:
            logger.error(f"Erro ao coletar Petlove: {e}")
            return []

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
